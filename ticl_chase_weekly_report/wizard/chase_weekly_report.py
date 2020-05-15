# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from pytz import timezone
import pytz
from xlrd import open_workbook
import xlrd

from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
import datetime
from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import calendar
from io import BytesIO
import xlsxwriter
from xlrd import open_workbook
import datetime as r_datetime

class ticl_chase_weekly_report(models.TransientModel):
    _name = "ticl.chase.weekly.report"
    _description = "Chase Weekly Report"

    from_date = fields.Datetime(string='From Date')
    to_date = fields.Datetime(string='To Date')
    chase_summary_file = fields.Binary('Chase Weekly Report')
    file_name = fields.Char('File Name')
    chase_report_printed = fields.Boolean('Chase Weekly Report')
    warehouse_ids = fields.Many2many('stock.location', string='Warehouse')
    report_type = fields.Many2many('ticl.report.type', string='Report Type')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    product_ids = fields.Many2many('product.product', 'ms_report_stock_product_rel', 'ms_report_stock_id',
                                   'product_id', 'Products')
    categ_ids = fields.Many2many('product.category', 'ms_report_stock_categ_rel', 'ms_report_stock_id',
                                 'categ_id', 'Categories')

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    @api.onchange('from_date', 'to_date')
    def onchange_week(self):
        from_date = str(self.from_date)
        to_date = str(self.to_date)
        if to_date < from_date:
            self.from_date = ''
            self.to_date = ''
            return {
                'warning': {
                    'title': "Warning",
                    'message': "To Date Should be higher than From Date",
                }
            }


    # @api.onchange('to_date')
    # def onchange_to_date(self):
    #     if self.to_date:
    #         self.from_date = self.to_date - timedelta(days=7)

    # @api.multi
    def action_print_received_items_report(self):
        workbook = xlwt.Workbook()
        if self.report_type.ids == []:
            self.report_type = self.env['ticl.report.type'].search([])
        for ids in self.report_type:
            if ids.name == "Inventory Summary":
                data = self.read()[0]
                product_ids = data['product_ids']
                categ_ids = data['categ_ids']
                warehouse_ids = data['warehouse_ids']

                if categ_ids:
                    product_ids = self.env['product.product'].search([('categ_id', 'in', categ_ids)])
                    product_ids = [prod.id for prod in product_ids]
                where_product_ids = " 1=1 "
                where_product_ids2 = " 1=1 "
                if product_ids:
                    where_product_ids = " quant.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
                    where_product_ids2 = " product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
                warehouse_ids2 = self.env['stock.location'].search([('is_location', '=', True)])
                ids_location = [loc.id for loc in warehouse_ids2]
                where_warehouse_ids = " quant.location_id in %s" % str(tuple(ids_location)).replace(',)', ')')
                # where_warehouse_ids2 = " location_id in %s"%str(tuple(ids_location)).replace(',)', ')')
                if warehouse_ids:
                    # where_warehouse_ids = " quant.location_id in %s"%str(tuple(warehouse_ids)).replace(',)', ')')
                    where_warehouse_ids2 = " location_id in %s" % str(tuple(warehouse_ids)).replace(',)', ')')

                datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
                date_string = self.get_default_date_model().strftime("%Y-%m-%d")
                report_name = 'Inventory Summary'
                datetime_format = '%Y-%m-%d %H:%M:%S'
                utc = datetime.now().strftime(datetime_format)
                utc = datetime.strptime(utc, datetime_format)
                tz = self.get_default_date_model().strftime(datetime_format)
                tz = datetime.strptime(tz, datetime_format)
                duration = tz - utc
                hours = duration.seconds / 60 / 60
                if hours > 1 or hours < 1:
                    hours = str(hours) + ' hours'
                else:
                    hours = str(hours) + ' hour'

                projects_dict = {}
                self.env.cr.execute("""
                                                       SELECT
                                                       loc.complete_name as location,
                                                       manufacturer.name as manufacturer,
                                                       prod_tmpl.name as product,
                                                       count(*),
                                                       move.inventory_status as Status,
                                                       condition.name as condition,
                                                       categ.name as prod_categ

                                                       from ticl_receipt_log_summary_line move
                                                       LEFT JOIN 
                                                       ticl_receipt_log_summary log on log.id = move.ticl_receipt_summary_id
                                                       LEFT JOIN 
                                                       stock_location loc on loc.id = log.receiving_location_id
                                                       LEFT JOIN 
                                                       manufacturer_order manufacturer on manufacturer.id=move.manufacturer_id
                                                       LEFT JOIN 
                                                       product_product prod on prod.id=move.product_id
                                                       LEFT JOIN 
                                                       product_template prod_tmpl on prod_tmpl.id=prod.product_tmpl_id
                                                       LEFT JOIN 
                                                       ticl_condition condition on condition.id=move.condition_id
                                                       LEFT JOIN 
                                                       product_category categ on categ.id=prod_tmpl.categ_id 
                                                       where loc.is_location=True AND move.check_sale=False
                                                       GROUP BY
                                                       product, manufacturer, prod_categ, condition, location, Status         

                                                   """)

                result = self.env.cr.fetchall()

                projects_dict = {}
                for pr in result:
                    if pr[0] not in projects_dict:
                        projects_dict[pr[0]] = pr[1]
                fp = BytesIO()
                column_heading_style = easyxf(
                    'font:name Calibri,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('Inventory Summary')
                # worksheet.write(1, 3, report_name,
                #                 easyxf('font:height 200;font:bold True;align: horiz center;'))
                worksheet.col(0).width = 5000
                worksheet.col(1).width = 5000
                worksheet.col(2).width = 3000
                worksheet.col(3).width = 5000
                worksheet.col(4).width = 3000
                worksheet.col(5).width = 4500
                worksheet.col(6).width = 5000

                worksheet.write(0, 0, _('Location'), column_heading_style)
                worksheet.write(0, 1, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 2, _('Model'), column_heading_style)
                worksheet.write(0, 3, _('Count'), column_heading_style)
                worksheet.write(0, 4, _('Status'), column_heading_style)
                worksheet.write(0, 5, _('Condition'), column_heading_style)
                worksheet.write(0, 6, _('Type'), column_heading_style)
                row = 1
                for i in range(0, len(result)):
                    worksheet.write(row, 0, result[i][0] or '')
                    worksheet.write(row, 1, result[i][1] or '')
                    worksheet.write(row, 2, result[i][2] or '')
                    worksheet.write(row, 3, result[i][3] or '')
                    worksheet.write(row, 4, result[i][4] or '')
                    worksheet.write(row, 5, result[i][5] or '')
                    if(result[i][6] == 'ATM'):
                        worksheet.write(row, 6, 'Unit' or '')
                    else:
                        worksheet.write(row, 6, result[i][6] or '')
                    row += 1
            if ids.name == "Inventory Detail":
                # date_split_1 = str(self.to_date - timedelta(days=7)).split(" ")
                # date_split_1 = str(self.to_date - timedelta(days=7)).split(" ")
                date_split_1 = str(self.from_date).split(" ")
                date_split_2 = str(self.to_date).split(" ")
                column_heading_style = easyxf(
                    'font: name Calibri,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('Inventory Detail Report')
                worksheet.write(0, 0, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 1, _('Model'), column_heading_style)
                worksheet.write(0, 2, _('Serial#'), column_heading_style)
                worksheet.write(0, 3, _('Count'), column_heading_style)
                worksheet.write(0, 4, _('Status'), column_heading_style)
                worksheet.write(0, 5, _('Received Date'), column_heading_style)
                worksheet.write(0, 6, _('Origin Location'), column_heading_style)
                worksheet.write(0, 7, _('Location'), column_heading_style)
                worksheet.write(0, 8, _('Condition'), column_heading_style)
                worksheet.write(0, 9, _('Type'), column_heading_style)
                worksheet.write(0, 10, _('Comments'), column_heading_style)
                worksheet.col(0).width = 5000
                worksheet.col(1).width = 7500
                worksheet.col(2).width = 3000
                worksheet.col(3).width = 5000
                worksheet.col(4).width = 4500
                worksheet.col(5).width = 5000
                worksheet.col(6).width = 5800
                worksheet.col(7).width = 6000
                worksheet.col(8).width = 5000
                worksheet.col(9).width = 3000
                worksheet.col(10).width = 3000
                row = 1
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'mm/dd/yy'

                self.env.cr.execute("""SELECT
                                        loc.name as location,
                                        manufacturer.name as manufacturer,
                                        prod_tmpl.name as product,
                                        count(*),
                                        move.serial_number as serial,
                                        condition.name as condition,
                                        categ.name as prod_categ,
                                        move.tel_note as note,
                                        log.delivery_date as receipt,
                                        send.name as origin
                                        from ticl_receipt_log_summary_line move
                                        LEFT JOIN 
                                        ticl_receipt_log_summary log on log.id = move.ticl_receipt_summary_id
                                        LEFT JOIN 
                                        stock_location loc on loc.id = log.receiving_location_id
                                        LEFT JOIN 
                                        res_partner send on send.id = log.sending_location_id
                                        LEFT JOIN 
                                        manufacturer_order manufacturer on manufacturer.id=move.manufacturer_id
                                        LEFT JOIN 
                                        product_product prod on prod.id=move.product_id
                                        LEFT JOIN 
                                        product_template prod_tmpl on prod_tmpl.id=prod.product_tmpl_id
                                        LEFT JOIN 
                                        ticl_condition condition on condition.id=move.condition_id
                                        LEFT JOIN 
                                        product_category categ on categ.id=prod_tmpl.categ_id 
                                        where loc.is_location=True AND move.check_sale=False AND categ.name in ('ATM','XL')
                                        GROUP BY
                                        product, manufacturer, prod_categ, condition, location , serial , note , receipt , origin
                                        UNION ALL
                                        SELECT
                                        loc.name as location,
                                        manufacturer.name as manufacturer,
                                        prod_tmpl.name as product,
                                        count(*),
                                        max(move.serial_number) as serial,
                                        condition.name as condition,
                                        categ.name as prod_categ,
                                        max(move.tel_note) as note,
                                        max(log.delivery_date) as receipt,
                                        max(send.name) as origin
                                        from ticl_receipt_log_summary_line move
                                        LEFT JOIN 
                                        ticl_receipt_log_summary log on log.id = move.ticl_receipt_summary_id
                                        LEFT JOIN 
                                        stock_location loc on loc.id = log.receiving_location_id
                                        LEFT JOIN 
                                        res_partner send on send.id = log.sending_location_id
                                        LEFT JOIN 
                                        manufacturer_order manufacturer on manufacturer.id=move.manufacturer_id
                                        LEFT JOIN 
                                        product_product prod on prod.id=move.product_id
                                        LEFT JOIN 
                                        product_template prod_tmpl on prod_tmpl.id=prod.product_tmpl_id
                                        LEFT JOIN 
                                        ticl_condition condition on condition.id=move.condition_id
                                        LEFT JOIN 
                                        product_category categ on categ.id=prod_tmpl.categ_id 
                                        where loc.is_location=True AND move.check_sale=False AND categ.name not in ('ATM','XL')
                                        GROUP BY
                                        product, manufacturer, prod_categ, condition, location
                                            """)
                result = self.env.cr.fetchall()

                for i in range(0,len(result)):
                    worksheet.write(row, 0, result[i][1] or '')
                    worksheet.write(row, 1, result[i][2] or '')
                    worksheet.write(row, 2, result[i][4] or '')
                    worksheet.write(row, 3, result[i][3] or '')
                    worksheet.write(row, 4, 'Inventory' or '')
                    if result[i][6] == "ATM" or result[i][6] == "XL":
                        if result[i][8] != None:
                            c_5 = str(result[i][8]).split(' ')[0].split('-')
                            c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                        else:
                            c5 = ''
                        worksheet.write(row, 5, c5 or '')
                        worksheet.write(row, 6, result[i][9] or '')
                        worksheet.write(row, 10, result[i][7] or '')
                    else:
                        worksheet.write(row, 5, '' or '')
                        worksheet.write(row, 6, '' or '')
                        worksheet.write(row, 10, '' or '')

                    # worksheet.write(row, 6, result[i][9] or '')
                    worksheet.write(row, 7, result[i][0] or '')
                    worksheet.write(row, 8, result[i][5] or '')
                    if(result[i][6] == 'ATM'):
                        worksheet.write(row, 9, 'Unit' or '')
                    else:
                        worksheet.write(row, 9, result[i][6] or '')
                    # worksheet.write(row, 10, result[i][7] or '')
                    row += 1

            if ids.name == "Received":
                date_split_1 = str(self.from_date).split(" ")
                date_split_2 = str(self.to_date).split(" ")
                if not self.from_date or not self.to_date:
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view or False
                    context = dict(self._context or {})
                    context['message'] = "Please Enter From and To date for Received Report"
                    return {
                        'name': 'Warning',
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sh.message.wizard',
                        'view': [('view', 'form')],
                        'target': 'new',
                        'context': context,
                    }
                column_heading_style = easyxf(
                    'font: name Calibri, bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('Received')
                worksheet.write(0, 0, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 1, _('Model'), column_heading_style)
                worksheet.write(0, 2, _('Serial#'), column_heading_style)
                worksheet.write(0, 3, _('Count'), column_heading_style)

                worksheet.write(0, 4, _('Status'), column_heading_style)
                worksheet.write(0, 5, _('Received Date'), column_heading_style)
                worksheet.write(0, 6, _('Origin Location'), column_heading_style)
                worksheet.write(0, 7, _('Location'), column_heading_style)
                worksheet.write(0, 8, _('Condition'), column_heading_style)
                worksheet.write(0, 9, _('Type'), column_heading_style)
                # worksheet.write(0, 10, _('Receipt ID'), column_heading_style)

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
                # worksheet.col(10).width = 3000

                row = 1
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'mm/dd/yy'
                for wizard in self:
                    if wizard.warehouse_ids.ids == []:
                        inventory_objs = self.env['ticl.receipt.log.summary.line'].search(
                            [('ticl_receipt_summary_id.delivery_date', '>=', date_split_1[0] + ' 00:00:00'),
                             ('ticl_receipt_summary_id.delivery_date', '<=', date_split_2[0] + ' 23:59:59')
                             ])
                    else:
                        inventory_objs = self.env['ticl.receipt.log.summary.line'].search(
                            [('ticl_receipt_summary_id.delivery_date', '>=', date_split_1[0] + ' 00:00:00'),
                             ('ticl_receipt_summary_id.delivery_date', '<=', date_split_2[0] + ' 23:59:59'),
                             ('ticl_receipt_summary_id.receiving_location_id', 'in', wizard.warehouse_ids.ids)])

                    custom_list = []
                    single_list = ''
                    for i in inventory_objs:
                        custom_list.append(i.ticl_receipt_summary_id.name)
                    for inventory in inventory_objs:
                        count = custom_list.count(inventory.ticl_receipt_summary_id.name)
                        if count <= 1:
                            worksheet.write(row, 0, inventory.manufacturer_id.name or '')
                            worksheet.write(row, 1, inventory.product_id.name or '')
                            worksheet.write(row, 2, inventory.serial_number or '')
                            worksheet.write(row, 3, count or '')
                            worksheet.write(row, 4, 'Received' or '')
                            if inventory.ticl_receipt_summary_id.delivery_date not in (None,False,''):
                                c_5 = str(inventory.ticl_receipt_summary_id.delivery_date).split(' ')[0].split('-')
                                c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                            else:
                                c5 = ''
                            worksheet.write(row, 5, c5 or '')
                            worksheet.write(row, 6, inventory.ticl_receipt_summary_id.sending_location_id.name or '')
                            worksheet.write(row, 7, inventory.ticl_receipt_summary_id.receiving_location_id.name or '')
                            worksheet.write(row, 8, inventory.condition_id.name or '')
                            if(inventory.tel_type.name == 'ATM'):
                                worksheet.write(row, 9, 'Unit' or '')
                            else:
                                worksheet.write(row, 9, inventory.tel_type.name or '')
                            # worksheet.write(row, 10, inventory.ticl_receipt_summary_id.name or '')
                            row += 1
                        elif count > 1:
                            if inventory.ticl_receipt_summary_id.name != single_list:
                                summary_log = self.env['ticl.receipt'].search(
                                    [('name', '=', inventory.ticl_receipt_summary_id.name)])
                                for inv in summary_log.ticl_receipt_lines:
                                    worksheet.write(row, 0, inv.manufacturer_id.name or '')
                                    worksheet.write(row, 1, inv.product_id.name or '')
                                    worksheet.write(row, 2, inv.serial_number or '')
                                    worksheet.write(row, 3, inv.count_number or '')
                                    worksheet.write(row, 4, 'Received' or '')
                                    if inventory.ticl_receipt_summary_id.delivery_date not in (None,False,''):
                                        c_5 = str(inventory.ticl_receipt_summary_id.delivery_date).split(' ')[0].split('-')
                                        c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                    else:
                                        c5 = ''
                                    worksheet.write(row, 5, c5 or '')
                                    worksheet.write(row, 6,
                                                    inventory.ticl_receipt_summary_id.sending_location_id.name or '')
                                    worksheet.write(row, 7,
                                                    inventory.ticl_receipt_summary_id.receiving_location_id.name or '')
                                    worksheet.write(row, 8, inv.condition_id.name or '')
                                    if (inv.tel_type.name == 'ATM'):
                                        worksheet.write(row, 9, 'Unit' or '')
                                    else:
                                        worksheet.write(row, 9, inv.tel_type.name or '')
                                    # worksheet.write(row, 10, inventory.ticl_receipt_summary_id.name or '')

                                    row += 1
                                single_list = inventory.ticl_receipt_summary_id.name

            if ids.name == "Shipped":
                date_split_1 = str(self.from_date).split(" ")
                date_split_2 = str(self.to_date).split(" ")
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'mm/dd/yy'
                column_heading_style = easyxf(
                    'font: name Calibri, bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('Shipped')
                worksheet.write(0, 0, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 1, _('Model'), column_heading_style)
                worksheet.write(0, 2, _('Serial #'), column_heading_style)
                worksheet.write(0, 3, _('Count'), column_heading_style)
                worksheet.write(0, 4, _('Status'), column_heading_style)
                worksheet.write(0, 5, _('Received Date'), column_heading_style)
                worksheet.write(0, 6, _('Origin Location'), column_heading_style)
                worksheet.write(0, 7, _('Location'), column_heading_style)
                worksheet.write(0, 8, _('Condition'), column_heading_style)
                worksheet.write(0, 9, _('Type'), column_heading_style)
                worksheet.write(0, 10, _('Shipment Type'), column_heading_style)
                worksheet.write(0, 11, _('Shipment Date'), column_heading_style)
                worksheet.write(0, 12, _('Funding Doc Type'), column_heading_style)
                worksheet.write(0, 13, _('Funding Doc Number'), column_heading_style)
                worksheet.write(0, 14, _('Project Id'), column_heading_style)
                # worksheet.write(0, 15, _('Comments'), column_heading_style)

                worksheet.col(0).width = 5000
                worksheet.col(1).width = 5000
                worksheet.col(2).width = 5000
                worksheet.col(3).width = 5000
                worksheet.col(4).width = 5000
                worksheet.col(5).width = 5000
                worksheet.col(6).width = 5000
                worksheet.col(7).width = 8000
                worksheet.col(8).width = 5000
                worksheet.col(9).width = 5000
                worksheet.col(10).width = 5000
                worksheet.col(11).width = 5000
                worksheet.col(12).width = 5000
                worksheet.col(13).width = 5000
                worksheet.col(14).width = 5000
                worksheet.col(15).width = 5000

                row = 1
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'mm/dd/yy'
                for wizard in self:
                    self.env.cr.execute("""select DISTINCT ON (rm_dup.lot) lot,rm_dup.manufacturer_id,rm_dup.product_id, rm_dup.count_number,rm_dup.state,rm_dup.line_id,rm_dup.sending_location_id,rm_dup.receiving_location_id,rm_dup.condition_id,rm_dup.tel_type,rm_dup.shipment_type,rm_dup.appointment_date_new,rm_dup.funding_doc_type,rm_dup.funding_doc_number,rm_dup.ticl_project_id,rm_dup.serial_number from (select tl.manufacturer_id as manufacturer_id,tl.product_id as product_id,spl.name as lot,CAST(tl.count_number AS INT) as count_number,
                            ts.state as state,tl.id as line_id,ts.sending_location_id as sending_location_id,ts.receiving_location_id as receiving_location_id,tl.condition_id as condition_id,tl.tel_type as tel_type,ts.shipment_type as shipment_type,
                            ts.appointment_date_new as appointment_date_new,tl.funding_doc_type as funding_doc_type,tl.funding_doc_number as funding_doc_number,tl.ticl_project_id as ticl_project_id,tl.serial_number as serial_number
                            from ticl_shipment_log_line as tl,ticl_shipment_log as ts,product_category as pc,stock_production_lot as spl where ts.state='shipped' 
                            and ts.id=tl.ticl_ship_id and pc.name in ('ATM','XL') and tl.tel_type=pc.id and spl.id=tl.lot_id and tl.lot_id is not null) as rm_dup;
                            """)
                    list_0 = self.env.cr.fetchall()
                    self.env.cr.execute("""select tl.lot_id as lot,tl.manufacturer_id as manufacturer_id,tl.product_id as product_id,CAST(tl.count_number AS INT) as count_number,ts.state as state,tl.id as line_id,
                            ts.sending_location_id as sending_location_id,ts.receiving_location_id as receiving_location_id,tl.condition_id as condition_id,tl.tel_type as tel_type,ts.shipment_type as shipment_type,
                            ts.appointment_date_new as appointment_date_new,tl.funding_doc_type as funding_doc_type,tl.funding_doc_number as funding_doc_number,tl.ticl_project_id as ticl_project_id,tl.serial_number as serial_number from ticl_shipment_log_line as tl,
                            ticl_shipment_log as ts,product_category as pc where ts.state='shipped' and ts.id=tl.ticl_ship_id and pc.name in ('ATM','XL') and tl.tel_type=pc.id and tl.lot_id is null;""")
                    list_1 = self.env.cr.fetchall()
                    self.env.cr.execute("""select min(tl.lot_id) as lot,min(tl.manufacturer_id) as manufacturer_id,min(tl.product_id) as product_id,count(CAST(tl.count_number AS INT)) as count_number,min(ts.state) as state,min(tl.id) as line_id,min(ts.sending_location_id) as  sending_location_id,min(ts.receiving_location_id) as receiving_location_id,min(tl.condition_id) as condition_id,
                        min(tl.tel_type) as tel_type,min(ts.shipment_type) as shipment_type,min(ts.appointment_date_new) as appointment_date_new,min(tl.funding_doc_type) as funding_doc_type,
                        min(tl.funding_doc_number) as funding_doc_number,min(tl.ticl_project_id) as ticl_project_id,min(tl.serial_number) as serial_number from ticl_shipment_log_line as tl,ticl_shipment_log as ts,product_category as pc where ts.state='shipped' 
                        and ts.id=tl.ticl_ship_id and pc.name not in ('ATM','XL') and tl.tel_type=pc.id Group By ts.sending_location_id,ts.receiving_location_id,
                        ts.appointment_date_new,tl.condition_id,tl.funding_doc_number,tl.ticl_project_id,tl.funding_doc_type,tl.ticl_ship_id,tl.product_id;""")
                    custom_list = list_0 + list_1 + self.env.cr.fetchall()
                    for c in custom_list:
                        ship_line = self.env['ticl.shipment.log.line'].search([('id','=',c[5])])
                        if ship_line.ship_stock_move_line_id:  
                            if ship_line.ship_stock_move_line_id.received_date not in (None,False,''):
                                c_5 = str(ship_line.ship_stock_move_line_id.received_date.strftime("%Y-%m-%d")).split('-')
                                c5 = '{0}-{1}-{2}'.format(c_5[1],c_5[2],c_5[0])
                        else:
                            if ship_line.receive_date:
                                c_5 = str(ship_line.receive_date.strftime("%Y-%m-%d")).split('-')
                                c5 = '{0}-{1}-{2}'.format(c_5[1],c_5[2],c_5[0])
                            else:
                                c5=''
                        if c[11] != None:
                            c_11 = str(c[11]).split('-')
                            c11 = '{0}-{1}-{2}'.format(c_11[1], c_11[2], c_11[0])
                        else:
                            c[11] =''
                        manufacturer_id = self.env['manufacturer.order'].search([('id','=',c[1])])
                        product_id = self.env['product.product'].search([('id','=',c[2])])
                        if c[0] != '':
                            lot = c[0]
                        else:
                            lot = c[15]
                        sending_location_id = self.env['stock.location'].search([('id', '=', c[6])])
                        receiving_location_id = self.env['res.partner'].search([('id', '=', c[7])])
                        condition_id = self.env['ticl.condition'].search([('id', '=', c[8])])
                        tel_type = self.env['product.category'].search([('id', '=', c[9])])
                        worksheet.write(row, 0, manufacturer_id.name or '')
                        worksheet.write(row, 1, product_id.name or '')
                        worksheet.write(row, 2, lot or '')
                        worksheet.write(row, 3, c[3] or '')
                        worksheet.write(row, 4, c[4].title() or '')
                        worksheet.write(row, 5, c5 or '')
                        worksheet.write(row, 6, sending_location_id.name or '')
                        worksheet.write(row, 7, receiving_location_id.name or '')
                        worksheet.write(row, 8, condition_id.name or '')
                        if (tel_type.name == 'ATM'):
                            worksheet.write(row, 9, 'Unit' or '')
                        else:
                            worksheet.write(row, 9, tel_type.name or '')
                        worksheet.write(row, 10, c[10] or '')
                        worksheet.write(row, 11, c11 or '')
                        worksheet.write(row, 12, c[12] or '')
                        worksheet.write(row, 13, c[13] or '')
                        worksheet.write(row, 14, c[14] or '')
                        # worksheet.write(row, 15, c[15] or '')
                        row += 1
                        
            #Sales Report                    
            if ids.name == "Sales":
                date_split_1 = str(self.from_date).split(" ")
                date_split_2 = str(self.to_date).split(" ")

                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                column_heading_style = easyxf(
                    'font:name Calibri,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('Sales')

                worksheet.write(0, 0, _('Sales ID'), column_heading_style)
                worksheet.write(0, 1, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 2, _('Model'), column_heading_style)
                worksheet.write(0, 3, _('Serial#'), column_heading_style)
                worksheet.write(0, 4, _('Count'), column_heading_style)
                worksheet.write(0, 5, _('Status'), column_heading_style)
                worksheet.write(0, 6, _('Received Date'), column_heading_style)
                worksheet.write(0, 7, _('Location'), column_heading_style)
                worksheet.write(0, 8, _('Condition'), column_heading_style)
                worksheet.write(0, 9, _('Type'), column_heading_style)
                worksheet.write(0, 10, _('Sold Type'), column_heading_style)
                worksheet.write(0, 11, _('Sold Date'), column_heading_style)
                worksheet.write(0, 12, _('Gross'), column_heading_style)
                worksheet.write(0, 13, _('Net'), column_heading_style)
                worksheet.write(0, 14, _('Commission'), column_heading_style)
                worksheet.write(0, 15, _('Check Number'), column_heading_style)

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
                worksheet.col(14).width = 3000
                worksheet.col(15).width = 5000

                row = 1
                for wizard in self:
                    heading = 'Sales'
                    # worksheet.write_merge(0, 0, 0, 8, heading, easyxf(
                    #     'font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
                    custom_list = []
                    loc_ids = []
                    # custom_list.append(('create_date', '>=', date_split_1[0] + ' 00:00:00'))
                    # custom_list.append(('create_date', '<=', date_split_2[0] + ' 23:59:59'))
                    warehouse_ids = self.env['stock.warehouse'].search([])
                    if self.warehouse_ids.ids == []:
                        custom_list.append(('warehouse_id', 'in', self.env['stock.warehouse'].search([]).ids))
                    else:
                        for ids in self.warehouse_ids:
                            loc = self.env['stock.warehouse'].search([('name', '=', ids.name)])
                            loc_ids.append(loc.id)
                        custom_list.append(('warehouse_id', 'in', loc_ids))
                    date_format = xlwt.XFStyle()
                    date_format.num_format_str = 'mm/dd/yy'
                    move_ids = self.env['stock.move.line'].search(custom_list+[('status','=','sold'),('order_from_receipt','=',True)],order='sale_stock_move_id desc')
                    for moves in move_ids:
                        if moves.sale_stock_move_id:
                            picking_id = self.env['stock.picking'].search(
                                [('origin', '=', moves.sale_stock_move_id)], limit=1)
                            so_id = self.env['sale.order'].search([('name', '=', moves.sale_stock_move_id)])
                            so_line_ids = self.env['sale.order.line'].search(
                                [('order_id', '=', so_id.id), ('product_id', '=', moves.product_id.id)], limit=1)
                            if moves.sale_import_data == True:
                                sale_type = moves.sale_type
                                check_number = moves.sale_check_number
                                if moves.sale_date_pick not in (None,False,''):
                                    c_5 = str(moves.sale_date_pick).split(' ')[0].split('-')
                                    c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                else:
                                    c5 = ''
                                sale_date_pick = c5
                                price_subtotal = moves.sale_gross or ''
                                bank_chanrges = moves.sale_net or ''
                                tellerex_charges = moves.sale_commission or ''
                            if moves.sale_import_data == False:
                                check_number = so_id.check_number
                                if picking_id.scheduled_date not in (None,False,''):
                                    c_5 = str(picking_id.scheduled_date).split(' ')[0].split('-')
                                    c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                else:
                                    c5 = ''
                                sale_date_pick = c5
                                if so_id.sale_type == 're-marketing':
                                    sale_type = 'External Sale'
                                if so_id.sale_type == 'disassembly_unit':
                                    sale_type = 'Parts Unit'
                                if so_id.sale_type == 'refurb':
                                    sale_type = 'Refurb'

                                if so_line_ids.product_uom_qty > 1:
                                    price_subtotal = round(so_line_ids.price_subtotal / so_line_ids.product_uom_qty, 2)
                                    bank_chanrges = round(so_line_ids.bank_chanrges / so_line_ids.product_uom_qty, 2)
                                    tellerex_charges = round(so_line_ids.tellerex_charges / so_line_ids.product_uom_qty,
                                                             2)
                                elif so_line_ids.product_uom_qty <= 1:
                                    price_subtotal = so_line_ids.price_subtotal
                                    bank_chanrges = so_line_ids.bank_chanrges
                                    tellerex_charges = so_line_ids.tellerex_charges
                            worksheet.write(row, 0, so_id.name or '')
                            worksheet.write(row, 1, so_line_ids.manufacturer_id.name or '')
                            worksheet.write(row, 2, so_line_ids.product_id.name or '')
                            worksheet.write(row, 3, moves.serial_number or '')
                            worksheet.write(row, 4, 1 or '')
                            worksheet.write(row, 5, 'Sold' or '')
                            if moves.received_date not in (None,False,''):
                                c_5 = str(moves.received_date).split(' ')[0].split('-')
                                c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                            else:
                                c5 = ''
                            worksheet.write(row, 6,c5 or '')
                            worksheet.write(row, 7, moves.warehouse_id.name or '')
                            worksheet.write(row, 8, 'To Recommend' or '')
                            if (so_line_ids.tel_type.name == 'ATM'):
                                worksheet.write(row, 9, 'Unit' or '')
                            else:
                                worksheet.write(row, 9, so_line_ids.tel_type.name or '')
                            worksheet.write(row, 10, sale_type or '')
                            worksheet.write(row, 11, sale_date_pick or '')
                            worksheet.write(row, 12, '$ ' + str(price_subtotal) or '')
                            worksheet.write(row, 13, '$ ' + str(bank_chanrges) or '')
                            worksheet.write(row, 14, '$ ' + str(tellerex_charges) or '')
                            worksheet.write(row, 15, check_number or '')
                            row += 1
                        else:
                            if moves.sale_import_data == True:
                                sale_type = moves.sale_type
                                check_number = moves.sale_check_number
                                # sale_date_pick = moves.sale_date_pick.strftime("%m/%d/%Y") or ''
                                price_subtotal = moves.sale_gross or ''
                                bank_chanrges = moves.sale_net or ''
                                tellerex_charges = moves.sale_commission or ''
                                if moves.sale_old_id:
                                    sale_order = self.env['sale.order'].search([('name', '=', moves.sale_old_id)])
                                worksheet.write(row, 0, moves.sale_old_id or '')
                                worksheet.write(row, 1, moves.manufacturer_id.name or '')
                                worksheet.write(row, 2, moves.product_id.name or '')
                                worksheet.write(row, 3, moves.serial_number or '')
                                worksheet.write(row, 4, 1 or '')
                                worksheet.write(row, 5, 'Sold' or '')
                                if moves.received_date not in (None,False,''):
                                    c_5 = str(moves.received_date).split(' ')[0].split('-')
                                    c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                else:
                                    c5 = ''
                                worksheet.write(row, 6, c5 or '')
                                worksheet.write(row, 7, moves.warehouse_id.name or '')
                                worksheet.write(row, 8, 'To Recommend' or '')
                                if (moves.categ_id.name == 'ATM'):
                                    worksheet.write(row, 9, 'Unit' or '')
                                else:
                                    worksheet.write(row, 9, moves.categ_id.name or '')
                                worksheet.write(row, 10, sale_type or '')
                                if moves.sale_date_pick not in (None,False,''):
                                    c_5 = str(moves.sale_date_pick).split(' ')[0].split('-')
                                    c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                else:
                                    c5 = ''
                                worksheet.write(row, 11, c5 or '')
                                worksheet.write(row, 12, '$ ' + str(price_subtotal) or "")
                                worksheet.write(row, 13, '$ ' + str(bank_chanrges) or "")
                                worksheet.write(row, 14, '$ ' + str(tellerex_charges) or "")
                                worksheet.write(row, 15, check_number or '')
                                row += 1
                    
            if ids.name == "COD":
                date_split_1 = str(self.from_date).split(" ")
                date_split_2 = str(self.to_date).split(" ")
                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                column_heading_style = easyxf(
                    'font:name Calibri,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('COD')

                worksheet.write(0, 0, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 1, _('Model'), column_heading_style)
                worksheet.write(0, 2, _('Serial#'), column_heading_style)
                worksheet.write(0, 3, _('Count'), column_heading_style)
                worksheet.write(0, 4, _('Status'), column_heading_style)
                worksheet.write(0, 5, _('Location'), column_heading_style)
                worksheet.write(0, 6, _('Condition'), column_heading_style)
                worksheet.write(0, 7, _('Type'), column_heading_style)
                worksheet.write(0, 8, _('Technician'), column_heading_style)
                worksheet.write(0, 9, _('Received Date'), column_heading_style)
                worksheet.write(0, 10, _('Date Processed'), column_heading_style)
                worksheet.write(0, 11, _('Duration'), column_heading_style)
                worksheet.write(0, 12, _('COD Comments'), column_heading_style)

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
                worksheet.col(12).width = 7000
                worksheet.col(13).width = 3000
                worksheet.col(14).width = 3000
                worksheet.col(15).width = 3000

                row = 1
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'mm/dd/yy'
                cond_ids = []
                for wizard in self:
                    heading = 'COD'
                    custom_list = []
                    loc_ids = []
                    warehouse_ids = self.env['stock.warehouse'].search([])
                    self._cr.execute("""select * from ticl_condition where name in ('Significant Damage', 'To Recommend', 'Refurb Required','Refurb Required - L1','Refurb Required - L2');""")
                    condition = self._cr.dictfetchall()
                    for ids in condition:
                        cond_ids.append(ids['id'])
                    custom_list.append(('condition_id', 'in', cond_ids))
                    custom_list.append(('state', 'in', ('wrapped', 'done')))
                    custom_list.append(('tel_cod', '=', 'Y'))
                    self._cr.execute("""select * from ticl_receipt_log_summary_line  where state in ('wrapped', 'done') and condition_id in {0} and tel_cod = 'Y' order by CAST(processed_date AS DATE) DESC,CAST(received_date AS DATE) ASC;""".format(tuple(cond_ids)))
                    summary_line_id = self._cr.dictfetchall()
                    for line_ids in summary_line_id:
                        status = self.env['stock.move'].search([('tel_unique_no', '=', line_ids["tel_unique_no"])],limit=1)
                        if status:
                            ids = self.env['ticl.receipt.log.summary.line'].search([('id', '=', line_ids['id'])])
                            if self.warehouse_ids.ids != []:
                                if ids.ticl_receipt_summary_id.receiving_location_id.id in self.warehouse_ids.ids:
                                    worksheet.write(row, 0, ids.manufacturer_id.name or '')
                                    worksheet.write(row, 1, ids.product_id.name or '')
                                    worksheet.write(row, 2, ids.serial_number or '')
                                    worksheet.write(row, 3, ids.count_number or '')
                                    worksheet.write(row, 4, status.status.title() or '')
                                    worksheet.write(row, 5,
                                                    ids.ticl_receipt_summary_id.receiving_location_id.name or '')
                                    worksheet.write(row, 6, ids.condition_id.name or '')
                                    if(ids.tel_type.name == 'ATM'):
                                        worksheet.write(row, 7, 'Unit' or '')
                                    else:
                                        worksheet.write(row, 7, ids.tel_type.name or '')
                                    worksheet.write(row, 8, ids.cod_employee_id.name or '')
                                    if status.received_date not in (None,False,''):
                                        c_5 = str(status.received_date).split(' ')[0].split('-')
                                        c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                    else:
                                        c5 = ''
                                    worksheet.write(row, 9, c5 or '')
                                    if status.processed_date != False:
                                        if status.processed_date not in (None,False,''):
                                            c_5 = str(status.processed_date).split(' ')[0].split('-')
                                            c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                        else:
                                            c5 = ''
                                        worksheet.write(row, 10, c5 or '')
                                    if status.processed_date != False:
                                        received_date = str(status.received_date)
                                        processed_date = str(status.processed_date)
                                        rec_date = received_date.split("-")
                                        proc_date = processed_date.split("-")
                                        rec_date[2] = rec_date[2].split(" ")
                                        proc_date[2] = proc_date[2].split(" ")
                                        f_date = date(int(rec_date[0]), int(rec_date[1]), int(rec_date[2][0]))
                                        l_date = date(int(proc_date[0]), int(proc_date[1]), int(proc_date[2][0]))
                                        daygenerator = (f_date + timedelta(x + 1) for x in range((l_date - f_date).days))
                                        days = sum(1 for day in daygenerator if day.weekday() < 5)
                                        # if days > 0:
                                        #     days = days -1
                                        delta = days
                                        worksheet.write(row, 11, delta or 0)
                                    worksheet.write(row, 12, ids.cod_comments or '')
                            else:
                                worksheet.write(row, 0, ids.manufacturer_id.name or '')
                                worksheet.write(row, 1, ids.product_id.name or '')
                                worksheet.write(row, 2, ids.serial_number or '')
                                worksheet.write(row, 3, ids.count_number or '')
                                worksheet.write(row, 4, status.status.title() or '')
                                worksheet.write(row, 5, ids.ticl_receipt_summary_id.receiving_location_id.name or '')
                                worksheet.write(row, 6, ids.condition_id.name or '')
                                if (ids.tel_type.name == 'ATM'):
                                    worksheet.write(row, 7, 'Unit' or '')
                                else:
                                    worksheet.write(row, 7, ids.tel_type.name or '')
                                worksheet.write(row, 8, ids.cod_employee_id.name or '')
                                if status.received_date not in (None,False,''):
                                    c_5 = str(status.received_date).split(' ')[0].split('-')
                                    c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                else:
                                    c5 = ''
                                worksheet.write(row, 9, c5 or '')
                                if status.processed_date != False:
                                    if status.processed_date not in (None,False,''):
                                        c_5 = str(status.processed_date).split(' ')[0].split('-')
                                        c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                                    else:
                                        c5 = ''
                                    worksheet.write(row, 10, c5 or '')
                                if status.processed_date != False:
                                    received_date = str(status.received_date)
                                    processed_date = str(status.processed_date)
                                    rec_date = received_date.split("-")
                                    proc_date = processed_date.split("-")
                                    rec_date[2] = rec_date[2].split(" ")
                                    proc_date[2] = proc_date[2].split(" ")
                                    f_date = date(int(rec_date[0]), int(rec_date[1]), int(rec_date[2][0]))
                                    l_date = date(int(proc_date[0]), int(proc_date[1]), int(proc_date[2][0]))
                                    daygenerator = (f_date + timedelta(x + 1) for x in range((l_date - f_date).days))
                                    days = sum(1 for day in daygenerator if day.weekday() < 5)
                                    # if days > 0:
                                    #     days = days -1
                                    delta = days
                                    worksheet.write(row, 11, delta or 0)
                                worksheet.write(row, 12, ids.cod_comments or '')
                            row += 1

            if ids.name == "Recycled":
                column_heading_style = easyxf(
                    'font:name Calibri,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
                worksheet = workbook.add_sheet('Recycled')
                worksheet.write(0, 0, _('Manufacturer'), column_heading_style)
                worksheet.write(0, 1, _('Model'), column_heading_style)
                worksheet.write(0, 2, _('Serial #'), column_heading_style)
                worksheet.write(0, 3, _('Count'), column_heading_style)
                worksheet.write(0, 4, _('Status'), column_heading_style)
                worksheet.write(0, 5, _('Received Date'), column_heading_style)
                worksheet.write(0, 6, _('Location'), column_heading_style)
                worksheet.write(0, 7, _('Condition'), column_heading_style)
                worksheet.write(0, 8, _('Type'), column_heading_style)
                worksheet.write(0, 9, _('Recycled Date'), column_heading_style)
                worksheet.write(0, 10, _('COD'), column_heading_style)
                worksheet.write(0, 11, _('Scrap Comments'), column_heading_style)

                worksheet.col(0).width = 5000
                worksheet.col(1).width = 5000
                worksheet.col(2).width = 3000
                worksheet.col(3).width = 3000
                worksheet.col(4).width = 4500
                worksheet.col(5).width = 5000
                worksheet.col(6).width = 10000
                worksheet.col(7).width = 6000
                worksheet.col(8).width = 5000
                worksheet.col(9).width = 5000
                worksheet.col(10).width = 3000
                worksheet.col(11).width = 10000

                row = 1
                date_format = xlwt.XFStyle()
                date_format.num_format_str = 'mm/dd/yy'
                for wizard in self:
                    self._cr.execute("""select * from stock_move_line  where status in ('recycled') order by CAST(recycled_date AS DATE) DESC,CAST(processed_date AS DATE) ASC;""")
                    recycle_objs = self._cr.dictfetchall()
                    for line_ids in recycle_objs:
                        ids = self.env['stock.move.line'].search([('id', '=', line_ids['id'])])
                        if ids.processed_date:
                            if ids.processed_date not in (None,False,''):
                                c_5 = str(ids.processed_date).split(' ')[0].split('-')
                                c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                            else:
                                c5 = ''
                            pd_date = c5
                        else:
                            pd_date = ''
                        if ids.recycled_date:
                            if ids.recycled_date not in (None,False,''):
                                c_5 = str(ids.recycled_date).split(' ')[0].split('-')
                                c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                            else:
                                c5 = ''
                            rd_date = c5
                        else:
                            rd_date = ''
                        worksheet.write(row, 0, ids.manufacturer_id.name or '')
                        worksheet.write(row, 1, ids.product_id.name or '')
                        worksheet.write(row, 2, ids.serial_number or '')
                        worksheet.write(row, 3, 1 or '')
                        worksheet.write(row, 4, 'Recycled' or '')
                        if ids.received_date not in (None,False,''):
                            c_5 = str(ids.received_date).split(' ')[0].split('-')
                            c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
                        else:
                            c5 = ''
                        worksheet.write(row, 5, c5 or '')
                        worksheet.write(row, 6, ids.location_dest_id.name or '')
                        worksheet.write(row, 7, ids.condition_id.name or '')
                        if ids.categ_id.name == "ATM":
                            worksheet.write(row, 8, "Unit" or '')
                        else:
                            worksheet.write(row, 8, ids.categ_id.name or '')
                        worksheet.write(row, 9, rd_date or '')
                        worksheet.write(row, 10, pd_date or '')
                        worksheet.write(row, 11, ids.scrap_tel_note or '')
                        row += 1



        fp = io.BytesIO()
        workbook.save(fp)
        excel_file = base64.encodestring(fp.getvalue())

        # xl = vals.get('file').split(',')
        # xlsx_file = excel_file.encode()
        excel_file = base64.decodestring(excel_file)
        book = xlrd.open_workbook(file_contents=excel_file, formatting_info=True)
        # book = open_workbook(self.chase_summary_file.decode('utf-8'), formatting_info=True)
        wbk = xlwt.Workbook()
        for i in range(len(book.sheets())):
            sheet = book.sheets()[i]
            if sheet.name == "Inventory Detail Report":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: x[7])
                data.sort(key=lambda x: x[8])
                data.sort(key=lambda x: x[1])
                data.sort(key=lambda x: x[0].lower())
                data.sort(key=lambda x: x[9], reverse=True)
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 5000
                sheet.col(1).width = 6000
                sheet.col(2).width = 4000
                sheet.col(3).width = 2000
                sheet.col(4).width = 3300
                sheet.col(5).width = 3500
                sheet.col(6).width = 9000
                sheet.col(7).width = 5500
                sheet.col(8).width = 5000
                sheet.col(9).width = 2500
                sheet.col(10).width = 10000

                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')
                final_style3 = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')

                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 3:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        elif idx_c == 5:
                            if value != '':
                                v = value.split('-')
                                x = r_datetime.datetime(int(v[2]), int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), final_style3)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style3)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)

            if sheet.name == "Received":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: x[7])
                data.sort(key=lambda x: x[8])
                data.sort(key=lambda x: x[1])
                data.sort(key=lambda x: x[0].lower())
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 5000
                sheet.col(1).width = 6000
                sheet.col(2).width = 4000
                sheet.col(3).width = 2000
                sheet.col(4).width = 3300
                sheet.col(5).width = 4000
                sheet.col(6).width = 9000
                sheet.col(7).width = 5500
                sheet.col(8).width = 4000
                sheet.col(9).width = 2500
                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')
                final_style3 = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')

                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 3:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        elif idx_c == 5:
                            if value != '':
                                v = value.split('-')
                                x = r_datetime.datetime(int(v[2]), int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), final_style3)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style3)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)

            if sheet.name == "Shipped":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: x[1])
                data.sort(key=lambda x: x[0].lower())
                data.sort(key=lambda x: x[14])
                data.sort(key=lambda x: x[6])
                data.sort(key=lambda x: x[7])
                # data.sort(key = lambda x: datetime.strptime(x[11], "%m-%d-%y"), reverse=True)
                data.sort(key=lambda x: x[11], reverse=True)

                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 5000
                sheet.col(1).width = 6000
                sheet.col(2).width = 4000
                sheet.col(3).width = 2000
                sheet.col(4).width = 3000
                sheet.col(5).width = 4000
                sheet.col(6).width = 5500
                sheet.col(7).width = 9000
                sheet.col(8).width = 4000
                sheet.col(9).width = 2500
                sheet.col(10).width = 3500
                sheet.col(11).width = 3500
                sheet.col(12).width = 4500
                sheet.col(13).width = 5000
                sheet.col(14).width = 3500
                sheet.col(15).width = 8000

                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')
                final_style3 = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')

                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 3:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        elif idx_c == 5 or idx_c == 11:
                            if value!='':
                                v= value.split('-')
                                x=r_datetime.datetime(int(v[2]),int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), final_style3)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style3)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)

            if sheet.name == "Inventory Summary":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: x[6])
                data.sort(key=lambda x: x[5])
                data.sort(key=lambda x: x[2])
                data.sort(key=lambda x: x[1].lower())
                data.sort(key=lambda x: x[0])
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 5500
                sheet.col(1).width = 5000
                sheet.col(2).width = 6000
                sheet.col(3).width = 2000
                sheet.col(4).width = 3300
                sheet.col(5).width = 5000
                sheet.col(6).width = 2500
                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')

                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 3:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)

            if sheet.name == "Sales":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: x[2])
                data.sort(key=lambda x: x[1].lower())
                data.sort(key=lambda x: x[0])
                # data.sort(key=lambda x: datetime.strptime(x[11], "%m-%d-%y"), reverse=True)
                data.sort(key=lambda x: x[11], reverse=True)
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 3000
                sheet.col(1).width = 5000
                sheet.col(2).width = 6000
                sheet.col(3).width = 4000
                sheet.col(4).width = 2000
                sheet.col(5).width = 3000
                sheet.col(6).width = 4000
                sheet.col(7).width = 5500
                sheet.col(8).width = 3700
                sheet.col(9).width = 2500
                sheet.col(10).width = 3500
                sheet.col(11).width = 3500
                sheet.col(12).width = 3500
                sheet.col(13).width = 2500
                sheet.col(14).width = 3200
                sheet.col(15).width = 3500
                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')
                final_style3 = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')
                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 4:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        elif idx_c == 6 or idx_c == 11:
                            if value != '':
                                v = value.split('-')
                                x = r_datetime.datetime(int(v[2]), int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), final_style3)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style3)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)

            if sheet.name == "COD":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 5000
                sheet.col(1).width = 5500
                sheet.col(2).width = 4000
                sheet.col(3).width = 2000
                sheet.col(4).width = 3000
                sheet.col(5).width = 5500
                sheet.col(6).width = 5000
                sheet.col(7).width = 2500
                sheet.col(8).width = 4000
                sheet.col(9).width = 4000
                sheet.col(10).width = 4000
                sheet.col(11).width = 2500
                sheet.col(12).width = 10000

                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')
                final_style3 = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')

                style = easyxf('font: name Calibri, bold True, color red')
                style1 = easyxf('font: name Calibri, bold True, color green')

                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 11:
                            if value != '' and (int(value) > 5):
                                sheet.write(idx_r + 1, idx_c, value, style)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, style1)

                        elif idx_c == 3:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        elif idx_c == 9 or idx_c == 10:
                            if value != '':
                                v = value.split('-')
                                x = r_datetime.datetime(int(v[2]), int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), final_style3)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style3)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)

            if sheet.name == "Recycled":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 5000
                sheet.col(1).width = 6000
                sheet.col(2).width = 4000
                sheet.col(3).width = 2000
                sheet.col(4).width = 3000
                sheet.col(5).width = 4000
                sheet.col(6).width = 5500
                sheet.col(7).width = 4000
                sheet.col(8).width = 2500
                sheet.col(9).width = 4000
                sheet.col(10).width = 3000
                sheet.col(11).width = 10000
                final_style1 = easyxf('font: name Calibri; align: horiz right, wrap yes')
                final_style2 = easyxf('font: name Calibri; align: horiz left, wrap yes')
                final_style3 = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')

                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 3:
                            if value != '':
                                sheet.write(idx_r + 1, idx_c, value, final_style1)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style2)
                        elif idx_c == 5 or idx_c == 9 or idx_c == 10:
                            if value != '':
                                v = value.split('-')
                                x = r_datetime.datetime(int(v[2]), int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), final_style3)
                            else:
                                sheet.write(idx_r + 1, idx_c, value, final_style3)
                        else:
                            sheet.write(idx_r + 1, idx_c, value, final_style2)
        fp = io.BytesIO()
        wbk.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        self.chase_summary_file = excel_file
        self.file_name = 'Chase Weekly Report'
        fp.close()
        self.from_date = ''
        self.to_date = ''
        # self.report_type = ''
        rec = {
            'type': 'ir.actions.act_url',
            'name': 'Chase Weekly Report',
            'url': '/web/content/ticl.chase.weekly.report/%s/chase_summary_file/%s.xls?download=true' % (
                self.id, self.file_name)
        }
        return rec
