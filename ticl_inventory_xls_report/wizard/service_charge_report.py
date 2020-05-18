# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
from odoo import models, fields, api, _
import calendar
from datetime import datetime


class ticl_service_charge_report(models.TransientModel):
    _name = "ticl.service.charge.report"
    _description = "Service Charge Report"

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
    service_charge_file = fields.Binary('Service Charge Report')
    file_name = fields.Char('File Name')
    service_charge_report_printed = fields.Boolean('Service Charge Report')
    print_type = fields.Selection([('excel','Excel'),('pdf','PDF')], string='Print Type')
    tel_type = fields.Many2one('product.category', string="Type")


    @api.multi
    def action_print_service_charge_report(self):
        if self.print_type == 'pdf':
            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_inventory_xls_report.service_charge_report_pdf',
                'model': 'ticl.service.charge.report',
                'report_type': "qweb-pdf",
            }
        if self.print_type == 'excel':
            workbook = xlwt.Workbook()
            date_split_1 = str(self.from_date).split(" ")
            rd = date_split_1[0].split('-')
            date_custom = '{0} {1}.{2}'.format(self.from_date.strftime('%b'), int(rd[2]), int(rd[0]))
            ans = calendar.weekday(int(rd[0]), int(rd[1]), int(rd[2]))
            date_split_2 = str(self.to_date).split(" ")
            rd_1 = date_split_2[0].split('-')
            date_customs = '{0} {1}.{2}'.format(self.to_date.strftime('%b'), int(rd_1[2]), int(rd_1[0]))
            ans_1 = calendar.weekday(int(rd_1[0]), int(rd_1[1]), int(rd_1[2]))
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            worksheet = workbook.add_sheet('Service Charge Report')
            worksheet.write(1, 4, '{0} {1}'.format(days[ans], date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 5, 'To', easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 6, '{0} {1}'.format(days[ans_1], date_customs), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(3, 0, _('Receipt Number'), column_heading_style)
            worksheet.write(3, 1, _('Received Date'), column_heading_style)
            worksheet.write(3, 2, _('Unique Id'), column_heading_style)
            worksheet.write(3, 3, _('Model'), column_heading_style)
            worksheet.write(3, 4, _('Manufacturer'), column_heading_style)
            worksheet.write(3, 5, _('Serial Number'), column_heading_style)
            worksheet.write(3, 6, _('XL'), column_heading_style)
            worksheet.write(3, 7, _('Type'), column_heading_style)
            worksheet.write(3, 8, _('Receiving charges'), column_heading_style)
            worksheet.write(3, 9, _('Monthly Service Charges'), column_heading_style)
            worksheet.write(3, 10, _('Refurbishment Charges'), column_heading_style)

            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 5000
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 5000
            worksheet.col(7).width = 5000
            worksheet.col(8).width = 5000
            worksheet.col(9).width = 5000
            worksheet.col(10).width = 5000

            row = 4
            for wizard in self:
                heading = 'Service Charge Report'
                worksheet.write_merge(0, 0, 0, 10, heading, easyxf(
                    'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))


                if  wizard.tel_type.id == False:
                    inventory_objs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('received_date', '<=', date_split_2[0] +' 23:59:59')
                                                                     ])
                else:

                    inventory_objs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('received_date', '<=', date_split_2[0] +' 23:59:59'),
                                                                     ('categ_id', '=', wizard.tel_type.id)
                                                                     ])
            

                for inventory in inventory_objs:
                    reveive_date = str(inventory.received_date).split(" ")
                    rd = reveive_date[0].split('-')
                    reveived_date  = '{0}-{1}-{2}'.format(inventory.received_date.strftime("%b"),int(rd[2]),int(rd[0]))
                    ans =calendar.weekday(int(rd[0]),int(rd[1]),int(rd[2]))

                    if inventory.xl_items == 'y':
                        xl_items = 'Yes'
                    elif inventory.xl_items == 'n':
                        xl_items = 'No'
                    else:
                        xl_items = ""

                    if inventory.future_ship_date == False:
                        monthly_charge = inventory.monthly_service_charge
                        received_date = str(inventory.received_date).split(" ")
                        today_date_time = datetime.now().replace(microsecond=0)
                        today = str(today_date_time).split(" ")
                        date1 = datetime.strptime(received_date[0], "%Y-%m-%d") 
                        date2 = datetime.strptime(today[0], "%Y-%m-%d")
                        months_str = calendar.month_name
                        months = []
                        while date1 <= date2:
                            month = date1.month
                            year = date1.year
                            month_str = months_str[month][0:3]
                            months.append("{0}-{1}".format(month_str, str(year)[-2:]))
                            next_month = month + 1 if month != 12 else 1
                            next_year = year + 1 if next_month == 1 else year
                            y =  str(date1.replace(month=next_month, year=next_year)).split(" ")
                            x = y[0]
                            rd_1 = x.split('-')
                            date1 = datetime.strptime("{0}-{1}-{2} 00:00:00".format(rd_1[0],rd_1[1],1), '%Y-%m-%d %H:%M:%S')
                        if len(months) == 1:
                            charges = monthly_charge
                        else:
                            charges = monthly_charge * len(months)
                        inventory.monthly_service_charge_total = charges
            
                    worksheet.write(row, 0, inventory.origin or '')
                    worksheet.write(row, 1, '{0} {1}'.format(days[ans], reveived_date) or '')
                    worksheet.write(row, 2, inventory.tel_unique_no or '')
                    worksheet.write(row, 3, inventory.product_id.name or '')
                    worksheet.write(row, 4, inventory.manufacturer_id.name or '')
                    worksheet.write(row, 5, inventory.serial_number or '')
                    worksheet.write(row, 6, xl_items or '')
                    worksheet.write(row, 7, inventory.categ_id.name or '')
                    worksheet.write(row, 8, "$" + str(inventory.service_price) or '')
                    worksheet.write(row, 9, "$" + str(inventory.monthly_service_charge_total) or 0)
                    worksheet.write(row, 10, "$" + str(inventory.refurbishment_charges) or 0)
                    row += 1

                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.service_charge_file = excel_file
                self.file_name = str(wizard.from_date) + '_' + 'Service Charge Report.xls'
                fp.close()
                
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'Service Charge Report',
                    'url': '/web/content/ticl.service.charge.report/%s/service_charge_file/%s.xls?download=true' % (
                        self.id,self.file_name)

                }

    @api.multi
    def get_from_date_values(self, from_date):
        x = from_date
        from_date = str(from_date).split(" ")
        rd = from_date[0].split('-')
        from_date = '{0} {1}.{2}'.format(x.strftime('%b'), int(rd[2]), int(rd[0]))
        import calendar
        ans = calendar.weekday(int(rd[0]), int(rd[1]), int(rd[2]))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dates = '{0} {1}'.format(days[ans], from_date)
        return dates

    @api.multi
    def get_to_date_values(self, to_date):
        x = to_date
        to_date = str(to_date).split(" ")
        rd = to_date[0].split('-')
        to_date = '{0} {1}.{2}'.format(x.strftime('%b'), int(rd[2]), int(rd[0]))
        import calendar
        ans = calendar.weekday(int(rd[0]), int(rd[1]), int(rd[2]))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dates = '{0} {1}'.format(days[ans], to_date)
        return dates

    @api.multi
    def get_charge_report_values(self,data=None):
        date_split_1 = str(self.from_date).split(" ")
        date_split_2 = str(self.to_date).split(" ")

        if self.tel_type.id == False:
            docs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                                ('received_date', '<=', date_split_2[0] +' 23:59:59')
                                                ])

        else:
            docs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('received_date', '<=', date_split_2[0] +' 23:59:59'),
                                                                     ('categ_id', '=', self.tel_type.id)
                                                                     ])

        return docs

    @api.multi
    def get_monthly_service_charge_total_values(self, inventory):
        if inventory.future_ship_date == False:
            monthly_charge = inventory.monthly_service_charge
            received_date = str(inventory.received_date).split(" ")
            today_date_time = datetime.now().replace(microsecond=0)
            today = str(today_date_time).split(" ")
            date1 = datetime.strptime(received_date[0], "%Y-%m-%d") 
            date2 = datetime.strptime(today[0], "%Y-%m-%d")
            months_str = calendar.month_name
            months = []
            while date1 <= date2:
                month = date1.month
                year = date1.year
                month_str = months_str[month][0:3]
                months.append("{0}-{1}".format(month_str, str(year)[-2:]))
                next_month = month + 1 if month != 12 else 1
                next_year = year + 1 if next_month == 1 else year
                y =  str(date1.replace(month=next_month, year=next_year)).split(" ")
                x = y[0]
                rd_1 = x.split('-')
                date1 = datetime.strptime("{0}-{1}-{2} 00:00:00".format(rd_1[0],rd_1[1],1), '%Y-%m-%d %H:%M:%S')
            if len(months) == 1:
                charges = monthly_charge
            else:
                charges = monthly_charge * len(months)
            return "$" + str(charges)
        else:
            charges = inventory.monthly_service_charge_total
            return "$" + str(charges)