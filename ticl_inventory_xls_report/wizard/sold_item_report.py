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
    _name = "ticl.sold.items.report"
    _description = "Received Stock Summary Report"

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
    warehouse_ids = fields.Many2many('stock.location', string='Warehouse')
    #location_id = fields.Many2many('stock.location', string='Location Name')
    categ_ids = fields.Many2many('product.category', 'stock_location_sold_categ', 'route_id', 'categ_id', 'Type', copy=False)



    #@api.multi
    def action_print_inventory_inbound(self):
        if self.print_type == 'pdf':

            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_inventory_xls_report.sold_items_report_pdf',
                'model': 'ticl.sold.items.report',
                'report_type': "qweb-pdf",

            }
        if self.print_type == 'excel':
            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'mm/dd/yy'
            workbook = xlwt.Workbook()
            workbook = xlwt.Workbook()
            date_split_1 = str(self.from_date).split(" ")
            date_split_2 = str(self.to_date).split(" ")
            fd = date_split_1[0].split('-')
            td = date_split_2[0].split('-')
            from_date_custom = '{1}/{2}/{3}'.format(self.from_date.strftime('%b'), int(fd[1]), int(fd[2]), int(fd[0][2:]))
            to_date_custom = '{1}/{2}/{3}'.format(self.to_date.strftime('%b'), int(td[1]), int(td[2]), int(td[0][2:]))
            column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
            worksheet = workbook.add_sheet('Sold Items Report')
            worksheet.write(1, 3, '{0}'.format(from_date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 4, 'To', easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(1, 5, '{0}'.format(to_date_custom), easyxf('font:height 200;font:bold True;align: horiz center;'))
            worksheet.write(3, 0, _('Type'), column_heading_style)
            worksheet.write(3, 1, _('Manufacturer'), column_heading_style)
            worksheet.write(3, 2, _('Model'), column_heading_style)
            worksheet.write(3, 3, _('Serial#'), column_heading_style)
            worksheet.write(3, 4, _('Count'), column_heading_style)
            worksheet.write(3, 5, _('Condition'), column_heading_style)
            worksheet.write(3, 6, _('Received Date'), column_heading_style)
            # worksheet.write(3, 7, _('Date Sold'), column_heading_style)
            # worksheet.write(3, 8, _('Gross Sale Price'), column_heading_style)

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
                heading = 'Sold Items Report'
                worksheet.write_merge(0, 0, 0, 8, heading, easyxf(
                    'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
                custom_list = []
                custom_list.append(('create_date', '>=', date_split_1[0] +' 00:00:00'))
                custom_list.append(('create_date', '<=', date_split_2[0] +' 23:59:59'))
                condition_id = self.env['ticl.condition'].search([('name','=','To Recommend')])
                custom_list.append(('condition_id','=',condition_id.id))
                if self.categ_ids:
                    custom_list.append(('categ_id', '=', self.categ_ids.ids))
                if self.warehouse_ids:
                    custom_list.append(('location_dest_id', '=', self.warehouse_ids.ids))
                inventory_objs = self.env['stock.move'].search(custom_list)

                # inventory_objs = self.env['stock.move'].search([('received_date', '>=', date_split_1[0] +' 00:00:00'),('received_date', '<=', date_split_2[0] +' 23:59:59'),('location_dest_id', '=',self.warehouse_ids.ids),('categ_id','=',self.categ_ids.ids)])
                list=[]
                single_list = ''
                location = ''
                lst_2 = []
                for i in inventory_objs:
                    list.append(i.product_id)
                for inventory in inventory_objs:
                    if inventory.received_date:
                        rd_date = inventory.received_date
                    else:
                        rd_date = ""
                    count = list.count(inventory.product_id)
                    if count <=1 :
                        worksheet.write(row, 0, inventory.categ_id.name or '')
                        worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                        worksheet.write(row, 2, inventory.product_id.name or '')
                        worksheet.write(row, 3, inventory.serial_number or '')
                        worksheet.write(row, 4, count or '',xlwt.easyxf("align: horiz left"))
                        worksheet.write(row, 5, inventory.condition_id.name or '')
                        worksheet.write(row, 6, rd_date, date_format or '')
                        # worksheet.write(row, 7, inventory.origin or '')
                        # worksheet.write(row, 8, inventory.location_dest_id.name or '')
                        row += 1

                    elif count > 1:
                        if inventory.product_id != single_list :
                            if inventory.product_id not in lst_2:
                                worksheet.write(row, 0, inventory.categ_id.name or '')
                                worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                                worksheet.write(row, 2, inventory.product_id.name or '')
                                worksheet.write(row, 3, inventory.serial_number or '')
                                if inventory.categ_id.name == "ATM":
                                    worksheet.write(row, 4, 1 or '', xlwt.easyxf("align: horiz left"))
                                else:
                                    worksheet.write(row, 4, count or '', xlwt.easyxf("align: horiz left"))
                                worksheet.write(row, 5, inventory.condition_id.name or '')
                                worksheet.write(row, 6, rd_date, date_format or '')
                                # worksheet.write(row, 7, inventory.origin or '')
                                # worksheet.write(row, 8, inventory.location_dest_id.name or '')
                                row += 1
                            single_list = inventory.product_id
                            location = inventory.location_id
                            lst_2.append(inventory.product_id)

                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.inventory_summary_file = excel_file
                self.file_name = str(wizard.from_date) + '_' + 'Sold Items Report'
                fp.close()
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'Sold Items Report',
                    'url': '/web/content/ticl.sold.items.report/%s/inventory_summary_file/%s.xls?download=true' % (
                        self.id,self.file_name)

                }

    #@api.multi
    def get_receive_date_values(self,received_date):
        if received_date:
            rd_date = str(received_date).split(" ")
            rd = rd_date[0].split('-')
            rd_date = '{1}/{2}/{3}'.format(received_date.strftime("%b"), int(rd[1]), int(rd[2]), int(rd[0][2:]))
            dates = '{0}'.format(rd_date)
            return dates

    #@api.multi
    def get_from_date_values(self, from_date):
        frm_date = str(from_date).split(" ")
        rd = frm_date[0].split('-')
        frm_date = '{1}/{2}/{3}'.format(from_date.strftime('%b'), int(rd[1]), int(rd[2]), int(rd[0][2:]))
        dates = '{0}'.format(frm_date)
        return dates

    #@api.multi
    def get_to_date_values(self, to_date):
        to_dt = str(to_date).split(" ")
        rd = to_dt[0].split('-')
        to_dt = '{1}/{2}/{3}'.format(to_date.strftime('%b'), int(rd[1]), int(rd[2]), int(rd[0][2:]))
        dates = '{0}'.format(to_dt)
        return dates

    #@api.multi
    def get_report_values(self,data=None):
        date_split_1 = str(self.from_date).split(" ")
        date_split_2 = str(self.to_date).split(" ")
        custom_list = []
        custom_list.append(('create_date', '>=', date_split_1[0] + ' 00:00:00'))
        custom_list.append(('create_date', '<=', date_split_2[0] + ' 23:59:59'))
        condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
        custom_list.append(('condition_id', '=', condition_id.id))
        if self.categ_ids:
            custom_list.append(('categ_id', '=', self.categ_ids.ids))
        if self.warehouse_ids:
            custom_list.append(('location_dest_id', '=', self.warehouse_ids.ids))
        docs = self.env['stock.move'].search(custom_list)
        lst = []
        lst_2 = []
        lst_3 = []
        origin = ''
        for j in docs:
            lst_2.append(j.product_id)
        for i in docs:
            if origin != i.product_id:
                count_origin = lst_2.count(i.product_id)
                if count_origin <= 1:
                    lst.append({'categ_id': i.categ_id.name,
                                'product_id': i.product_id.name,
                                'condition_id': i.condition_id.name,
                                'count': count_origin,
                                'serial_number': i.serial_number,
                                'manufacturer_id': i.manufacturer_id.name,
                                'received_date': i.received_date,
                                # 'origin': i.origin,
                                # 'location_dest_id': i.location_dest_id.name
                                })
                elif count_origin > 1:
                    if i.product_id not in lst_3:
                        if i.categ_id.name == "ATM":
                            count_origin = 1
                        lst.append({'categ_id': i.categ_id.name,
                                    'product_id': i.product_id.name,
                                    'condition_id': i.condition_id.name,
                                    'count': count_origin,
                                    'serial_number': i.serial_number,
                                    'manufacturer_id': i.manufacturer_id.name,
                                    'received_date': i.received_date,
                                    # 'origin': i.origin,
                                    # 'location_dest_id': i.location_dest_id.name
                                    })
                    origin = i.product_id
                    lst_3.append(i.product_id)
        return lst
