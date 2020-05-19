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
        [('update_check_sale', 'update_check_sale'),('update_status_stock', 'update_status_stock'),('update_status_recycle', 'update_status_recycle')], string='Select')



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
                        #receipt_name = col1.strip()
                        receipt = recipt_obj.search([('tel_unique_no','=',col1)])
                        if receipt:
                            vals = {}
                            print("----receipt",receipt)
                            status = sheet.cell(row,1).value
                            print("----total_weight",status)
                            vals.update({'status':status})
                            receipt.sudo().write(vals)

                    elif self.import_type == 'update_status_recycle':
                        recipt_obj = self.env['stock.move.line']
                        col1 = sheet.cell(row,0).value
                        
                        #receipt_name = col1.strip()
                        receipt = recipt_obj.search([('tel_unique_no','=',col1),('status','=','recycled')])
                        if receipt:
                            vals = {}
                            col1 = sheet.cell(row, 1).value
                            if col1:
                                c_date = self.convert_date(col1,workbook.datemode)
                                print("----c_date",c_date)
                                vals.update({'recycled_date':c_date})

                            scrap_tel_note = sheet.cell(row,2).value
                            vals.update({'scrap_tel_note':scrap_tel_note})
                            receipt.sudo().write(vals)

                
            except Exception as e:
                self.env.cr.rollback()
                raise Warning(_("%s" % e))
