import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning
import threading
import urllib3
import json
import requests
import logging

_logger = logging.getLogger(__name__)

class ticl_shipment(models.Model):
    _name = 'ticl.shipment'
    _inherit = ['mail.thread']
    _description = "TICL Shipment"

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ticl.shipment') or 'New'
        if 'ticl_shipment_lines' not in vals.keys():
            raise UserError('Please add line items')
        for i in range(len(vals['ticl_shipment_lines'])):
            move_id = self.env['stock.move']
            inv_check = move_id.search(
                [('categ_id', '=', vals['ticl_shipment_lines'][i][2]['tel_type']), ('product_id', '=', vals['ticl_shipment_lines'][i][2]['product_id']),
                 ('status', '=', 'inventory')])
            inv_d_check = move_id.search_count(
                [('categ_id', '=', vals['ticl_shipment_lines'][i][2]['tel_type']),
                 ('product_id', '=', vals['ticl_shipment_lines'][i][2]['product_id']),
                 ('status', '=', 'inventory')])

            if len(inv_check.ids) <= 0:
                product_id = self.env['product.product'].search(
                    [('id', '=', int(vals['ticl_shipment_lines'][i][2]['product_id']))])
                print('\n\n prod name',int(vals['ticl_shipment_lines'][i][2]['product_id']),product_id)
                raise UserError('Insufficient Items:{0} in the Inventory'.format(product_id.name))

            vals['ticl_shipment_lines'][i][2]['stock_move_id'] = inv_check[0].id
            vals['ticl_shipment_lines'][i][2]['ticl_unique_no'] = inv_check[0].tel_unique_no
            vals['ticl_shipment_lines'][i][2]['condition_id'] = inv_check[0].condition_id.id
            move_id.search([('id', '=', inv_check[0].id)]).write({'status': 'picked', 'add_pallet': vals['name']})
        result = super(ticl_shipment, self).create(vals)
        return result

    @api.model
    def write(self, values):
        if 'state' not in values.keys():
            for i in range(len(self.ticl_shipment_lines),len(values['ticl_shipment_lines'])):
                move_id = self.env['stock.move']
                inv_check = move_id.search(
                    [('categ_id', '=', values['ticl_shipment_lines'][i][2]['tel_type']), ('product_id', '=', values['ticl_shipment_lines'][i][2]['product_id']),
                     ('status', '=', 'inventory')])
                if len(inv_check.ids) <= 0:
                    product_id = self.env['product.product'].search(
                        [('id', '=', int(values['ticl_shipment_lines'][i][2]['product_id']))])
                    print('\n\n prod name', int(values['ticl_shipment_lines'][i][2]['product_id']), product_id)
                    raise UserError('Insufficient Items:{0} in the Inventory'.format(product_id.name))

                if len(inv_check) <= 1:
                    values['ticl_shipment_lines'][i][2]['stock_move_id'] = inv_check.id
                    values['ticl_shipment_lines'][i][2]['ticl_unique_no'] = inv_check.tel_unique_no
                    values['ticl_shipment_lines'][i][2]['condition_id'] = inv_check.condition_id.id
                    move_id.search([('id', '=', inv_check.id)]).write({'status': 'picked', 'add_pallet': self.name})
                else:
                    values['ticl_shipment_lines'][i][2]['stock_move_id'] = inv_check[0].id
                    values['ticl_shipment_lines'][i][2]['ticl_unique_no'] = inv_check[0].tel_unique_no
                    values['ticl_shipment_lines'][i][2]['condition_id'] = inv_check[0].condition_id.id
                    move_id.search([('id', '=', inv_check[0].id)]).write({'status': 'picked', 'add_pallet': self.name})

        return super(ticl_shipment, self).write(values)

    name = fields.Char(string='Shipment Number', index=True )
    # tel_note = fields.Char(string='Comment/Note')
    create_date = fields.Datetime('Create Date',default=datetime.now())
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_ship_log','In Shipping Log'),
        ],
        string='Status', default='draft',track_visibility='onchange')

    ticl_shipment_lines = fields.One2many('ticl.shipment.line', 'ticl_shipment_id', ondelete='cascade',track_visibility='onchange')


class ticl_shipment_log_line(models.Model):
    _name = 'ticl.shipment.line'
    _inherit = ['mail.thread']
    _description = "Shipping Line"

    name = fields.Text(string='Description')
    shipment_date = fields.Datetime(string='Shipment Date', default=datetime.today())
    ticl_shipment_id = fields.Many2one('ticl.shipment', string='Shipment ID', invisible=1)
    product_id = fields.Many2one('product.product', string='Model Name',track_visibility='onchange')
    stock_move_id =  fields.Many2one('stock.move',string='Inventory Id',store=True,track_visibility='onchange')
    manufacturer_id = fields.Many2one('manufacturer.order', related = 'product_id.manufacturer_id',string="Manufacturer",readonly=0,track_visibility='onchange')
    count_number = fields.Char(string='Count',default=1,readonly=1)
    condition_id = fields.Many2one('ticl.condition', string="Condition",track_visibility='onchange')
    tel_type = fields.Many2one('product.category', string="Type",track_visibility='onchange')
    tel_note = fields.Char(string='Comment/Note')
    ticl_unique_no = fields.Char(string='Unique Number',track_visibility='onchange')
    product_weight = fields.Char(string="Product Weight")

    @api.onchange('product_id')
    def on_change_product_id(self):
        if self.product_id:
            self.product_weight = self.product_id.product_weight

    @api.onchange('tel_type')
    def on_change_type(self):
        if self.tel_type:
            inv_check =  self.env['stock.move'].search([('categ_id','=',self.tel_type.id),('status','=','inventory')])
            products = []
            for ids in inv_check:
                products.append(ids.product_id.id)
            return {'domain': {'product_id': [('id', 'in', list(set(products)))]}}

    @api.model
    def unlink(self):
        for ids in self:
            self.env['stock.move'].search([('id','=',ids.stock_move_id.id)]).write({'status': 'inventory','add_pallet' : False})
        return super(ticl_shipment_log_line, self).unlink()

