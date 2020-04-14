# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ticl_order(models.Model):
    _name = 'ticl.order'
    _description = "Work Order"
    _order = 'receive_date desc, id desc'

    # @api.model
    # def create(self, vals):
    #     seq = self.env['ir.sequence'].next_by_code('ticl.order') or '/'
    #     vals['name'] = seq
    #     return super(ticl_order, self).create(vals)


    name = fields.Char(string="Work Order")
    receive_date = fields.Datetime(string="Received Date")
#    menufacrur_id = fields.Many2one('menufacrur.order', string="Menufactrur")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',)
    location_dest_id = fields.Many2one('stock.location', 'Products Location')
    ticl_order_lines = fields.One2many('ticl.order.line', 'ticl_order_id', ondelete='cascade')
    states = fields.Selection([('draft', 'Draft'),('inventory', 'Inventory')], string='Status', default="draft")
    stock_move_count = fields.Integer('Stock Move', compute="stock_move_total_count")
    stock_transfer_count = fields.Integer('Transfer', compute="transfer_total_count")
    user_id = fields.Many2one('res.users', string='Responsible Persons', default=lambda self: self.env.user)
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    


    def stock_move_total_count(self):
        stock_move_ids = self.env['stock.move'].search([('ticl_order_id', '=', self.id)])
        self.stock_move_count = len(stock_move_ids)

    def transfer_total_count(self):
        transfer_ids = self.env['stock.picking'].search([('ticl_order_id', '=', self.id)])
        self.stock_transfer_count = len(transfer_ids)
    
#     @api.multi
    def view_stock_move(self):
        action = {
            'name': _('Stock Moves(s)'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'target': 'current',
        }
        stock_move_ids = self.env['stock.move'].search([('ticl_order_id', '=', self.id)])
        if len(stock_move_ids) == 1:
            action['res_id'] = stock_move_ids.ids[0]
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', stock_move_ids.ids)]
        return action


#     @api.multi
    def view_stock_transfer(self):
        action = {
            'name': _('Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'target': 'current',
        }
        stock_transfer_ids = self.env['stock.picking'].search([('ticl_order_id', '=', self.id)])
        if len(stock_transfer_ids) == 1:
            action['res_id'] = stock_transfer_ids.ids[0]
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', stock_transfer_ids.ids)]
        return action


    def confirm_order(self):
        source_location_id = self.env['stock.location'].search([('location_id.name','=', self.warehouse_id.code)],limit=1)
        stock_picking_type_id = self.env['stock.picking.type'].search([('warehouse_id','=', self.warehouse_id.id), ('code','=', 'internal')],limit=1)
        vals = {
            'picking_type_id' : stock_picking_type_id.id,
            'scheduled_date': self.receive_date,
            'location_id': source_location_id.id, 
            'location_dest_id': self.location_dest_id.id, 
            'ticl_order_id': self.id,
            'condition_id': self.condition_id.id, 

        }
        picking_id = self.env['stock.picking'].create(vals)        

        for ticl_line in self.ticl_order_lines:
            move_ids_without_package = {
                'name' : ticl_line.product_id.name,
                'product_id' : ticl_line.product_id.id,
                'product_uom_qty': ticl_line.product_uom_qty, 
                'product_uom': ticl_line.product_id.uom_id.id,
                'location_id': source_location_id.id, 
                'location_dest_id': self.location_dest_id.id,  
                'ticl_order_id': self.id, 
            }
            picking_id.move_ids_without_package = [(0, 0, move_ids_without_package)]
        #self.states = 'inventory'

    # def confirm_shipped(self):
    #     self.states = 'shipped'




class ticl_order_line(models.Model):
    _name = 'ticl.order.line'
    _description = "Work Order Line"

    @api.onchange('product_id', 'product_function','part_name','oem_pm','product_lenght','product_width','product_height',
        'weight','product_squre_feet','categ_id','manufacturer_id','condition_id')
    def onchange_product_id(self):
        self.part_name = self.product_id.part_name
        self.oem_pm = self.product_id.oem_pm
        self.product_function = self.product_id.product_function
        self.product_lenght = self.product_id.product_lenght
        self.product_width = self.product_id.product_width
        self.product_height = self.product_id.product_height
        self.weight = self.product_id.weight
        self.product_squre_feet = self.product_id.product_squre_feet
        self.categ_id = self.product_id.categ_id.id or False
        self.manufacturer_id = self.product_id.manufacturer_id.id
        self.condition_id = self.product_id.condition_id.id or False


    ticl_order_id = fields.Many2one('ticl.order', invisible=1)
    product_id = fields.Many2one('product.product', string='Chase Model Name', required=1)
    part_name = fields.Char(string="Version Number")
    serial_number = fields.Char(string = "Serial Number")
    oem_pn = fields.Char(string = "OEM PN")
    product_function = fields.Char(string = "Function")
    product_uom_qty = fields.Float(string = "QTY" , default=1.0)
    product_lenght = fields.Float(string = "Length")
    product_width = fields.Float(string = "Width")
    product_height = fields.Float(string = "Height")
    weight = fields.Float(string = "Weight")
    product_squre_feet = fields.Float(string = "Square Feet")
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    categ_id = fields.Many2one('product.category', string="Type")
    funding_type_id = fields.Many2one('fund.doc.type', string = "Funding Doc Type")
    count_number = fields.Char(string = "Count")
    fund_doc_type = fields.Char(string = "Funding Doc Type")
    fund_doc_number = fields.Char(string = "Funding Doc Number")
    ticl_project_id = fields.Char(string = "Project Id")

