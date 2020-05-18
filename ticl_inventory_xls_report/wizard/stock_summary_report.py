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


class ticstockreport(models.TransientModel):
    _name = "ticl.stock.report"
    _description = "Received Stock Summary Report"

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
    inventory_summary_file = fields.Binary('Inbound Inventory Report')
    file_name = fields.Char('File Name')
    inventory_report_printed = fields.Boolean('Inbound Inventory Report')
    print_type = fields.Selection([('excel','Excel'),('pdf','PDF')], string='Print Type')
    warehouse_ids = fields.Many2many('stock.location', string='Warehouse')
    location_id = fields.Many2many('stock.location', string='Location Name')


    #@api.multi
    def action_print_inventory_inbound(self):
        if self.print_type == 'pdf':

            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_inventory_xls_report.stock_report_pdf',
                'model': 'ticl.stock.report',
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
            worksheet = workbook.add_sheet('Received Stock Summary Report')
            worksheet.write(1, 3, '{0} {1}'.format(days[ans], date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 4, 'To', easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 5, '{0} {1}'.format(days[ans_1], date_custom1), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(3, 0, _('Type'), column_heading_style)
            worksheet.write(3, 1, _('Manufacturer'), column_heading_style)
            worksheet.write(3, 2, _('Model'), column_heading_style)
            worksheet.write(3, 3, _('Serial#'), column_heading_style)
            worksheet.write(3, 4, _('Count'), column_heading_style)
            worksheet.write(3, 5, _('Condition'), column_heading_style)
            worksheet.write(3, 6, _('Received Date'), column_heading_style)
            worksheet.write(3, 7, _('Receipt Id'), column_heading_style)
            worksheet.write(3, 8, _('Warehouse'), column_heading_style)


            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 3000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 4500
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 5800
            worksheet.col(7).width = 6000
            worksheet.col(8).width = 5000
            worksheet.col(9).width = 3000
            worksheet.col(10).width = 5000
            worksheet.col(11).width = 3000
            worksheet.col(12).width = 5000
            worksheet.col(13).width = 3000

            row = 4
            for wizard in self:
                heading = 'Received Stock Summary Report'
                worksheet.write_merge(0, 0, 0, 8, heading, easyxf(
                    'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
                inventory_objs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),('received_date', '<=', date_split_2[0] +' 23:59:59'),('location_dest_id', '=',self.warehouse_ids.ids)])
                list=[]
                single_list = ''
                for i in inventory_objs:
                    list.append(i.origin)
                for inventory in inventory_objs:
                    reveive_date = str(inventory.received_date).split(" ")
                    rd = reveive_date[0].split('-')
                    reveived_date  = '{0}-{1}-{2}'.format(inventory.received_date.strftime("%b"),int(rd[2]),int(rd[0]))
                    ans =calendar.weekday(int(rd[0]),int(rd[1]),int(rd[2]))
                    count = list.count(inventory.origin)
                    if count <=1 :
                        worksheet.write(row, 0, inventory.categ_id.name or '')
                        worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                        worksheet.write(row, 2, inventory.product_id.name or '')
                        worksheet.write(row, 3, inventory.serial_number or '')
                        worksheet.write(row, 4, count or '',xlwt.easyxf("align: horiz left"))
                        worksheet.write(row, 5, inventory.condition_id.name or '')
                        worksheet.write(row, 6, '{0} {1}'.format(days[ans], reveived_date) or '')
                        worksheet.write(row, 7, inventory.origin or '')
                        worksheet.write(row, 8, inventory.location_dest_id.name or '')

                        row += 1
                    elif count >1:
                        if inventory.origin != single_list :
                            summary_log = self.env['ticl.receipt'].search([('name','=',inventory.origin)])
                            for inv in summary_log.ticl_receipt_lines:
                                worksheet.write(row, 0, inv.tel_type.name or '')
                                worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                                worksheet.write(row, 2, inv.product_id.name or '')
                                worksheet.write(row, 3, inv.serial_number or '')
                                worksheet.write(row, 4, inv.count_number or '',xlwt.easyxf("align: horiz left"))
                                worksheet.write(row, 5, inv.condition_id.name or '')
                                worksheet.write(row, 6, '{0} {1}'.format(days[ans],reveived_date) or '')
                                worksheet.write(row, 7, inventory.origin or '')
                                worksheet.write(row, 8, inventory.location_dest_id.name or '')

                                row += 1
                            single_list = inventory.origin
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.inventory_summary_file = excel_file
                self.file_name = str(wizard.from_date) + '_' + 'Received Stock Summary Report'
                fp.close()
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'Received Stock Summary Report',
                    'url': '/web/content/ticl.stock.report/%s/inventory_summary_file/%s.xls?download=true' % (
                        self.id,self.file_name)

                }
   # @api.multi
    def get_receive_date_values(self,received_date):
        reveived_date = str(received_date).split(" ")
        rd = reveived_date[0].split('-')
        reveived_date = '{0}-{1}-{2}'.format(received_date.strftime("%b"), int(rd[2]), int(rd[0]))
        ans = calendar.weekday(int(rd[0]), int(rd[1]), int(rd[2]))
        days = ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"]
        dates = '{0} {1}'.format(days[ans],reveived_date)
        return dates


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
    def get_report_values(self,data=None):
        date_split_1 = str(self.from_date).split(" ")
        date_split_2 = str(self.to_date).split(" ")
        docs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),
                                              ('received_date', '<=', date_split_2[0] +' 23:59:59'),
                                            ('location_dest_id', '=',self.warehouse_ids.ids)])
        lst = []
        lst_2 = []
        origin =''
        for j in docs:
            lst_2.append(j.origin)
        for i in docs:
            if origin != i.origin :
                count_origin = lst_2.count(i.origin)
                if count_origin <=1 :
                    lst.append({'categ_id': i.categ_id.name,
                    'product_id': i.product_id.name,
                    'condition_id': i.condition_id.name,
                    'count': count_origin,
                    'serial_number': i.serial_number,
                    'manufacturer_id': i.manufacturer_id.name,
                    'received_date': i.received_date,
                    'origin': i.origin,
                    'location_dest_id': i.location_dest_id.name })
                elif count_origin >1 :
                    summary_log = self.env['ticl.receipt'].search([('name', '=', i.origin)]).ticl_receipt_lines
                    for inv in summary_log:
                        lst.append({'categ_id': inv.tel_type.name,
                                    'product_id': inv.product_id.name,
                                    'condition_id': inv.condition_id.name,
                                    'count': inv.count_number,
                                    'serial_number': inv.serial_number,
                                    'manufacturer_id': inv.manufacturer_id.name,
                                    'received_date': i.received_date,
                                    'origin': i.origin,
                                    'location_dest_id': i.location_dest_id.name})
                origin = i.origin
        return lst
