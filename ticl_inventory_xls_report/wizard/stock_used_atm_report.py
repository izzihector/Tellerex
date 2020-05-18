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
import calendar
from datetime import timedelta

class ticl_stock_used_atm_report(models.TransientModel):
    _name = "ticl.stock.used.atm.report"
    _description = "Processed ATM Stock Report"

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


    def default_condition(self):
        return self.env['ticl.condition'].search([('name', '=', 'Used')])


    from_date = fields.Datetime(string='From Date')
    to_date = fields.Datetime(string='To Date')
    inventory_used_atm_file = fields.Binary('Inbound Inventory Report')
    file_name = fields.Char('File Name')
    inventory_report_printed = fields.Boolean('Inbound Inventory Report')
    print_type = fields.Selection([('excel','Excel'),('pdf','PDF')], string='Print Type')
    warehouse_ids = fields.Many2many('stock.location', string='Warehouse')
    location_id = fields.Many2many('stock.location', string='Location Name')
    condition_id = fields.Many2one('ticl.condition', string="Type",default=default_condition)



    @api.multi
    def action_print_used_atm_report(self):
        if self.print_type == 'pdf':

            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_inventory_xls_report.stock_used_atm_report_pdf',
                'model': 'ticl.stock.used.atm.report',
                'report_type': "qweb-pdf",

            }
        if self.print_type == 'excel':
            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'mm/dd/yy'
            workbook = xlwt.Workbook()
            date_split_1 = str(self.from_date).split(" ")
            date_split_2 = str(self.to_date).split(" ")
            fd = date_split_1[0].split('-')
            td = date_split_2[0].split('-')
            from_date_custom = '{1}/{2}/{3}'.format(self.from_date.strftime('%b'), int(fd[1]), int(fd[2]), int(fd[0][2:]))
            to_date_custom = '{1}/{2}/{3}'.format(self.to_date.strftime('%b'), int(td[1]), int(td[2]), int(td[0][2:]))
            column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            worksheet = workbook.add_sheet('Processed ATM Stock Report')

            worksheet.write(1, 4, '{0}'.format(from_date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 5, 'To', easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 6, '{0}'.format(to_date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(3, 0, _('Manufacturer'), column_heading_style)
            worksheet.write(3, 1, _('Model'), column_heading_style)
            worksheet.write(3, 2, _('Serial#'), column_heading_style)
            worksheet.write(3, 3, _('Count'), column_heading_style)
            worksheet.write(3, 4, _('Status'), column_heading_style)
            worksheet.write(3, 5, _('Location'), column_heading_style)
            worksheet.write(3, 6, _('Condition'), column_heading_style)
            worksheet.write(3, 7, _('Type'), column_heading_style)
            worksheet.write(3, 8, _('Received Date'), column_heading_style)
            worksheet.write(3, 9, _('Date Processed'), column_heading_style)
            worksheet.write(3, 10, _('Comments'), column_heading_style)


            worksheet.col(0).width = 5000
            worksheet.col(1).width = 6000
            worksheet.col(2).width = 3000
            worksheet.col(3).width = 2000
            worksheet.col(4).width = 5000
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 5000
            worksheet.col(7).width = 3000
            worksheet.col(8).width = 5000
            worksheet.col(9).width = 5000
            worksheet.col(10).width = 8000

            row = 4
            to_recommend = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
            ref_required = self.env['ticl.condition'].search([('name', '=', 'Refurb Required')])
            quarantine = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
            sig_damage = self.env['ticl.condition'].search([('name', '=', 'Significant Damage')])
            for wizard in self:
                heading = 'Processed ATM Stock Report'
                worksheet.write_merge(0, 0, 0, 10, heading, easyxf(
                    'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))

                inventory_objs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                                                     ('received_date', '<=', date_split_2[0] +' 23:59:59'),
                                                                ('location_dest_id', '=', self.warehouse_ids.ids),
                                                                ('condition_id', 'in',
                                                                 [to_recommend.id, ref_required.id, sig_damage.id, quarantine.id]),
                                                                ('status', '=','inventory')
                                                                     ])
                for inventory in inventory_objs:
                    if inventory.processed_date:
                        pd_date = inventory.processed_date
                    else:
                        pd_date=''

                    worksheet.write(row, 0, inventory.manufacturer_id.name or '')
                    worksheet.write(row, 1, inventory.product_id.name or '')
                    worksheet.write(row, 2, inventory.serial_number or '')
                    worksheet.write(row, 3, inventory.product_uom_qty or '')
                    worksheet.write(row, 4, inventory.status or '')
                    worksheet.write(row, 5, inventory.location_dest_id.name or '')
                    worksheet.write(row, 6, inventory.condition_id.name or '')
                    worksheet.write(row, 7, inventory.categ_id.name or '')
                    worksheet.write(row, 8, inventory.received_date, date_format or '')
                    worksheet.write(row, 9, pd_date, date_format or '')
                    worksheet.write(row, 10, inventory.tel_note or '')

                    row += 1

                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.inventory_used_atm_file = excel_file
                self.file_name = str(wizard.from_date) + '_' + 'Processed ATM Stock Report.xls'
                fp.close()
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'Processed ATM Stock Report',
                    'url': '/web/content/ticl.stock.used.atm.report/%s/inventory_used_atm_file/%s.xls?download=true' % (
                        self.id,self.file_name)

                }


    @api.multi
    def get_receive_date_values(self,received_date):
        rd_date = str(received_date).split(" ")
        rd = rd_date[0].split('-')
        rd_date = '{1}/{2}/{3}'.format(received_date.strftime("%b"), int(rd[1]), int(rd[2]), int(rd[0][2:]))
        dates = '{0}'.format(rd_date)
        return dates

    @api.multi
    def get_processed_date_values(self,processed_date):
        if processed_date:
            pd_date = str(processed_date).split(" ")
            pd = pd_date[0].split('-')
            pd_date = '{1}/{2}/{3}'.format(processed_date.strftime("%b"), int(pd[1]), int(pd[2]), int(pd[0][2:]))
            dates = '{0}'.format(pd_date)
            return dates

    @api.multi
    def get_from_date_values(self, from_date):
        frm_date = str(from_date).split(" ")
        rd = frm_date[0].split('-')
        frm_date = '{1}/{2}/{3}'.format(from_date.strftime('%b'), int(rd[1]), int(rd[2]), int(rd[0][2:]))
        dates = '{0}'.format(frm_date)
        return dates

    @api.multi
    def get_to_date_values(self, to_date):
        to_dt = str(to_date).split(" ")
        rd = to_dt[0].split('-')
        to_dt = '{1}/{2}/{3}'.format(to_date.strftime('%b'), int(rd[1]), int(rd[2]), int(rd[0][2:]))
        dates = '{0}'.format(to_dt)
        return dates


    @api.multi
    def get_used_atm_report_values(self,data=None):
        date_split_1 = str(self.from_date).split(" ")
        date_split_2 = str(self.to_date).split(" ")
        to_recommend = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
        ref_required = self.env['ticl.condition'].search([('name', '=', 'Refurb Required')])
        sig_damage = self.env['ticl.condition'].search([('name', '=', 'Significant Damage')])
        quarantine = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
        docs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                                        ('received_date', '<=', date_split_2[0] +' 23:59:59'),
                                                        ('location_dest_id', '=',self.warehouse_ids.ids),
                                                        ('status', '=','inventory'),
                                                        ('condition_id', 'in',[to_recommend.id,ref_required.id,sig_damage.id, quarantine.id])])        
        return docs