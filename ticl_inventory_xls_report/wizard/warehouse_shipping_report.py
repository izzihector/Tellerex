# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
import datetime
from odoo import models, fields, api, _
import calendar

class ticl_warehouse_shipping_report(models.TransientModel):
    _name = "ticl.warehouse.shipping.report"
    _description = "Warehouse Shipping Report"

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
    warehouse_shipping_file = fields.Binary('Warehouse Shipping Report')
    file_name = fields.Char('File Name')
    shipping_report_printed = fields.Boolean('Warehouse Shipping Report')
    print_type = fields.Selection([('excel','Excel'),('pdf','PDF')], string='Print Type')
    warehouse_ids = fields.Many2many('stock.location', string='Warehouse')


    #@api.multi
    def action_print_warehouse_shipping_report(self):
        if self.print_type == 'pdf':
            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_inventory_xls_report.warehouse_shipping_report_pdf',
                'model': 'ticl.warehouse.shipping.report',
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
            date_custom1 = '{0} {1}.{2}'.format(self.to_date.strftime('%b'), int(rd_1[2]), int(rd_1[0]))
            ans_1 = calendar.weekday(int(rd_1[0]), int(rd_1[1]), int(rd_1[2]))
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            worksheet = workbook.add_sheet('Warehouse Shipping Report')
            worksheet.write(1, 3, '{0} {1}'.format(days[ans], date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 4, 'To', easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 5, '{0} {1}'.format(days[ans_1], date_custom1), easyxf('font:height 200;font:bold True;align: horiz center;'))
             
            worksheet.write(3, 0, _('Odoo Shippment Id'), column_heading_style)
            worksheet.write(3, 1, _('Echo Shipment Id'), column_heading_style)
            worksheet.write(3, 2, _('Product'), column_heading_style)
            worksheet.write(3, 3, _('Manufacturer'), column_heading_style)
            worksheet.write(3, 4, _('Serial#'), column_heading_style)
            worksheet.write(3, 5, _('Type'), column_heading_style)
            worksheet.write(3, 6, _('Condition'), column_heading_style)
            worksheet.write(3, 7, _('XL'), column_heading_style)
            worksheet.write(3, 8, _('Shipment Date'), column_heading_style)
            worksheet.write(3, 9, _('Appointment Date'), column_heading_style)
            worksheet.write(3, 10, _('Employee'), column_heading_style)
            worksheet.write(3, 11, _('Origin Location'), column_heading_style)
            worksheet.write(3, 12, _('Destination Location'), column_heading_style)
            worksheet.write(3, 13, _('Fnding Doc Type'), column_heading_style)
            worksheet.write(3, 14, _('Funding Doc Number'), column_heading_style)
            worksheet.write(3, 15, _('Project Id'), column_heading_style)
            
           

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
            worksheet.col(11).width = 5000
            worksheet.col(12).width = 5000
            worksheet.col(13).width = 5000
            worksheet.col(14).width = 5000
            worksheet.col(15).width = 5000

            row = 4
            for wizard in self:
                heading = 'Warehouse Shipping Report'
                worksheet.write_merge(0, 0, 0, 15, heading, easyxf(
                    'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))


                if  wizard.warehouse_ids.ids == []:
                    shipping_objs = self.env['ticl.shipment.log.line'].search([('ticl_ship_id.appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('ticl_ship_id.appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                                     ('ticl_ship_id.state', '=', 'shipped')
                                                                     ])
                else:
                    shipping_objs = self.env['ticl.shipment.log.line'].search([('ticl_ship_id.appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('ticl_ship_id.appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                                     ('ticl_ship_id.sending_location_id', 'in', wizard.warehouse_ids.ids),
                                                                     ('ticl_ship_id.state', '=', 'shipped')
                                                                     ])


                for shipping in shipping_objs:
                    ship_date = str(shipping.ticl_ship_id.appointment_date_new).split(" ")
                    sd = ship_date[0].split('-')
                    appointment_date_new  = '{0}-{1}-{2}'.format(shipping.ticl_ship_id.appointment_date_new.strftime("%b"),int(sd[2]),int(sd[0]))
                    ans =calendar.weekday(int(sd[0]),int(sd[1]),int(sd[2]))
                    days = ["Mon", "Tue", "Wed", "Thur","Fri", "Sat", "Sun"]
                    appoint_date = str(shipping.ticl_ship_id.appointment_date_new).split(" ")
                    ad = appoint_date[0].split('-')
                    appointment_date_new  = '{0}-{1}-{2}'.format(shipping.ticl_ship_id.appointment_date_new.strftime("%b"),int(ad[2]),int(ad[0]))
                    ans =calendar.weekday(int(rd[0]),int(rd[1]),int(rd[2]))
                    days = ["Mon", "Tue", "Wed", "Thur","Fri", "Sat", "Sun"]
                    if shipping.xl_items == 'y':
                        xl_items = 'Yes'
                    elif shipping.xl_items == 'n':
                        xl_items = 'No'
                    else:
                        xl_items = ""

                    worksheet.write(row, 0, shipping.ticl_ship_id.name or '')
                    worksheet.write(row, 1, shipping.ticl_ship_id.echo_tracking_id or '')
                    worksheet.write(row, 2, shipping.product_id.name or '')
                    worksheet.write(row, 3, shipping.manufacturer_id.name or '')
                    worksheet.write(row, 4, shipping.serial_number or '')
                    worksheet.write(row, 5, shipping.tel_type.name or '')
                    worksheet.write(row, 6, shipping.condition_id.name or '')
                    worksheet.write(row, 7, xl_items or '')
                    worksheet.write(row, 8, '{0} {1}'.format(days[ans], appointment_date_new) or '')
                    worksheet.write(row, 9, '{0} {1}'.format(days[ans], appointment_date_new) or '')
                    worksheet.write(row, 10, shipping.ticl_ship_id.hr_employee_id.name or '')
                    worksheet.write(row, 11, shipping.ticl_ship_id.sending_location_id.name or '')
                    worksheet.write(row, 12, shipping.ticl_ship_id.receiving_location_id.name or '')
                    worksheet.write(row, 13, shipping.funding_doc_type or '')
                    worksheet.write(row, 14, shipping.funding_doc_number or '')
                    worksheet.write(row, 15, shipping.ticl_project_id or '')
                    
                    row += 1

                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.warehouse_shipping_file = excel_file
                self.file_name = str(wizard.from_date) + '_' + 'Warehouse Shipping Report.xls'
                fp.close()
                
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'Warehouse Shipping Report',
                    'url': '/web/content/ticl.warehouse.shipping.report/%s/warehouse_shipping_file/%s.xls?download=true' % (
                        self.id,self.file_name)

                }


    #@api.multi
    def get_from_date_values(self, from_date):
        x = from_date
        from_date = str(from_date).split(" ")
        rd = from_date[0].split('-')
        from_date = '{0} {1}.{2}'.format(x.strftime('%b'), int(rd[2]), int(rd[0]))
        ans = calendar.weekday(int(rd[0]), int(rd[1]), int(rd[2]))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dates = '{0} {1}'.format(days[ans], from_date)
        return dates

    #@api.multi
    def get_to_date_values(self, to_date):
        x = to_date
        to_date = str(to_date).split(" ")
        rd = to_date[0].split('-')
        to_date = '{0} {1}.{2}'.format(x.strftime('%b'), int(rd[2]), int(rd[0]))
        ans = calendar.weekday(int(rd[0]), int(rd[1]), int(rd[2]))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dates = '{0} {1}'.format(days[ans], to_date)
        return dates


    #@api.multi
    def get_warehouse_report_values(self,data=None):
        date_split_1 = str(self.from_date).split(" ")
        date_split_2 = str(self.to_date).split(" ")

        if  self.warehouse_ids.ids == []:
            docs = self.env['ticl.shipment.log.line'].search([('ticl_ship_id.appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                            ('ticl_ship_id.appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                            ('ticl_ship_id.state', '=', 'shipped')
                                                            ])
        else:
            docs = self.env['ticl.shipment.log.line'].search([('ticl_ship_id.appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                            ('ticl_ship_id.appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                            ('ticl_ship_id.sending_location_id', 'in', self.warehouse_ids.ids),
                                                            ('ticl_ship_id.state', '=', 'shipped')
                                                            ])
        return docs