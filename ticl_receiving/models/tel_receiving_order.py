# -*- coding: utf-8 -*-
import json
import re
import uuid
from functools import partial
from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode
from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
from odoo.tools.misc import formatLang
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons import decimal_precision as dp
import logging
from datetime import datetime


_logger = logging.getLogger(__name__)



class TelReceiving(models.Model):
    _name = 'tel.receiving'
    _inherit = ['mail.thread']
    _description = "Tel Receiving Order"
    _order = "id desc"

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('tel.receiving') or '/'
        vals['name'] = seq
        return super(TelReceiving, self).create(vals)

#Total ATM
    @api.depends('receiving_order_line.count_number')
    def count_total_atm(self):  
        for receving in self:      
            total_atm = 0     
            for line in receving.receiving_order_line:
                if line.tel_type.name == 'ATM':
                    total_atm += int(line.count_number)  
            receving.update({'total_atm': total_atm })

#Total Signage
    @api.depends('receiving_order_line.count_number')
    def count_total_signage(self):  
        for receving in self:      
            total_signage = 0
            for line in receving.receiving_order_line:
                if line.tel_type.name == 'Signage':
                    total_signage += int(line.count_number)  
            receving.update({'total_signage': total_signage })

#Total Accessory
    @api.depends('receiving_order_line.count_number')
    def count_total_accessory(self):  
        for receving in self:      
            total_accessory = 0
            for line in receving.receiving_order_line:
                if line.tel_type.name == 'Accessory':
                    total_accessory += int(line.count_number)  
            receving.update({'total_accessory': total_accessory })


            


    name = fields.Char(string='Receipt', index=True)
    tel_note = fields.Text(string='Note')
    asn_received_date = fields.Date(string='Received Date')
    expected_delivery_date = fields.Date(string='Delivery Date', default=datetime.date(datetime.now()))
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)')
    sending_location_id = fields.Many2one('stock.location', string='Sending Location')
    receiving_id = fields.Many2one('tel.asn.receiving', string="ASN Number")
    warehouse_id = fields.Many2one('stock.warehouse', string='Receiving warehouse', default=lambda self: self.env.user.warehouse_id.id)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    state = fields.Selection([('draft', 'Draft'),('pending','Pending'),('completed','Completed'),('cancel', 'Cancelled')],
        string='Status', default='draft')

    total_atm = fields.Char(string='Total ATM', compute='count_total_atm')
    total_signage = fields.Char(string='Total Signage', compute='count_total_signage')
    total_accessory = fields.Char(string='Total Accessory', compute='count_total_accessory')


    # move_type = fields.Selection([
    #     ('direct', 'As soon as possible'),
    #     ('one','When all products are ready'),
    # ], string='Shipping Policy',track_visibility='onchange', default='one')

    # priority = fields.Selection([
    #     ('0', 'Not Urgent'),
    #     ('1','Normal'),
    #     ('2','Urjent'),
    #     ('3', 'Very Urgent')
    # ], string='Priority',track_visibility='onchange', default='1')


    asn_bol_type = fields.Selection([('asn', 'ASN'),('bol','BOL')], string='Type', default='bol')

    stock_move_count = fields.Integer('Stock Move', compute="stock_move_total_count")
    stock_transfer_count = fields.Integer('Transfer', compute="transfer_total_count")
    receiving_order_line = fields.One2many('tel.receiving.line', 'tel_receiving_id', string='Revceiving Lines', ondelete='cascade')    


# Function for view stock in button and Count Records
    # def stock_move_total_count(self):
    #     stock_move_ids = self.env['stock.move'].search([('tel_receive_id', '=', self.id)])
    #     self.stock_move_count = len(stock_move_ids)

    # def transfer_total_count(self):
    #     transfer_ids = self.env['stock.picking'].search([('tel_receive_id', '=', self.id)])
    #     self.stock_transfer_count = len(transfer_ids)

    # @api.multi
    # def view_stock_move(self):
    #     action = {
    #         'name': _('Stock Moves(s)'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'stock.move',
    #         'target': 'current',
    #     }
    #     stock_move_ids = self.env['stock.move'].search([('tel_receive_id', '=', self.id)])
    #     if len(stock_move_ids) == 1:
    #         action['res_id'] = stock_move_ids.ids[0]
    #         action['view_mode'] = 'form'
    #     else:
    #         action['view_mode'] = 'tree,form'
    #         action['domain'] = [('id', 'in', stock_move_ids.ids)]
    #     return action

    # @api.multi
    def view_stock_transfer(self):
        action = {
            'name': _('Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'target': 'current',
        }
        stock_transfer_ids = self.env['stock.picking'].search([('tel_receive_id', '=', self.id)])
        if len(stock_transfer_ids) == 1:
            action['res_id'] = stock_transfer_ids.ids[0]
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', stock_transfer_ids.ids)]
        return action


#Receiving Log Entry Function
    def confirm_receiving_log(self):

        if not self.receiving_order_line:
            raise Warning('Please Fill Inventory Line after you can Submit!')
            #raise UserError(_('Please Fill Inventory Line after you can Submit!'))

        vals = {
            'tel_receiving_log_id': self.id,
            'name': self.name,
            'expected_delivery_date': self.expected_delivery_date,
            'sending_location_id': self.sending_location_id.id, 
            'warehouse_id': self.warehouse_id.id, 
            'tel_receiving_log_id': self.id,
            'name': self.name,
            'total_atm':self.total_atm,
            'total_signage':self.total_signage,
            'total_accessory':self.total_accessory,

        }
        log_id = self.env['receiving.log.summary'].create(vals)        

        for tel_line in self.receiving_order_line:
            if int(tel_line.count_number) > 0:
                receiving_log_line = {
                    'tel_receiving_log_id': self.id,
                    'name' : tel_line.product_id.name,
                    'product_id' : tel_line.product_id.id,
                    #'count_number': tel_line.count_number,  
                    'receive_date': tel_line.received_date,  
                    'serial_number': tel_line.serial_number,
                    'funding_doc_type': tel_line.funding_doc_type,
                    'funding_doc_number': tel_line.funding_doc_number,
                    'ticl_project_id': tel_line.ticl_project_id,
                    'manufacturer_id': tel_line.manufacturer_id.id,
                    'condition_id': tel_line.condition_id.id,
                    'tel_type': tel_line.tel_type.id,

                }
                
               # log_id.receiving_log_line = [(0, 0, receiving_log_line)]
                log_id.receiving_log_line = [(0, 0, receiving_log_line)] * int(tel_line.count_number)
        self.state = 'pending'


        
        # lines = []
        # for tel_line in self.receiving_order_line:
        #     lines.append(
        #         (0,0,{
        #             'name' : tel_line.product_id.name,
        #             'product_id' : tel_line.product_id.id,
        #             'count_number': tel_line.count_number,  
        #             'receive_date': tel_line.received_date,  
        #             'serial_number': tel_line.serial_number,
        #             'funding_doc_type': tel_line.funding_doc_type,
        #             'funding_doc_number': tel_line.funding_doc_number,
        #             'ticl_project_id': tel_line.ticl_project_id,
        #             'manufacturer_id': tel_line.manufacturer_id.id,
        #             'condition_id': tel_line.condition_id.id,
        #             'tel_type': tel_line.tel_type.id,

        #             })
        #         )  

        # vals = {
        #     'expected_delivery_date': self.expected_delivery_date,
        #     'sending_location_id': self.sending_location_id.id, 
        #     'warehouse_id': self.warehouse_id.id, 
        #     'tel_receiving_log_id': self.id,
        #     'name': self.name,
        #     'total_atm':self.total_atm,
        #     'total_signage':self.total_signage,
        #     'total_accessory':self.total_accessory,
        #     'receiving_log_line':lines,

        # }
        # log_id = self.env['receiving.log.summary'].create(vals)
        # self.state = 'pending'



# this function for Completed Shipment

    def confirm_shipment_order(self):
        source_location_id = self.env['stock.location'].search([('location_id.name','=', self.warehouse_id.code)],limit=1)
        stock_picking_type_id = self.env['stock.picking.type'].search([('warehouse_id','=', self.warehouse_id.id), ('code','=', 'internal')],limit=1)
        vals = {
            'picking_type_id' : stock_picking_type_id.id,
            'shipped_date': self.asn_received_date,
            'location_id': self.sending_location_id.id, 
            'location_dest_id': source_location_id.id, 
            'tel_receive_id': self.id,
            'origin': self.name,

        }
        picking_id = self.env['stock.picking'].create(vals)        

        for tel_line in self.receiving_order_line:
            move_ids_without_package = {
                'name' : tel_line.product_id.name,
                'product_id' : tel_line.product_id.id,
                'product_uom_qty': tel_line.count_number, 
                'product_uom': tel_line.product_id.uom_id.id,
                'location_id': self.sending_location_id.id,
                'location_dest_id': source_location_id.id,  
                'receive_date': tel_line.received_date,  
                'tel_receive_id': self.id,
                'serial_number': tel_line.serial_number,
                'fund_doc_type': tel_line.funding_doc_type,
                'fund_doc_number': tel_line.funding_doc_number,
                'ticl_project_id': tel_line.ticl_project_id,
                'manufacturer_id': tel_line.manufacturer_id.id,
                'condition_id': tel_line.condition_id.id,
                'categ_id': tel_line.tel_type.id,
                'order_from_receipt': True,
                'origin': self.name,
            }
            picking_id.move_ids_without_package = [(0, 0, move_ids_without_package)]
        self.state = 'completed'


class TelAsnReceivingLine(models.Model):
    _name = 'tel.receiving.line'
    _inherit = ['mail.thread']
    _description = "Tel Receiving Line"
    _order = "id desc"

    @api.onchange('tel_type', 'ticl_checked')
    def _all_checked(self):
        for line in self:
            if line.tel_type.name == 'ATM':
                self.ticl_checked = True
                self.count_number = 1
            else:
                self.ticl_checked = False
                self.count_number = ''


    name = fields.Text(string='Description')
    received_date = fields.Date(string='Received Date', default=datetime.date(datetime.now()))
    check_asn = fields.Boolean(string="Check ASN", required=True)
    tel_receiving_id = fields.Many2one('tel.receiving', string='Receiving Reference', invisible=1)
    product_id = fields.Many2one('product.product', string='Model Name')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    serial_number = fields.Char(string='Serial #')
    count_number = fields.Char(string='Count')
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    tel_type = fields.Many2one('product.category', string="Type")
    funding_doc_type = fields.Char(string = "Funding Doc Type")
    funding_doc_number = fields.Char(string = "Funding Doc No.")
    ticl_project_id = fields.Char(string = "Project Id")
    ticl_checked = fields.Boolean(string="Check")



    @api.model
    def so_barcode(self, serial_number):
        tel_obj = self.env['tel.serial.number']
        tel_receiving_line = self.env['tel.receiving.line']
        tel_no = tel_obj.search([('serial_number', '=', self.serial_number)])
        for res in self:
            if res.serial_number != tel_no.serial_number:
                raise Warning('There is no serial number as such!')
            
            if res.serial_number == tel_no.serial_number:
                for tel in tel_no:
                    vals = {
                            'product_id' : tel.product_id.id,
                            'manufacturer_id' : tel.product_id.manufacturer_id.id,
                            'condition_id' : tel.product_id.condition_id.id,
                            'tel_type' : tel.product_id.categ_id.id,
                             }
                    record = self.update(vals)
                    
                    
                    
    @api.onchange('serial_number', 'product_id')
    def onchange_serial_number(self):
        tel_obj = self.env['tel.serial.number']
        tel_receiving_line = self.env['tel.receiving.line']
        tel_no = tel_obj.search([('serial_number', '=', self.serial_number)])
        print ("============tel_no========", tel_no)
        for res in self:
            # if res.serial_number != tel_no.serial_number:
            #     raise Warning('There is no serial number as such!')
            
            if res.serial_number == tel_no.serial_number:
                for tel in tel_no:
                    vals = {
                            'product_id' : tel.product_id.id,
                            'manufacturer_id' : tel.product_id.manufacturer_id.id,
                            'condition_id' : tel.product_id.condition_id.id,
                            'tel_type' : tel.product_id.categ_id.id,
                             }
                    record = self.update(vals)