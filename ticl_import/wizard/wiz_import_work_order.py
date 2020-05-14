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
        [('receipt', 'Receipt'),('receipt_line', 'Receipt Line')], string='Select', required=True)

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
                    if self.import_type == 'receipt_line':
                        receiptLine_obj = self.env['ticl.receipt.line']
                        col5 = sheet.cell(row, 5).value
                        unique_no = col5.strip()
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
                raise Warning(_("Invalid file! Please Choose .xlsx File."))


    # return {'type': 'ir.actions.act_window_close'}
