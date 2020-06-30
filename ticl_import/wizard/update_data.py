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


class import_update_data(models.TransientModel):
    _name = "import.update.data"

    file_data = fields.Binary('Select File', required=True)
    file_name = fields.Char('File Name')
    import_option = fields.Selection(
        [('xls', 'XLS File')], string='Select', default='xls')
    import_type = fields.Selection(
        [('update_check_sale', 'update_check_sale'),('import_sale', 'import_sale'),('update_COD', 'update_COD'),('update_check_shipment', 'update_check_shipment'),('update_status_stock', 'update_status_stock'),('update_status_recycle', 'update_status_recycle')], string='Select')



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
                    if self.import_type == 'update_check_sale':
                        recipt_obj = self.env['ticl.receipt.log.summary.line']
                        col1 = sheet.cell(row, 0).value
                        #receipt_name = col1.strip()
                        receipt = recipt_obj.search([('tel_unique_no','=',col1)])
                        if receipt:
                            vals = {}
                            check_sale = sheet.cell(row,1).value
                            vals.update({'check_sale':check_sale})
                            receipt.sudo().write(vals)

                    elif self.import_type == 'update_status_stock':
                        recipt_obj = self.env['stock.move.line']
                        col1 = sheet.cell(row, 0).value
                        print("----col1",col1)
                        col1 = str(col1).split('.')
                        print("----col1",col1)
                        #receipt_name = col1.strip()
                        receipt = recipt_obj.search([('tel_unique_no','=',col1)])
                        print("----receipt",receipt)
                        if receipt:
                            vals = {}
                            print("----receipt",receipt)
                            status = sheet.cell(row,1).value
                            print("----total_weight",status)
                            vals.update({'status':status})
                            receipt.sudo().write(vals) 

                    elif self.import_type == 'update_status_recycle':
                        recipt_obj = self.env['stock.move.line']
                        col1 = sheet.cell(row, 0).value
                        print("----col1",col1)
                        col1 = str(col1).split('.')
                        print("----col1",col1)
                        receipt = recipt_obj.search([('tel_unique_no','=',col1)])
                        print("----receipt",receipt)
                        if receipt:
                            vals = {}

                            recycled_date = sheet.cell(row,2).value
                            if not recycled_date:
                                raise Exception("Approval date field is blank in row %s , Please review the file."% (row + 1))
                            if recycled_date:
                                if type(recycled_date) is str:  
                                    appr_date = datetime.strptime(recycled_date, "%m/%d/%Y")
                                else:
                                    appr_date = datetime(*xlrd.xldate_as_tuple(recycled_date, workbook.datemode))
                                vals.update({'recycled_date':appr_date.strftime("%Y-%m-%d")})                            

                            status = sheet.cell(row,1).value
                            print("----total_weight",status)
                            vals.update({'status':status})
                            receipt.sudo().write(vals) 


                    elif self.import_type == 'update_check_shipment':
                        recipt_obj = self.env['stock.move.line']
                        col1 = sheet.cell(row, 0).value
                        print("----col1",col1)
                        col1 = str(col1).split('.')
                        receipt = recipt_obj.search([('tel_unique_no','=',col1)])
                        print("----receipt",receipt)
                        if receipt:
                            vals = {}
                            print("----receipt",receipt)
                            status = sheet.cell(row,1).value
                            print("----total_weight",status)
                            vals.update({'status':status})
                            receipt.sudo().write(vals)

                    elif self.import_type == 'update_COD':
                        recipt_obj = self.env['stock.move.line']
                        col1 = sheet.cell(row, 0).value
                        col1 = int(col1)
                        print("----col1",col1)
                        #col2 = sheet.cell(row, 1).value
                        col3 = sheet.cell(row, 2).value
                        # col4 = sheet.cell(row, 3).value
                        # col5 = sheet.cell(row, 4).value
                        # col6 = sheet.cell(row, 5).value
                        # col7 = sheet.cell(row, 6).value
                        # col8 = sheet.cell(row, 7).value
                        # col9 = sheet.cell(row, 8).value
                        # col10 = sheet.cell(row, 9).value
                        receipt = recipt_obj.search([('tel_unique_no','=',col1)])
                        # print("----receipt",receipt)
                        # epp = self.env['ticl.epp.manufacturer'].search([('name','=',col2)])
                        # hdd = self.env['ticl.hdd.manufacturer'].search([('name','=',col4)])
                        emp = self.env['hr.employee'].search([('name','=',col3)])
                        if receipt:
                            vals = {}
                            # vals.update({'epp_manufacturer':epp})
                            # vals.update({'epp_serial_num':col3})
                            # vals.update({'hdd_manufacturer':hdd})

                            processed_date = sheet.cell(row,2).value
                            # if not processed_date:
                            #     raise Exception("Approval date field is blank in row %s , Please review the file."% (row + 1))
                            if processed_date:
                                if type(processed_date) is str:  
                                    appr_date = datetime.strptime(processed_date, "%m/%d/%Y")
                                else:
                                    appr_date = datetime(*xlrd.xldate_as_tuple(processed_date, workbook.datemode))
                                vals.update({'processed_date':appr_date.strftime("%Y-%m-%d")})                        
                            
                            vals.update({'cod_employee_id':emp})
                            #vals.update({'tel_cod':col7})
                            # vals.update({'atm_cleaned':col8})
                            # vals.update({'atm_photographed':col9})
                            # vals.update({'atm_data_destroyed':col10})
                            # vals.update({'state':'wrapped'})
                            receipt.sudo().write(vals)  


                    elif self.import_type == 'import_sale':
                        stock_line_obj = self.env['stock.move.line']
                        col1 = sheet.cell(row, 0).value
                        print("====col1==",col1)
                        col1 = str(col1).split('.')
                        col2 = sheet.cell(row, 1).value
                        print("====col2==",col2)
                        col3 = sheet.cell(row, 2).value
                        col4 = sheet.cell(row, 3).value
                        col5 = sheet.cell(row, 4).value
                        col7 = sheet.cell(row, 6).value
                        col7 = float(col7)
                        col8 = sheet.cell(row, 7).value
                        col8 = float(col8)     
                        col9 = sheet.cell(row, 8).value
                        col9 = float(col9)
                        col10 = sheet.cell(row, 9).value
                        sale_import = stock_line_obj.search([('serial_number','=',col1),('status','=','sold')])
                        print("----sale_import",sale_import)
                        if sale_import:
                            vals = {}

                            sale_date_pick = sheet.cell(row,5).value
                            if not sale_date_pick:
                                raise Exception("Approval date field is blank in row %s , Please review the file."% (row + 1))
                            if sale_date_pick:
                                if type(sale_date_pick) is str:  
                                    appr_date = datetime.strptime(sale_date_pick, "%m/%d/%Y")
                                else:
                                    appr_date = datetime(*xlrd.xldate_as_tuple(sale_date_pick, workbook.datemode))
                                vals.update({'sale_date_pick':appr_date.strftime("%Y-%m-%d")})                        
                            
                            vals.update({'sale_import_data':col3 or ''})
                            vals.update({'sale_old_id':col4 or ''})
                            vals.update({'sale_type':col5 or ''})
                            vals.update({'sale_gross':str(col7)})
                            vals.update({'sale_net':str(col8)})
                            vals.update({'sale_commission':str(col9)})
                            col10 = sheet.cell(row, 9).value
                            if col10:
                                vals.update({'sale_check_number':int(col10)})
                            sale_import.sudo().write(vals)                                                                                     

                
            except Exception as e:
                self.env.cr.rollback()
                raise Warning(_("%s" % e))
