# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
import datetime

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class ticstockreport(models.TransientModel):
    _name = "ticl.stock.report"
    _description = "Stock Summary Report"

    @api.onchange('from_date', 'to_date')
    def onchange_week(self):
        # if self.from_date:
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
    inventory_summary_file = fields.Binary('Inbound Inventory Report')
    file_name = fields.Char('File Name')
    inventory_report_printed = fields.Boolean('Inbound Inventory Report')
    print_type = fields.Selection([('excel','Excel'),('pdf','PDF')], string='Print Type')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_id = fields.Many2many('stock.location', string='Location Name')


    @api.multi
    def action_print_inventory_inbound(self):
        print("====self.====",self.from_date,self.to_date)
        if self.print_type == 'pdf':

            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_inventory_xls_report.stock_report_pdf',
                'model': 'ticl.stock.report',
                'report_type': "qweb-pdf",

            }
        elif self.print_type == 'excel':
            new_from_date = self.from_date.strftime('%Y-%m-%d')
            new_to_date = self.to_date.strftime('%Y-%m-%d')
            workbook = xlwt.Workbook()
            amount_tot = 0
            column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            worksheet = workbook.add_sheet('Stock Summary Report')

            # worksheet.write(2, 3, self.env.user.company_id.name, easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 3, new_from_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 4, 'To', easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 5, new_to_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(3, 0, _('Type'), column_heading_style)
            worksheet.write(3, 1, _('Manufacturer'), column_heading_style)
            worksheet.write(3, 2, _('Unique Id'), column_heading_style)
            worksheet.write(3, 3, _('Model'), column_heading_style)
            worksheet.write(3, 4, _('Serial#'), column_heading_style)
            worksheet.write(3, 5, _('Condition'), column_heading_style)
            worksheet.write(3, 6, _('Received Date'), column_heading_style)
            worksheet.write(3, 7, _('Origin Location'), column_heading_style)
            worksheet.write(3, 8, _('Warehouse'), column_heading_style)
            worksheet.write(3, 9, _('Shipping Status'), column_heading_style)
            worksheet.write(3, 10, _('Comment'), column_heading_style)


            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 3000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 3000
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 6500
            worksheet.col(7).width = 6000
            worksheet.col(8).width = 5000
            worksheet.col(9).width = 3000
            worksheet.col(10).width = 5000
            worksheet.col(11).width = 3000
            worksheet.col(12).width = 5000
            worksheet.col(13).width = 3000

            row = 4
            for wizard in self:
                heading = 'Stock Summary Report'
                worksheet.write_merge(0, 0, 0, 10, heading, easyxf(
                    'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))

                inventory_objs = self.env['stock.move'].search([('received_date', '>=', wizard.from_date),
                                                                     ('received_date', '<=', wizard.to_date),
                                                                     ('warehouse_id', '=',wizard.warehouse_ids.ids)])
                print("===inventory_objs====",inventory_objs)
                for inventory in inventory_objs:
                    worksheet.write(row, 0, inventory.categ_id.name or '')
                    worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                    worksheet.write(row, 2, inventory.tel_unique_no or ' ')
                    worksheet.write(row, 3, inventory.product_id.name or '')
                    worksheet.write(row, 4, inventory.serial_number or '')
                    worksheet.write(row, 5, inventory.condition_id.name or '')
                    worksheet.write(row, 6, str(inventory.receive_date) or '')
                    worksheet.write(row, 7, inventory.origin or '')
                    worksheet.write(row, 8, inventory.warehouse_id.name or '')
                    worksheet.write(row, 9, inventory.shipping_status or '')
                    worksheet.write(row, 10, inventory.tel_note or '')

                    row += 1

                fp = io.BytesIO()
                workbook.save(fp)
                print("===workbook====",workbook)
                excel_file = base64.encodestring(fp.getvalue())
                self.inventory_summary_file = excel_file
                self.file_name = str(wizard.from_date) + '_' + 'Stock Summary Report.xls'
                fp.close()
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'Stock Summary Report',
                    'url': '/web/content/ticl.stock.report/%s/inventory_summary_file/%s.xls?download=true' % (
                        self.id,self.file_name)

                }

    @api.multi
    def get_report_values(self,data=None):
        docs = self.env['stock.move'].search([('receive_date', '>=', self.from_date),
                                                                 ('receive_date', '<=', self.to_date),
                                                                 ('warehouse_id', '=',self.warehouse_ids.ids)])
        return docs
