# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
import datetime

class PrintInventorySummary(models.TransientModel):
    _name = "print.inventory.summary"

    
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    inventory_summary_file = fields.Binary('Excel Report')
    file_name = fields.Char('File Name')
    inventory_report_printed = fields.Boolean('Excel Report')
    inventory_status = fields.Selection([('inventory', 'Inventory'),('shipped', 'Shipped'),('recycled','Recycled')], string='Status')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Location')
    location_ids = fields.Many2many('stock.location', string='Location')

    
    @api.multi
    def action_print_inventory_summary(self):
        new_from_date = self.from_date.strftime('%Y-%m-%d')
        new_to_date = self.to_date.strftime('%Y-%m-%d')
        workbook = xlwt.Workbook()
        amount_tot = 0
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('Inventory Report')

       # worksheet.write(2, 3, self.env.user.company_id.name, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 5, new_from_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 6, 'To',easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 7, new_to_date,easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(3, 0, _('Manufacturer'), column_heading_style) 
        worksheet.write(3, 1, _('Model'), column_heading_style)
        worksheet.write(3, 2, _('Part#'), column_heading_style)
        worksheet.write(3, 3, _('Serial#'), column_heading_style)
        worksheet.write(3, 4, _('Count'), column_heading_style)
        worksheet.write(3, 5, _('Status'), column_heading_style)
        worksheet.write(3, 6, _('Received Date'), column_heading_style)
        worksheet.write(3, 7, _('Funding Doc Type'), column_heading_style)
        worksheet.write(3, 8, _('Funding Doc Number'), column_heading_style)
        worksheet.write(3, 9, _('Project Id'), column_heading_style)
        worksheet.write(3, 10, _('Location'), column_heading_style)
        worksheet.write(3, 11, _('Condition'), column_heading_style)
        worksheet.write(3, 12, _('Type'), column_heading_style)
        
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 3000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 2000
        worksheet.col(5).width = 3000 
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 3000
        worksheet.col(10).width = 5000
        worksheet.col(11).width = 3000
        worksheet.col(12).width = 5000
        worksheet.col(13).width = 3000
        
       # worksheet2 = workbook.add_sheet('Inventory Report')
        row = 4
        for wizard in self:
            heading =  'Inventory Report'
            worksheet.write_merge(0, 0, 0, 12, heading, easyxf('font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
           # heading =  'Inventory Report'
           # worksheet2.write_merge(0, 0, 0, 8, heading, easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
            inventory_objs = self.env['ticl.order.line'].search([('ticl_order_id.receive_date','>=',wizard.from_date),
                                                               ('ticl_order_id.receive_date','<=',wizard.to_date)])
            print("----inventory_objs----",inventory_objs)               
            for inventory in inventory_objs:
                #receive_date = datetime.datetime.strptime('ticl_order_id.receive_date', '%m/%d/%Y')
                #print("-----receive_date------",receive_date)

                worksheet.write(row, 0, inventory.manufacturer_id.name or '')
                worksheet.write(row, 1, inventory.product_id.name or '')
                worksheet.write(row, 2, inventory.product_id.part_name or '')
                worksheet.write(row, 3, str(inventory.serial_number) or '')
                worksheet.write(row, 4, str(inventory.count_number) or '')
                worksheet.write(row, 5, inventory.ticl_order_id.states or '')
                worksheet.write(row, 6, str(inventory.ticl_order_id.receive_date) or '')
                worksheet.write(row, 7, str(inventory.fund_doc_type) or '')
                worksheet.write(row, 8, str(inventory.fund_doc_number) or '')
                worksheet.write(row, 9, str(inventory.ticl_project_id) or '')
                worksheet.write(row, 10, inventory.ticl_order_id.warehouse_id.name or '')
                worksheet.write(row, 11, inventory.ticl_order_id.condition_id.name or '')
                worksheet.write(row, 12, inventory.categ_id.name or '')
                row += 1
                       
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.inventory_summary_file = excel_file
            wizard.file_name = str(wizard.from_date)+'_'+'Inventory Report.xls'
            wizard.inventory_report_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'print.inventory.summary',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                       }



    @api.multi
    def action_print_shipped_report(self):
        new_from_date = self.from_date.strftime('%Y-%m-%d')
        new_to_date = self.to_date.strftime('%Y-%m-%d')
        workbook = xlwt.Workbook()
        amount_tot = 0
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('Shipped Report')

       # worksheet.write(2, 3, self.env.user.company_id.name, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 5, new_from_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 6, 'To',easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 7, new_to_date,easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(3, 0, _('Type'), column_heading_style)
        worksheet.write(3, 1, _('Manufacturer'), column_heading_style) 
        worksheet.write(3, 2, _('Part'), column_heading_style) 
        worksheet.write(3, 3, _('Serial'), column_heading_style) 
        worksheet.write(3, 4, _('Count'), column_heading_style) 
        worksheet.write(3, 5, _('Status'), column_heading_style) 
        worksheet.write(3, 6, _('Receive Date'), column_heading_style) 
        worksheet.write(3, 7, _('Funding Doc Type'), column_heading_style) 
        worksheet.write(3, 8, _('Funding Doc Number'), column_heading_style) 
        worksheet.write(3, 9, _('Project Id'), column_heading_style) 
        worksheet.write(3, 10, _('Location'), column_heading_style)
        worksheet.write(3, 11, _('Shipped Date'), column_heading_style)
        worksheet.write(3, 12, _('Destination'), column_heading_style)
        worksheet.write(3, 13, _('Condition'), column_heading_style)
        
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 3000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 2000
        worksheet.col(5).width = 3000 
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 3000
        worksheet.col(10).width = 5000
        worksheet.col(11).width = 3000
        worksheet.col(12).width = 5000
        worksheet.col(13).width = 3000

        row = 4
        for wizard in self:
            heading =  'Shipped Report'
            worksheet.write_merge(0, 0, 0, 12, heading, easyxf('font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
            inventory_objs = self.env['stock.move'].search([('shipped_date','>=',wizard.from_date),
                                                               ('shipped_date','<=',wizard.to_date),
                                                               ('states','=',wizard.inventory_status),
                                                               ('warehouse_id','=',wizard.warehouse_ids.ids),
                                                               ])
            print("----inventory_objs----",inventory_objs)               
            for inventory in inventory_objs:
                worksheet.write(row, 0, inventory.categ_id.name or '')
                worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                worksheet.write(row, 2, inventory.product_id.name or '')
                worksheet.write(row, 3, inventory.serial_number or '')
                worksheet.write(row, 4, inventory.count_number or '')
                worksheet.write(row, 5, inventory.states or '')
                worksheet.write(row, 6, str(inventory.receive_date) or '')
                worksheet.write(row, 7, inventory.fund_doc_type or '')
                worksheet.write(row, 8, inventory.fund_doc_number or '')
                worksheet.write(row, 9, inventory.ticl_project_id or '')
                worksheet.write(row, 10, inventory.warehouse_id.name or '')
                worksheet.write(row, 11, str(inventory.shipped_date) or '')
                worksheet.write(row, 12, inventory.location_dest_id.name or '')
                worksheet.write(row, 13, inventory.condition_id.name or '')
                row += 1           
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.inventory_summary_file = excel_file
            wizard.file_name = str(wizard.from_date)+'_'+'Inventory Shipped Report.xls'
            wizard.inventory_report_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'print.inventory.summary',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                       }


# Recycled Report
    @api.multi
    def action_print_recycled_report(self):
        new_from_date = self.from_date.strftime('%Y-%m-%d')
        new_to_date = self.to_date.strftime('%Y-%m-%d')
        workbook = xlwt.Workbook()
        amount_tot = 0
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('Chase Recycled Report')

       # worksheet.write(2, 3, self.env.user.company_id.name, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 5, new_from_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 6, 'To',easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 7, new_to_date,easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(3, 0, _('Type'), column_heading_style)
        worksheet.write(3, 1, _('Manufacturer'), column_heading_style) 
        worksheet.write(3, 2, _('Model'), column_heading_style) 
        worksheet.write(3, 3, _('Serial'), column_heading_style) 
        worksheet.write(3, 4, _('Count'), column_heading_style) 
        worksheet.write(3, 5, _('Status'), column_heading_style) 
        worksheet.write(3, 6, _('Receive Date'), column_heading_style) 
        worksheet.write(3, 7, _('Recycled Date'), column_heading_style) 
        worksheet.write(3, 8, _('Location'), column_heading_style) 

        
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 3000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 2000
        worksheet.col(5).width = 3000 
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000

        row = 4
        for wizard in self:
            heading =  'Chase Recycled Report'
            worksheet.write_merge(0, 0, 0, 12, heading, easyxf('font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
            inventory_objs = self.env['stock.move'].search([('shipped_date','>=',wizard.from_date),
                                                               ('shipped_date','<=',wizard.to_date),
                                                               ('states','=',wizard.inventory_status),
                                                               ('warehouse_id','=',wizard.warehouse_ids.ids),
                                                               ])
            print("----inventory_objs----",inventory_objs)               
            for inventory in inventory_objs:
               # receive_date = invoice.ticl_order_id.receive_date.strftime('%Y-%m-%d')
                #print("-----receive_date------",receive_date)

                worksheet.write(row, 0, inventory.categ_id.name or '')
                worksheet.write(row, 1, inventory.manufacturer_id.name or '')
                worksheet.write(row, 2, inventory.product_id.name or '')
                worksheet.write(row, 3, inventory.serial_number or '')
                worksheet.write(row, 4, inventory.count_number or '')
                worksheet.write(row, 5, inventory.states or '')
                worksheet.write(row, 6, str(inventory.receive_date) or '')
                worksheet.write(row, 7, str(inventory.recycled_date) or '')
                worksheet.write(row, 8, inventory.fund_doc_number or '')

                row += 1           
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.inventory_summary_file = excel_file
            wizard.file_name = str(wizard.from_date)+'_'+'Inventory Recycled Report.xls'
            wizard.inventory_report_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'print.inventory.summary',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                       }
