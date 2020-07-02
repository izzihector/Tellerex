#-*- coding: utf-8 -*-
import os
import csv
import tempfile
import binascii
import xlrd
import base64
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date


class import_work_order(models.TransientModel):
    _name = "import.work.order"

    file_data = fields.Binary('Select File', required=True)
    file_name = fields.Char('File Name')
    import_option = fields.Selection(
        [('xls', 'XLS File')], string='Select', default='xls')
    import_type = fields.Selection(
        [('receipt', 'Receipt'),('receipt_line', 'Receipt Line'),('shipment', 'Shipment'),('shipment_line', 'Shipment Line')], string='Select', required=True)

    def convert_date(self, date_val, wb):
        if date_val:
            if isinstance(date_val, float) == True or isinstance(date_val, int) == True:
                x = datetime(*xlrd.xldate_as_tuple(date_val, wb))
                sp = str(x).split(' ')
                dft = sp[0]
                if '/' in dft:
                    x = dft.split('/')
                elif '-' in dft:
                    x = dft.split('-')
                dates = datetime(int(x[0]), int(x[1]), int(x[2]), 00, 00, 00)
                # dates = datetime(int(dft[0:4]), int(dft[5:7]), int(dft[-2:]), 00, 00, 00)
            else:
                dft=date_val
                if '/' in dft:
                    x = dft.split('/')
                elif '-' in dft:
                    x = dft.split('-')
                dates = datetime(int(x[2]), int(x[0]), int(x[1]), 00, 00, 00)
                # dates = datetime(int(pickupDate[-4:]), int(pickupDate[:2]), int(pickupDate[3:5]), 00, 00, 00)
            datetime_object = dates
            #datetime_object = datetime(*xlrd.xldate_as_tuple(pickupDate, wb.datemode))
            converted_date = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
            return converted_date
    
    def import_button(self):
        if self.import_option == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_data))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    if self.import_type == 'shipment_line':
                        shipment_obj = self.env['ticl.shipment.log']
                        col1 = sheet.cell(row, 0).value
                        shipment_name = col1.strip()
                        shipment = shipment_obj.search([('name','=',shipment_name)])
                        if shipment:
                            vals={'ticl_ship_id':shipment.id}
                            col2 = sheet.cell(row, 1).value
                            col5 = sheet.cell(row, 4).value
                            col4 = sheet.cell(row, 3).value
                            col8 = sheet.cell(row, 7).value
                            col9 = sheet.cell(row, 8).value
                            col13 = sheet.cell(row, 12).value
                            vals.update({'common_name':col2,'funding_doc_type':col5,'funding_doc_number':col4,'ticl_project_id':col8,'receipt_id':col9,'tid':col13})
                            col6 = sheet.cell(row, 5).value
                            manufacturer_name = col6.strip()
                            manufacturer = self.env['manufacturer.order'].search([('name','=',manufacturer_name)])
                            vals.update({'manufacturer_id':manufacturer.id})
                            col7 = sheet.cell(row, 6).value
                            product_name = col7.strip()
                            product = self.env['product.product'].search([('name','=',product_name)])
                            vals.update({'product_id':product.id,'tel_type':product.categ_id.id})
                            col10 = sheet.cell(row, 9).value
                            if col10:
                                c_date = self.convert_date(col10,workbook.datemode)
                                vals.update({'receive_date':c_date})
                                
                            if shipment.dropship_state == 'yes':
                                col11 = sheet.cell(row, 10).value
                                vals.update({'serial_number':col11})
                            if shipment.dropship_state == 'no':
                                col12 = sheet.cell(row, 11).value
                                if col12:
                                    lot_name = col12.strip() 
                                    lot = self.env['stock.production.lot'].search([('name','=',lot_name)],limit = 1)
                                    vals.update({'lot_id':lot.id})
                            col10 = sheet.cell(row, 9).value
                            if col10 and isinstance(col10, str) == True and col10 != '0':
                                condition_name = col10.strip()
                                condition = self.env['ticl.condition'].search([('name','=',condition_name)])
                                vals.update({'condition_id':condition.id})
                            self.env['ticl.shipment.log.line'].create(vals)
                            
                    if self.import_type == 'shipment':
                        shipment_obj = self.env['ticl.shipment.log']
                        col3 = sheet.cell(row, 2).value
                        shipment_name = col3.strip()
                        shipment = shipment_obj.search([('name','=',shipment_name)])
                        if not shipment:
                            
                            vals={'name':shipment_name,'echo_call':'no'}
                            col6 = sheet.cell(row, 5).value
                            dropship = col6.strip().lower()
                            vals.update({'dropship_state':dropship})
                            col8 = sheet.cell(row, 7).value
                            org_location = col8.strip()
                            if dropship == 'yes':
                                source_location = self.env['res.partner'].search([('name','=',org_location)])
                                vals.update({'sending_rigger_id':source_location.id})
                            if dropship == 'no':
                                source_location = self.env['stock.location'].search([('name','=',org_location)])
                                vals.update({'sending_location_id':source_location.id})
                            col5 = sheet.cell(row, 4).value
                            dst_location = col5.strip()
                            destn_location = self.env['res.partner'].search([('name','=',dst_location)])
                            vals.update({'receiving_location_id':destn_location.id})
                            col7 = sheet.cell(row, 6).value
                            emp_name = col7.strip()
                            emp = self.env['hr.employee'].search([('name','=',emp_name)])
                            vals.update({'hr_employee_id':emp.id})
                            col11 = sheet.cell(row, 10).value
                            if isinstance(col11, str) == True and col11 != '0':
                                ware_name = col11.strip()
                                warehouse = self.env['stock.warehouse'].search([('name','=',ware_name)])
                                vals.update({'warehouse_id':warehouse.id})
                            col9 = sheet.cell(row, 8).value
                            shipment_type = col9.strip()
                            vals.update({'shipment_type':shipment_type})
                            col10 = sheet.cell(row, 9).value
                            bol = col10
                            vals.update({'echo_tracking_id':bol})
                            col4 = sheet.cell(row, 3).value
                            if col4:
                                c_date = self.convert_date(col4,workbook.datemode)
                                vals.update({'delivery_date_new':c_date})
                            col12 = sheet.cell(row, 11).value
                            if col12:
                                c_date = self.convert_date(col12,workbook.datemode)
                                vals.update({'appointment_date_new':c_date})
                            shipment_obj.create(vals)
                    
                    if self.import_type == 'receipt_line':
                        receiptLine_obj = self.env['ticl.receipt.line']
                        col5 = sheet.cell(row, 5).value
                        unique_no = int(col5)
                        receipt_line = receiptLine_obj.search([('tel_unique_no','=',unique_no)])
                        if not receipt_line:
                            receipt_obj = self.env['ticl.receipt']
                            col2 = sheet.cell(row, 1).value
                            receipt_name = col2.strip()
                            receipt = receipt_obj.search([('name','=',receipt_name)])
                            vals={'tel_unique_no':unique_no,'ticl_receipt_id':receipt.id,'count_number':1}
                            col7 = sheet.cell(row, 6).value
                            product_name = col7.strip()
                            product = self.env['product.product'].search([('name','=',product_name)])
                            vals.update({'product_id':product.id})
                            col8 = sheet.cell(row, 7).value
                            serial_number = col8.strip()
                            vals.update({'serial_number':serial_number})
                            col10 = sheet.cell(row, 9).value
                            condition_name = col10.strip()
                            condition = self.env['ticl.condition'].search([('name','=',condition_name)])
                            vals.update({'condition_id':condition.id})
                            col12 = sheet.cell(row, 11).value
                            type_p = col12.strip()
                            categ = self.env['product.category'].search([('name','=',type_p)])
                            vals.update({'tel_type':categ.id})
                            col13 = sheet.cell(row, 12).value
                            xl = col13.strip()
                            vals.update({'xl_items':xl.lower()})
                            col14 = sheet.cell(row, 13).value
                            manufacturer_name = col14.strip()
                            manufacturer = self.env['manufacturer.order'].search([('name','=',manufacturer_name)])
                            vals.update({'manufacturer_id':manufacturer.id})
                            receiptLine_obj.create(vals)
                        
                    if self.import_type == 'receipt':
                        receipt_obj = self.env['ticl.receipt']
                        col2 = sheet.cell(row, 1).value
                        receipt_name = col2.strip()
                        receipt = receipt_obj.search([('name','=',receipt_name)])
                        if not receipt:
                            
                            vals={'name':receipt_name,'total_pallet':1,'echo_call':'no'}
                            col3 = sheet.cell(row, 2).value
                            s_location = col3.strip()
                            source_location = self.env['res.partner'].search([('name','=',s_location)])
                            vals.update({'sending_location_id':source_location.id})
                            col4 = sheet.cell(row, 3).value
                            d_location = col4.strip()
                            dest_location = self.env['stock.location'].search([('name','=',d_location)])
                            vals.update({'receiving_location_id':dest_location.id})
                            rcv_date = sheet.cell(row, 4).value
                            if rcv_date:
                                if isinstance(rcv_date, float) == True or isinstance(rcv_date, int) == True:
                                    x = datetime(*xlrd.xldate_as_tuple(rcv_date, workbook.datemode))
                                    sp = str(x).split(' ')
                                    dft = sp[0]
                                    if '/' in dft:
                                        x = dft.split('/')
                                    elif '-' in dft:
                                        x = dft.split('-')
                                    dates = datetime(int(x[0]), int(x[1]), int(x[2]), 00, 00, 00)
                                    # dates = datetime(int(dft[0:4]), int(dft[5:7]), int(dft[-2:]), 00, 00, 00)
                                else:
                                    dft=rcv_date
                                    if '/' in dft:
                                        x = dft.split('/')
                                    elif '-' in dft:
                                        x = dft.split('-')
                                    dates = datetime(int(x[2]), int(x[0]), int(x[1]), 00, 00, 00)
                                    # dates = datetime(int(pickupDate[-4:]), int(pickupDate[:2]), int(pickupDate[3:5]), 00, 00, 00)
                                datetime_object = dates
                                #datetime_object = datetime(*xlrd.xldate_as_tuple(pickupDate, wb.datemode))
                                pickup_date = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
                            vals.update({'pickup_date':pickup_date,'delivery_date':pickup_date})
                            col11 = sheet.cell(row, 10).value
                            emp_name = col11.strip()
                            emp = self.env['hr.employee'].search([('name','=',emp_name)])
                            vals.update({'hr_employee_id':emp.id})
                            col9 = sheet.cell(row, 8).value
                            ware_name = col9.strip()
                            warehouse = self.env['stock.warehouse'].search([('name','=',ware_name)])
                            vals.update({'warehouse_id':warehouse.id})
                            receipt_obj.create(vals)
                
            except Exception as e:
                self.env.cr.rollback()
                raise Warning(_("%s" % e))


    # return {'type': 'ir.actions.act_window_close'}
