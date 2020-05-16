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
        [('update_check_sale', 'update_check_sale'),('update_status_stock', 'update_status_stock')], string='Select')

    
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

                
            except Exception as e:
                self.env.cr.rollback()
                raise Warning(_("%s" % e))
