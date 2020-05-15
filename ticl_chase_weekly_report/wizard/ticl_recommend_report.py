# -*- coding: utf-8 -*-
import time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlwt
from datetime import datetime,date, timedelta
import calendar
from xlwt import easyxf
import base64
import io
class ticl_recommend_receipt(models.Model):
    _inherit = "ticl.receipt.line"

    to_recommend_file = fields.Binary('To Recommend Report')
    def generate_to_recommend_xls(self):
        workbook = xlwt.Workbook()

        # style = xlwt.easyxf('font:bold True; font: color green; pattern: pattern solid, fore_colour green;')
        style_green = xlwt.easyxf('font:bold True; font: color green;align: horiz right')
        style_orange = xlwt.easyxf('font:bold True; font: color orange;')
        style_red = xlwt.easyxf('font:bold True; font: color red;')
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('To Recommend Report')
         
        worksheet.write(0, 0, _('Location'), column_heading_style)
        worksheet.write(0, 1, _('Manufacturer'), column_heading_style)
        worksheet.write(0, 2, _('Model'), column_heading_style)
        worksheet.write(0, 3, _('Serial #'), column_heading_style)
        worksheet.write(0, 4, _('Condition'), column_heading_style)
        worksheet.write(0, 5, _('Received Date'), column_heading_style)
        worksheet.write(0, 6, _('Comments'), column_heading_style)
        worksheet.write(0, 7, _('Aging'), column_heading_style)
        worksheet.write(0, 8, _('Notes'), column_heading_style)
        # worksheet.write(0, 9, _('Receipt Number'), column_heading_style)
        # worksheet.write(0, 10, _('State'), column_heading_style)


        worksheet.col(0).width = 8000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 7000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        # worksheet.col(9).width = 5000
        # worksheet.col(10).width = 5000

        row = 1
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'mm/dd/yy'
        condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])


        for wizard in self:
            recommend_objs = self.env['ticl.receipt.line'].search(
                        [('condition_id', '=', condition_id.id),
                        ('ticl_receipt_id.state', 'in', ('pending','inprogress','completed'))])
            for ids in recommend_objs:
                status = self.env['stock.move'].search([('serial_number', '=', ids.serial_number), (
                        'status', 'in', ('picked', 'packed', 'inventory','assigned'))],limit=1)
                if status.status in ('picked', 'packed', 'inventory', 'assigned'):

                    if ids.received_date:
                        rec_date = ids.received_date.strftime("%m/%d/%Y ")
                    else:
                        rec_date= ""
                    worksheet.write(row, 0, ids.ticl_receipt_id.receiving_location_id.name or '')
                    worksheet.write(row, 1, ids.manufacturer_id.name or '')
                    worksheet.write(row, 2, ids.product_id.name or '')
                    worksheet.write(row, 3, ids.serial_number or '')
                    worksheet.write(row, 4, ids.condition_id.name or '')
                    worksheet.write(row, 5, rec_date, date_format or '')
                    worksheet.write(row, 6, ids.tel_note or '')
                            
                    if ids.received_date:
                        received_date = str(ids.received_date)
                        rec_date = received_date.split("-")
                        rd = rec_date[2].split(" ")
                        rd_date = date(int(rec_date[0]), int(rec_date[1]), int(rd[0]))
                        today_date = date.today()
                        duration = today_date - rd_date
                        duration_days = duration.days

                    if ids.received_date == False or ids.ticl_receipt_id.state == 'pending':
                        worksheet.write(row, 7, "Pre Arrival", style_green)
                    elif  duration_days < 15 and ids.ticl_receipt_id.state != 'pending':
                        worksheet.write(row, 7, duration_days, style_green)
                    elif duration_days >=15 and duration_days <=29 and ids.ticl_receipt_id.state != 'pending':
                        worksheet.write(row, 7, duration_days, style_orange)
                    else:
                        worksheet.write(row, 7, duration_days, style_red)
                   

                    worksheet.write(row, 8, '' or '')
                    # worksheet.write(row, 9, ids.ticl_receipt_id.name or '')
                    # worksheet.write(row, 10, ids.ticl_receipt_id.state or '')


                    row += 1

            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            self.to_recommend_file = excel_file
            self.file_name = 'To Recommend Report'
            fp.close()
            
            return {
                'type': 'ir.actions.act_url',
                'name': 'To Recommend Report',
                'url': '/web/content/ticl.receipt.line/%s/to_recommend_file/%s.xls?download=true' % (
                    self.id,self.file_name)

            }
