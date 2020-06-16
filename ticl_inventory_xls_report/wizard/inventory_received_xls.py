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


class ticlinventoryinbound(models.TransientModel):
    _name = "ticl.inventory.inbound"
    _description = "Inbound Inventory"

    @api.onchange('from_date', 'to_date')
    def onchange_week(self):
        if self.from_date:
            from_date = fields.Date.from_string(self.from_date)
            self.to_date = from_date + datetime.timedelta(weeks=-1)


    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    inventory_summary_file = fields.Binary('Inbound Inventory Report')
    file_name = fields.Char('File Name')
    inventory_report_printed = fields.Boolean('Inbound Inventory Report')
    inventory_status = fields.Selection([('inventory', 'Inventory')], string='Status', default='inventory')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_id = fields.Many2many('stock.location', string='Location Name')

    
    
    #@api.multi
    def action_print_inventory_inbound(self):
        new_from_date = self.from_date.strftime('%Y-%m-%d')
        new_to_date = self.to_date.strftime('%Y-%m-%d')
        workbook = xlwt.Workbook()
        amount_tot = 0
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('Inbound/Received Inventory Report')

       # worksheet.write(2, 3, self.env.user.company_id.name, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 5, new_from_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 6, 'To',easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(1, 7, new_to_date,easyxf('font:height 200;font:bold True;align: horiz center;'))
        worksheet.write(3, 0, _('Manufacturer'), column_heading_style) 
        worksheet.write(3, 1, _('Model'), column_heading_style)
        worksheet.write(3, 2, _('Serial#'), column_heading_style)
        worksheet.write(3, 3, _('Count'), column_heading_style)
        worksheet.write(3, 4, _('Status'), column_heading_style)
        worksheet.write(3, 5, _('Received Date'), column_heading_style)
        worksheet.write(3, 6, _('Funding Doc Type'), column_heading_style)
        worksheet.write(3, 7, _('Funding Doc Number'), column_heading_style)
        worksheet.write(3, 8, _('Project Id'), column_heading_style)
        worksheet.write(3, 9, _('Location'), column_heading_style)
        worksheet.write(3, 10, _('Condition'), column_heading_style)
        worksheet.write(3, 11, _('Type'), column_heading_style)
        
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
            heading =  'Inbound/Received Inventory Report'
            worksheet.write_merge(0, 0, 0, 12, heading, easyxf('font:height 210; align: horiz center;pattern: pattern solid, fore_color yellow; font: color black; font:bold True;' "borders: top thin,bottom thin"))
            
            inventory_objs = self.env['ticl.order.line'].search([('ticl_order_id.receive_date','<=',wizard.from_date),
                                                               ('ticl_order_id.receive_date','>=',wizard.to_date),
                                                               ('ticl_order_id.states','=',wizard.inventory_status),
                                                               ('ticl_order_id.warehouse_id','in',wizard.warehouse_ids.ids)])
            print("----inventory_objs----",inventory_objs)               
            for inventory in inventory_objs:
                #receive_date = datetime.datetime.strptime('ticl_order_id.receive_date', '%m/%d/%Y')
                #print("-----receive_date------",receive_date)

                worksheet.write(row, 0, inventory.manufacturer_id.name or '')
                worksheet.write(row, 1, inventory.product_id.model_name or '')
                worksheet.write(row, 2, inventory.serial_number or '')
                worksheet.write(row, 3, inventory.count_number or ' ')
                worksheet.write(row, 4, inventory.ticl_order_id.states or '')
                worksheet.write(row, 5, str(inventory.ticl_order_id.receive_date) or '')
                worksheet.write(row, 6, inventory.fund_doc_type or '')
                worksheet.write(row, 7, inventory.fund_doc_number or '')
                worksheet.write(row, 8, inventory.ticl_project_id or '')
                worksheet.write(row, 9, inventory.ticl_order_id.warehouse_id.name or '')
                worksheet.write(row, 10, inventory.ticl_order_id.condition_id.name or '')
                worksheet.write(row, 11, inventory.categ_id.name or '')
                row += 1
                       
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.inventory_summary_file = excel_file
            wizard.file_name = str(wizard.from_date)+'_'+'Inbound/Received Inventory Report.xls'
            wizard.inventory_report_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'ticl.inventory.inbound',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                       }
