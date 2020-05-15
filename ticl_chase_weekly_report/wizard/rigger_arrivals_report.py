# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import xlwt
import io
import xlrd
import base64
from xlwt import easyxf
import datetime
from datetime import datetime, timedelta, date
import calendar
from xlrd import open_workbook

class ticl_warehouse_shipping_report(models.TransientModel):
    _name = "ticl.rigger.arrivals.report"
    _description = "Rigger Arrivals Report"

    @api.onchange('from_date', 'to_date')
    def onchange_week(self):
        from_date = str(self.from_date)
        to_date = str(self.to_date)
        if to_date < from_date:
            return {
                'warning': {
                    'title': "Warning",
                    'message': "To Date Should be higher than From Date",
                }
            }

    from_date = fields.Datetime(string='From Date')
    to_date = fields.Datetime(string='To Date')
    rigger_arrivals_file = fields.Binary('Rigger Arrivals Report')
    file_name = fields.Char('File Name')
    rigger_report_printed = fields.Boolean('Rigger Arrivals Report')
    report_type = fields.Char(default="rigger_arrivals")

    # @api.multi
    def action_print_rigger_arrivals_report(self):
        if self.report_type == 'rigger_arrivals':
            workbook = xlwt.Workbook()
            date_split_1 = str(self.from_date).split(" ")
            date_split_2 = str(self.to_date).split(" ")

            column_heading_style = easyxf('font: name Calibri, bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            worksheet = workbook.add_sheet('Rigger Arrivals Report')
            column_style = easyxf('font: name Calibri')
             
            worksheet.write(0, 0, _('Destination ID Rigger'), column_heading_style)
            worksheet.write(0, 1, _('Shipment ID'), column_heading_style)
            worksheet.write(0, 2, _('Shipped Date'), column_heading_style)
            worksheet.write(0, 3, _('Estimated Delivery'), column_heading_style)
            worksheet.write(0, 4, _('Carrier'), column_heading_style)
            worksheet.write(0, 5, _('BOL'), column_heading_style)
            worksheet.write(0, 6, _('Project ID'), column_heading_style)
            worksheet.write(0, 7, _('Terminal ID'), column_heading_style)
            worksheet.write(0, 8, _('Common Name'), column_heading_style)
            worksheet.write(0, 9, _('Manufacturer'), column_heading_style)
            worksheet.write(0, 10, _('Model'), column_heading_style)
            worksheet.write(0, 11, _('Serial #'), column_heading_style)            

            worksheet.col(0).width = 8000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 7000
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 5000
            worksheet.col(7).width = 5000
            worksheet.col(8).width = 5000
            worksheet.col(9).width = 5000
            worksheet.col(10).width = 5000
            worksheet.col(11).width = 5000

            row = 1
            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'mm/dd/yy'
            for wizard in self:
                shipping_objs = self.env['ticl.shipment.log.line'].search([('ticl_ship_id.appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('ticl_ship_id.appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                                     ('ticl_ship_id.state', '=', 'shipped')
                                                                     ])

                for shipping in shipping_objs:
                    dest_rigger = shipping.ticl_ship_id.receiving_location_id.name
                    if dest_rigger != "Chase Chicago" and dest_rigger != "Chase Las Vegas" \
                    and dest_rigger != "Chase Allentown" and dest_rigger != "Chase Atlanta" and \
                    dest_rigger != "Chase Dallas" and dest_rigger != "Chase Newark":
                        worksheet.write(row, 0, dest_rigger or '')
                        worksheet.write(row, 1, shipping.ticl_ship_id.name or '')
                        worksheet.write(row, 2, datetime.strptime(str(shipping.ticl_ship_id.appointment_date_new) + " 00:00:00",
                                                      '%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y "), date_format or '')

                        if shipping.ticl_ship_id.estimated_delivery_date:
                            worksheet.write(row, 3, datetime.strptime(str(shipping.ticl_ship_id.estimated_delivery_date),'%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y "), date_format or '')
                        else:
                            if shipping.ticl_ship_id.delivery_date_new:
                                worksheet.write(row, 3, datetime.strptime(str(shipping.ticl_ship_id.delivery_date_new) + " 00:00:00",'%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y "), date_format or '')
                            else:
                                worksheet.write(row, 3,'')
                        worksheet.write(row, 4, shipping.ticl_ship_id.shipping_carrier_id.name or '')
                        worksheet.write(row, 5, shipping.ticl_ship_id.echo_tracking_id or '')
                        worksheet.write(row, 6, shipping.ticl_project_id or '')
                        worksheet.write(row, 7, shipping.tid or '')
                        worksheet.write(row, 8, shipping.common_name or '')
                        worksheet.write(row, 9, shipping.manufacturer_id.name or '')
                        worksheet.write(row, 10, shipping.product_id.name or '')
                        if shipping.ticl_ship_id.dropship_state == 'no':
                            worksheet.write(row, 11, shipping.lot_id.name or '')
                        else:
                            worksheet.write(row, 11, shipping.serial_number or '')
                        row += 1

                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                excel_file = base64.decodestring(excel_file)
                book = xlrd.open_workbook(file_contents=excel_file, formatting_info=True)
                wbk = xlwt.Workbook()
                for i in range(len(book.sheets())):
                    sheet = book.sheets()[i]
                    if sheet.name == "Rigger Arrivals Report":
                        data = [sheet.row_values(i) for i in range(sheet.nrows)]
                        labels = data[0]
                        data = data[1:]
                        data.sort(key=lambda x: x[10].lower())
                        data.sort(key=lambda x: x[3])
                        data.sort(key=lambda x: x[1])
                        data.sort(key=lambda x: x[0].lower())
                        sheet = wbk.add_sheet(sheet.name)
                        sheet.col(0).width = 8000
                        sheet.col(1).width = 5000
                        sheet.col(2).width = 5000
                        sheet.col(3).width = 7000
                        sheet.col(4).width = 5000
                        sheet.col(5).width = 5000
                        sheet.col(6).width = 5000
                        sheet.col(7).width = 5000
                        sheet.col(8).width = 5000
                        sheet.col(9).width = 5000
                        sheet.col(10).width = 5000
                        sheet.col(11).width = 5000

                        for idx, label in enumerate(labels):
                            sheet.write(0, idx, label, column_heading_style)
                        for idx_r, row in enumerate(data):
                            for idx_c, value in enumerate(row):
                                if idx_c == 2 or idx_c == 3:
                                    sheet.write(idx_r + 1, idx_c, value, date_format)
                                else:
                                    sheet.write(idx_r + 1, idx_c, value, column_style)

                fp = io.BytesIO()
                wbk.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.rigger_arrivals_file = excel_file
                self.file_name = 'Rigger Arrivals Report'
                fp.close()
                return {
                'type': 'ir.actions.act_url',
                'name': 'Excel',
                'url': '/web/content/ticl.rigger.arrivals.report/%s/rigger_arrivals_file/%s.xls?download=true' % (
                                self.id,self.file_name)
                }