# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

import time
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64


class ticl_receipt(models.Model):
    _name = 'ticl.receipt.asn'
    _description = "Receiving Import"
    _order = 'id desc'


#Total ATM
    @api.depends('ticl_receipt_lines.count_number')
    def count_total_atm(self):  
        for receving in self:      
            total_atm = 0     
            for line in receving.ticl_receipt_lines:
                if line.tel_type.name == 'ATM':
                    total_atm += int(line.count_number)  
            receving.update({'total_atm': total_atm })

#Total Signage
    @api.depends('ticl_receipt_lines.count_number')
    def count_total_signage(self):  
        for receving in self:      
            total_signage = 0
            for line in receving.ticl_receipt_lines:
                if line.tel_type.name == 'Signage':
                    total_signage += int(line.count_number)  
            receving.update({'total_signage': total_signage })

#Total Accessory
    @api.depends('ticl_receipt_lines.count_number')
    def count_total_accessory(self):  
        for receving in self:      
            total_accessory = 0
            for line in receving.ticl_receipt_lines:
                if line.tel_type.name == 'Accessory':
                    total_accessory += int(line.count_number)  
            receving.update({'total_accessory': total_accessory })

#Total quarantine if any Item In quarantine so state change in quarantine not create Log
    @api.depends('ticl_receipt_lines.condition_id')
    def count_total_quarantine(self):  
        for receving in self:      
            total_quarantine = 0
            for line in receving.ticl_receipt_lines:
                if line.condition_id.name == 'Quarantine':
                    total_quarantine += 1
            receving.update({'total_quarantine': total_quarantine })

     #delivery date plus five days       
    def _get_delivery_date(self):
        today = datetime.today()
        wk = today.weekday()
        days = 0
        if wk in (0,1,2,3,4,6):
            days = 7
        elif wk == 5:
            days = 6
        else:
            days = 5
        deliveryDate = today + timedelta(days=days)
        return deliveryDate

    attachment = fields.Binary(string="Attachment")
    store_fname = fields.Char(string="File Name")
    name = fields.Char(string='Receipt', index=True, readonly=True)
    tel_note = fields.Char(string='Comment/Note')
    asn_received_date = fields.Date(string='Received Date')
    delivery_date = fields.Date(string='Delivery Date')
    # bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)',related='receipt_id.bill_of_lading_number', store=True)
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)',store=True)
    sending_location_id = fields.Many2one('res.partner', string='Origin Location')
    receiving_location_id = fields.Many2one('stock.location', string='Receiving Location')
    receiving_id = fields.Many2one('tel.asn.receiving', string="ASN Number")
    warehouse_id = fields.Many2one('stock.warehouse', string='Receiving warehouse', default=lambda self: self.env.user.warehouse_id.id)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    asn_bol_type = fields.Selection([('asn', 'ASN'),('bol','BOL')], string='Type', default='bol')
    state = fields.Selection(related='receipt_id.state', store=True,string='Status')
    total_atm = fields.Char(string='Total ATM', compute='count_total_atm')
    total_signage = fields.Char(string='Total Signage', compute='count_total_signage')
    total_accessory = fields.Char(string='Total Accessory', compute='count_total_accessory')
    ticl_receipt_lines = fields.One2many('ticl.receipt.line.asn', 'ticl_receipt_id', ondelete='cascade')
    total_quarantine = fields.Char(string='Quarantine', compute='count_total_quarantine')
    start_quarantine_date = fields.Date(string='Start Quarantine Date')
    end_quarantine_date = fields.Date(string='End Quarantine Date')
    # shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier',related='receipt_id.shipping_carrier_id', store=True)
    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier',store=True)
    pick_up_date = fields.Date(string='Pick up Date')
    pickup_date = fields.Date(string='PickUp Date')
    accepted_date =  fields.Date(string='Accepted Date', store=True)
    # accepted_date =  fields.Date(string='Accepted Date',related='receipt_id.accepted_date', store=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee')
    receipt_id = fields.Many2one('ticl.receipt', string="Receipt No")
    receipt_name = fields.Char(string='Receipt Name')
    total_pallet = fields.Char(string='Total Pallet')
    # ticl_receipt = fields.One2many('ticl.receipt', 'asn_receipt')


# Employee Auto Update in
    @api.onchange('user_id')
    def on_change_user(self):
        if not self.user_id:
            return {}
        emp = self.env['hr.employee'].search([('user_id','=',self.user_id.id)])
        self.hr_employee_id = emp

    # @api.multi
    def submit_asn(self):
        emp = self.env['hr.employee'].search([('user_id','=',self.user_id.id)])
        warehouse_id = self.env['stock.warehouse'].search([('name', '=', self.receiving_location_id.name)])
        vals = {
            'pickup_date': self.pickup_date,
            'hr_employee_id': emp.id,
            'sending_location_id': self.sending_location_id.id,
            'receiving_location_id': self.receiving_location_id.id,
            'old_name': self.receipt_name,
            'total_pallet':self.total_pallet,
            'warehouse_id':warehouse_id.id

        }
        ticl_ship_lines = []
        total_weight = []
        total_monitory_value = []
        for line in self.ticl_receipt_lines:
            if line.tel_type.name =='ATM' and line.condition_id.name in ('Refurb Required - L1','Refurb Required - L2','Significant Damage') or line.condition_id.name == 'To Recommend':
                line.hide_cod = False
                line.tel_cod = "Y"
            else:
                line.hide_cod = True
            ticl_ship_lines.append((0,0,{
                "tel_type":line.tel_type.id,
                "product_id" :line.product_id.id,
                "serial_number":line.serial_number,
                "count_number" :line.count_number,
                "type_dup": line.tel_type.id,
                "manufacturer_id_dup": line.product_id.manufacturer_id.id,
                "manufacturer_id":line.product_id.manufacturer_id.id,
                "condition_id":line.condition_id.id,
                "xl_items": line.product_id.xl_items,
                "tel_cod": line.tel_cod,
                "monitory_value": line.product_id.monitory_value,
                "product_weight": line.product_id.product_weight,
            }))
            if line.product_id.product_weight:
                product_weight_int = int(line.product_id.product_weight)
                total_weight.append(product_weight_int)

            if line.product_id.monitory_value:
                monitory_value_int = int(line.product_id.monitory_value)
                total_monitory_value.append(monitory_value_int)

        vals['total_weight'] = sum(total_weight)
        vals['total_monitory_value'] = sum(total_monitory_value)
        vals.update({'ticl_receipt_lines':ticl_ship_lines})

        rcpt = self.env['ticl.receipt'].create(vals)
        self.name = rcpt.name
#         self.state = 'submit'
        self.receipt_id = rcpt.id
        return True
        
    # write method for updating data in Receipt Page
    # @api.multi
    def write(self, values):
        tel_receipt = self.env['ticl.receipt'].search([('name', '=', self.name)])
        if 'total_pallet' in values.keys():
            tel_receipt.write({'total_pallet': values['total_pallet']})
        return super(ticl_receipt, self).write(values)



class ticl_receipt_line(models.Model):
    _name = 'ticl.receipt.line.asn'
    _description = "Receiving Line"


    @api.onchange('product_id')
    def onchange_product_id(self):
        self.manufacturer_id = self.product_id.manufacturer_id.id or False
        #self.condition_id = self.product_id.condition_id.id or False

    @api.onchange('tel_type', 'ticl_checked')
    def _all_checked(self):
        for line in self:
            if line.tel_type.name == 'ATM':
                self.ticl_checked = True
                self.count_number = 1
                self.hide_xl_items = True
                self.xl_items = ''
            else:
                self.ticl_checked = False
                self.count_number = ''
                self.hide_xl_items = False


# NCR FUnction for Validation
    @api.onchange('manufacturer_id', 'serial_number')
    def _onchange_serial_number(self):
        if self.serial_number and self.manufacturer_id.name:
            if len(self.serial_number) != 8 and self.manufacturer_id.name == "NCR":
                self.serial_number = ''
                return {
                    'warning': {
                        'title': "Warning",
                        'message': "Serial number should be 8 Digit for NCR ATM's !",
                    }

                }

# XL FUnction for Validation
    @api.onchange('tel_type')
    def onchange_tel_type(self):
        for line in self:
            if line.tel_type.name != 'ATM':
                self.xl_items = 'y'
                self.hide_cod = True
            else:
                self.xl_items = 'n'
                self.hide_cod = False

# Filter Product Basis of Product TYpe
    @api.onchange('tel_type', 'condition_id')
    def onchange_product_type(self):
        res = {}
        if self.tel_type.name == 'ATM':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
        elif self.tel_type.name == 'Accessory':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
        elif self.tel_type.name == 'Signage':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
        else:
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
            
        if self.tel_type.name == 'ATM' and self.condition_id.name == 'Used':
            self.hide_cod = False
            self.tel_cod = 'Y'
        else:
            self.hide_cod = True
        return res

#Check for Used Condition ATM
    @api.onchange('condition_id')
    def onchange_move_inventory(self):
        if self.condition_id.name != 'Used':
            self.check_move_inventory = True
        else:
            self.check_move_inventory = False


# TICL Service Charges Fnction 
    @api.depends('tel_type', 'xl_items', 'service_price', 'repalletize')
    def _total_service_price(self):
        rec_repalletize = self.env['ticl.service.charge'].search([('name', '=', 'Repalletize')])
        for line in self:
            rec_log = self.env['ticl.service.charge'].search([('name', '=', 'ATM'),('monthly_service_charge', '=', False)])
            if line.tel_type.name == "ATM":
                line.service_price = rec_log.service_price
                if line.repalletize == "y":
                    line.service_price = rec_log.service_price + rec_repalletize.service_price 

            rec_signage = self.env['ticl.service.charge'].search([('name', '=', 'Signage'),('xl_items', '=', 'y'),('monthly_service_charge', '=', False)])
            if line.tel_type.name == "Signage" and line.xl_items == "y":
                line.service_price = rec_signage.service_price
                if line.repalletize == "y":
                    line.service_price = rec_signage.service_price + rec_repalletize.service_price

            rec_signage = self.env['ticl.service.charge'].search([('name', '=', 'Signage'),('xl_items', '=', 'n'),('monthly_service_charge', '=', False)])
            if line.tel_type.name == "Signage" and line.xl_items == "n":
                line.service_price = rec_signage.service_price
                if line.repalletize == "y":
                    line.service_price = rec_signage.service_price + rec_repalletize.service_price

            rec_accessory = self.env['ticl.service.charge'].search([('name', '=', 'Accessory'),('xl_items', '=', 'y'),('monthly_service_charge', '=', False)])
            if line.tel_type.name == 'Accessory' and line.xl_items == 'y':
                line.service_price = rec_accessory.service_price
                if line.repalletize == "y":
                    line.service_price = rec_accessory.service_price + rec_repalletize.service_price

            rec_accessory = self.env['ticl.service.charge'].search([('name', '=', 'Accessory'),('xl_items', '=', 'n'),('monthly_service_charge', '=', False)])
            if line.tel_type.name == 'Accessory' and line.xl_items == 'n':
                line.service_price = rec_accessory.service_price
                if line.repalletize == "y":
                    line.service_price = rec_accessory.service_price + rec_repalletize.service_price

                

    name = fields.Text(string='Description')
    received_date = fields.Date(string='Received Date', default=datetime.today())
    check_asn = fields.Boolean(string="Check ASN")
    ticl_receipt_id = fields.Many2one('ticl.receipt.asn', invisible=1)
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
    tel_note = fields.Char(string='Comment/Note')
    tel_cod = fields.Selection([('Y', 'Y'),('N','N')], string='COD')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')], default='y')
    hide_cod = fields.Boolean(string="Hide COD")
    #service_price = fields.Float(string='Price')
    service_price = fields.Float(string='Price', compute ='_total_service_price')
    check_move_inventory = fields.Boolean(string="Move Inventory")
    hide_xl_items = fields.Boolean(string="Hide XL")
    repalletize = fields.Selection(string="Repalletize", selection=[('y', 'Y'), ('n', 'N')], default='n')
