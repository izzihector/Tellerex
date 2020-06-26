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
from odoo import models, fields, api, _,tools
from odoo.exceptions import UserError
import os

import xlrd
import urllib
import io
import logging

logger = logging.getLogger(__name__)
#from googleapiclient.http import MediaIoBaseDownload
#from apiclient import discovery
#from httplib2 import Http
#import oauth2client
#from oauth2client import file, client, tools
import base64


class ticl_receipt_log_summary(models.Model):
    _name = 'ticl.receipt.log.summary'
    _inherit = ['mail.thread']
    _description = "Receiving Order"
    _order = 'delivery_date desc, id desc'
    _order = "id desc"


    #Default Supplier Location Fucntion
    @api.model
    def _default_location(self):
        location = self.env['stock.location'].search([('usage','=','supplier')])
        print("==location=====",location)
        return location

    # Total Cleaned ATM
    @api.depends('ticl_receipt_summary_lines.atm_cleaned')
    def count_total_cleaned_atm(self):
        for receving_log in self:
            count_cleaned_atm = 0
            for line in receving_log.ticl_receipt_summary_lines:
                if line.atm_cleaned == False and line.tel_type.name == 'ATM' and line.product_id.name != '5285' and line.tel_cod == 'Y':
                    count_cleaned_atm += 1
            receving_log.update({'count_cleaned_atm': count_cleaned_atm})

    # Total Atm Photographed
    @api.depends('ticl_receipt_summary_lines.atm_photographed')
    def total_count_atm_photographed(self):
        for receving_log in self:
            count_atm_photographed = 0
            for line in receving_log.ticl_receipt_summary_lines:
                if line.atm_photographed == False and line.tel_type.name == 'ATM' and line.condition_id.name == 'Refurb Required' or line.condition_id.name == 'To Recommend' or line.condition_id.name == 'Significant Damage' and line.product_id.name != '5285' and line.tel_cod == 'Y':
                    count_atm_photographed += 1
            receving_log.update({'count_atm_photographed': count_atm_photographed})

    # Total Atm Data Destroyed
    @api.depends('ticl_receipt_summary_lines.atm_data_destroyed')
    def total_count_atm_data_destroyed(self):
        for receving_log in self:
            count_atm_data_destroyed = 0
            for line in receving_log.ticl_receipt_summary_lines:
                if line.atm_data_destroyed == False and line.tel_type.name == 'ATM' and line.condition_id.name == 'Refurb Required' or line.condition_id.name == 'To Recommend' or line.condition_id.name == 'Significant Damage' and line.product_id.name != '5285' and line.tel_cod == 'Y':
                    count_atm_data_destroyed += 1
            receving_log.update({'count_atm_data_destroyed': count_atm_data_destroyed})

    # Total Cleaned ATM
    @api.depends('ticl_receipt_summary_lines.atm_wrapped')
    def total_atm_wrapped(self):
        for receving_log in self:
            count_atm_wrapped = 0
            for line in receving_log.ticl_receipt_summary_lines:
                if line.atm_wrapped == False and line.tel_type.name == 'ATM' and line.condition_id.name == 'Refurb Required' or line.condition_id.name == 'To Recommend' or line.condition_id.name == 'Significant Damage' and line.product_id.name != '5285' and line.tel_cod == 'Y':
                    count_atm_wrapped += 1
            receving_log.update({'count_atm_wrapped': count_atm_wrapped})

    # Total Count processing ATM
    @api.onchange('count_cleaned_atm', 'count_atm_photographed', 'count_atm_data_destroyed', 'count_atm_wrapped')
    def total_atm_count_process(self):
        for ids in self.ticl_receipt_summary_lines:
            if ids.tel_type.name == 'ATM':
                if self.count_cleaned_atm or self.count_atm_photographed or self.count_atm_data_destroyed or self.count_atm_wrapped:
                    self.atm_count_process = self.count_cleaned_atm + self.count_atm_photographed + self.count_atm_data_destroyed + self.count_atm_wrapped
    # @api.one
    def total_atm_count(self):
        for ids in self:
            ids.total_atm = ids.tel_receipt_log_id.total_atm

    # @api.one
    def total_signage_count(self):
        for ids in self:
            ids.total_signage = ids.tel_receipt_log_id.total_signage

    # @api.one
    def total_accessory_count(self):
        for ids in self:
            ids.total_accessory = ids.tel_receipt_log_id.total_accessory

    # @api.one
    def count_total_lockbox(self):
        for ids in self:
            ids.total_lockbox = ids.tel_receipt_log_id.total_lockbox

    # @api.one
    def count_total_xl(self):
        for ids in self:
            ids.total_xl = ids.tel_receipt_log_id.total_xl



    name = fields.Char(string='Receipt', index=True, readonly=True,track_visibility='onchange')
    tel_note = fields.Char(string='Comment/Note')
    asn_received_date = fields.Date(string='Received Date')
    pickup_date = fields.Date(string='Pick up Date',track_visibility='onchange')
    delivery_date = fields.Date(string='Delivery Date',track_visibility='onchange')
    estimated_delivery_date = fields.Date(string='Est Delivery Date')
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)',track_visibility='onchange')

    sending_location_id = fields.Many2one('res.partner', string='Origin Location',track_visibility='onchange')
    receiving_location_id = fields.Many2one('stock.location', string='Destination Location',track_visibility='onchange')
    
    receiving_id = fields.Many2one('tel.asn.receiving', string="ASN Number")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    state = fields.Selection(
        [('draft', 'Draft'), ('pending', 'Pending'), ('inprogress', 'In-Progress'), ('completed', 'Completed'),
         ('quarantine', 'Quarantine'), ('cancel', 'Cancelled')],track_visibility='onchange',
        string='Status', default='inprogress')

    # total_atm = fields.Char(string='# of ATM')
    # total_signage = fields.Char(string='# of Signage')
    # total_accessory = fields.Char(string='# of Accessories')

    total_atm = fields.Char(string='# of ATM', compute="total_atm_count")
    total_signage = fields.Char(string='# of Signage', compute="total_signage_count")
    total_accessory = fields.Char(string='# of Accessories', compute="total_accessory_count")
    total_lockbox = fields.Char(string='# of Lockbox', compute='count_total_lockbox')
    total_xl = fields.Char(string='# of XL', compute='count_total_xl')

    asn_bol_type = fields.Selection([('asn', 'ASN'), ('bol', 'BOL')], string='Type', default='bol')
    ticl_receipt_summary_lines = fields.One2many('ticl.receipt.log.summary.line', 'ticl_receipt_summary_id',
                                                 ondelete='cascade',track_visibility='onchange')
    ticl_receipt_payment_lines_log = fields.One2many('ticl.receipt.payment.log', 'ticl_receipt_log_payment_id', ondelete='cascade')


    tel_receipt_log_id = fields.Many2one("ticl.receipt", string="TEL Received ID")
    placard_printing = fields.Selection(
        [('atm', 'ATM'), ('accessory', 'Accessory'), ('accessory', 'Accessory'), ('signage', 'Signage')],
        string='Placards Printing', default='atm')
    tel_type = fields.Many2one('product.category', string="Type")
    placards_count = fields.Integer('placards', compute="placards_count_total")
    used_atm_count = fields.Integer('Used ATM', compute="count_total_used_atm")
    atm_count_process = fields.Integer('Total Processing Used ATM', compute="total_atm_count_process")

    count_cleaned_atm = fields.Integer('Cleaned ATM', compute="count_total_cleaned_atm")
    count_atm_photographed = fields.Integer('Atm Photographed', compute="total_count_atm_photographed")
    count_atm_data_destroyed = fields.Integer('Data Destroyed', compute="total_count_atm_data_destroyed")
    count_atm_wrapped = fields.Integer('ATM Wrapped', compute="total_atm_wrapped")

    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier',track_visibility='onchange')
    shipment_status = fields.Char(string="Shipment Status")
    accepted_date = fields.Date(string='Accepted Date',track_visibility='onchange')
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee',track_visibility='onchange')
    summary_log_id = fields.Many2one('ticl.receipt.log.summary.line', string="Summary Id")
    quarantine_count = fields.Integer('Quarantine Items', compute="count_quarantine_items")
    old_name = fields.Char(string='Old Receipt Id', index=True)
    sent = fields.Boolean(readonly=True, default=False, copy=False,
        help="It indicates that the receipt has been sent to inventory.")

    total_cost = fields.Char(string='Total Cost')
    total_weight = fields.Char(string="Total Weight")
    total_pieces = fields.Char(string='Total Pieces')

    total_pallet = fields.Char(string='Total Pallet')
    echo_tracking_id = fields.Char(string="Echo Receipt Id")
    shipment_mode = fields.Selection([('TL', 'TL'),
                                      ('LTL', 'LTL')], string='ShipmentMode')

    echo_call = fields.Selection([('yes', 'YES'),
                                      ('no', 'NO')], string='Call Echo(Optional)')
    response_message = fields.Char(string='Responce Message') 
    error_code = fields.Char(string='Error Code')   
    error_message = fields.Char(string='Error Message')   
    error_field_name = fields.Char(string='Error Field Name')
    is_error = fields.Boolean(string='Is Error', default=False, copy=False)
    count_condition = fields.Integer('Count based on condition', compute="hide_move_to_inventory")
    hide_button_move = fields.Boolean(string='Hide', default=False)

    miles = fields.Integer(string='Miles')   
    chase_fright_cost = fields.Float(string='Chase Fright Charge')
    receipt_type = fields.Selection([('Regular', 'Regular'),('Inventory Transfer', 'Inventory Transfer'),
                                      ('Guaranteed', 'Guaranteed'),
                                      ('Expedited', 'Expedited'),('Non Freight','Non Freight'),
                                      ('Re-Consignment', 'Re-Consignment'),('warehouse_transfer', 'Warehouse Transfer')], 
                                       string='Receipt Type'
                                      ,default='Inventory Transfer',track_visibility='onchange')


    is_validate = fields.Boolean(string='Is Validate', default=False, copy=False)
    is_invoice = fields.Boolean(string='Is Invoice', default=False, copy=False)
    validate_date = fields.Date(string='Validate Date')
    validate_by = fields.Many2one('res.users', string="Validate By")
    approval_authority = fields.Char(string='Approval Authority')
    approved_date = fields.Date(string='Approved date')
    property_stock_supplier = fields.Many2one('stock.location', string="Vendor Location", store=True,
        default=_default_location)



   
    # Validate Fright Charge Function
    #@api.multi
    def validate_fright_charge(self):
        for record in self:
            if not record.approval_authority and record.receipt_type in ['Guaranteed','Expedited','Re-Consignment']:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view or False
                context = dict(self._context or {})
                context['message'] = "Please enter Approval Authority before validate!."
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

            record.write({'is_validate':True,
                          'validate_date':datetime.date(datetime.now()),
                          'validate_by':self.env.user.id})
            self.env['ticl.fright.service.line'].create_detail_mnth_fright_inv(record,'receipt')

    @api.depends('ticl_receipt_summary_lines.count_number')
    def hide_move_to_inventory(self):  
        for receiving_log in self:      
            count_condition = 0
            for line in receiving_log.ticl_receipt_summary_lines:
                if line.condition_id.name == 'New' or line.condition_id.name == 'Factory Sealed' or line.condition_id.name == 'Refurb Complete' or \
                    (line.tel_type.name == "Signage") or (line.tel_type.name == "Accessory") \
                    or (line.tel_type.name == "XL") or (line.tel_type.name == "Lockbox") or (line.tel_cod == 'N' and  line.tel_type.name == "ATM" and line.condition_id.name in ["To Recommend", "Significant Damage", "Refurb Required", "Quarantine","Refurb Required - L1","Refurb Required - L2"]):
                    count_condition += int(line.count_number) 
            receiving_log.update({'count_condition': count_condition,'hide_button_move': False })


    # This function for Quarantine items
    def count_quarantine_items(self):
        quarantine_count_ids = self.env['ticl.receipt.log.summary.line'].search(
            [('ticl_receipt_summary_id', '=', self.id), ('condition_id', '=', 'Quarantine')])
        self.quarantine_count = len(quarantine_count_ids)

#     @api.multi
    def view_total_quarantine(self):

        quarantine_item_count_ids = self.env['ticl.receipt.log.summary.line'].search(
            [('ticl_receipt_summary_id', '=', self.id), ('condition_id', '=', 'Quarantine')])
        action = self.env.ref('ticl_receiving.ticl_action_receipt_log_summary_quarantines')
        if len(quarantine_item_count_ids) >= 1:
            # action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', quarantine_item_count_ids.ids)]

        return action.read([])[0]

    # This function for Used ATM
    def count_total_used_atm(self):
        atm_count_ids = self.env['ticl.receipt.log.summary.line'].search(
            [('ticl_receipt_summary_id', '=', self.id), ('tel_type', '=', 'ATM'), ('product_id', '!=', '5285'), ('tel_cod', '=', 'Y')])
        condition_ids = []
        for ids in atm_count_ids:
            if ids.tel_type.name == 'ATM' and ids.condition_id.name == 'Significant Damage' or ids.condition_id.name == 'Refurb Required - L1' or ids.condition_id.name == 'Refurb Required - L2' or ids.condition_id.name == 'To Recommend' or ids.condition_id.name == 'Quarantine':
                condition_ids.append(ids.id)
        self.used_atm_count = len(condition_ids)

#     @api.multi
    def view_used_atm(self):
        action = {
            'name': _('COD ATM(P)'),
            'type': 'ir.actions.act_window',
            'res_model': 'ticl.receipt.log.summary.line',
            'views': [[self.env.ref('ticl_receiving.ticl_receipt_log_summary_tree_view_atm_process').id, 'tree'],
                      [self.env.ref('ticl_receiving.ticl_receipt_log_summary_form_view_placard').id, 'form']],
            'target': 'current',
        }
        atm_count_ids = self.env['ticl.receipt.log.summary.line'].search(
            [('ticl_receipt_summary_id', '=', self.id), ('tel_type', '=', 'ATM'), ('product_id', '!=', '5285'), ('tel_cod', '=', 'Y')])
        condition_ids = []
        for ids in atm_count_ids:
            if ids.tel_type.name == 'ATM' and ids.condition_id.name in ('Refurb Required - L1','Refurb Required - L2','Significant Damage') or ids.condition_id.name == 'To Recommend' or ids.condition_id.name == 'Quarantine':
                condition_ids.append(ids.id)
        if len(condition_ids) >= 1:
            # action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', condition_ids)]
        return action

    # This function for placards_count
    def placards_count_total(self):
        placards_count_ids = self.env['ticl.receipt.log.summary.line'].search(
            [('ticl_receipt_summary_id', '=', self.id), ('tel_type', '=', 'ATM')])
        self.placards_count = len(placards_count_ids)

#     @api.multi
    def view_total_placards(self):
        action = {
            'name': _('Placards(P)'),
            'type': 'ir.actions.act_window',
            'res_model': 'ticl.receipt.log.summary.line',
            'view_id': self.env.ref('ticl_receiving.ticl_receipt_log_summary_tree_view_placard').id,
            'target': 'current',
        }
        placards_count_ids = self.env['ticl.receipt.log.summary.line'].search(
            [('ticl_receipt_summary_id', '=', self.id), ('tel_type', '=', 'ATM')])
        if len(placards_count_ids) >= 1:
            action['view_mode'] = 'tree'
            action['domain'] = [('id', 'in', placards_count_ids.ids)]
        return action

    def create_mv_line(self,data,move,picking):

        location_dest_id = self.env['stock.location'].browse(data.get('location_dest_id'))
        sending_location_id = self.env['res.partner'].browse(data.get('sending_location_id'))
        wareKey = self.env['stock.location'].browse(data.get('location_dest_id')).name
        warehouse = self.env['stock.warehouse'].search([('name','=',wareKey)])
        pickingType = self.env['stock.picking.type'].search([('warehouse_id','=',warehouse.id),('name','=','Receipts')])
        moveLine = self.env['stock.move.line']
        moveLine.create({
            'picking_id':picking.id,
            'move_id':move.id,
            'lot_name':data.get('serial_number'),
            'product_id':data.get('product_id'),
#             'product_uom_qty':data.get('product_uom_qty'),
            'location_dest_id':pickingType.default_location_dest_id.id,
            'location_id':data.get('location_id'),
            'ticl_warehouse_id':location_dest_id.id,
            'product_uom_id':data.get('product_uom'),
            'sending_location_id' : sending_location_id.id,
#             'product_qty':0,
            'qty_done':1,
            #'state':'confirmed',
            'reference':picking.name,
            'origin' : data.get('origin'),
            'tel_cod' : data.get('tel_cod'),
            'repalletize' : data.get('repalletize'),
            'order_from_receipt' : data.get('order_from_receipt'),
            'tel_note' : data.get('tel_note'),
            'tel_receipt_summary_id' : data.get('tel_receipt_summary_id'),
            'tel_unique_no' : data.get('tel_unique_no'),
            'received_date' : data.get('received_date'),
            'processed_date' : data.get('processed_date') or False,
            'cod_comments' :data.get('cod_comments') or False,
            'serial_number' : data.get('serial_number'),
            'xl_items' : data.get('xl_items'),
            'hr_employee_id' : data.get('hr_employee_id'),
            'cod_employee_id' : data.get('cod_employee_id'),
            'manufacturer_id' : data.get('manufacturer_id'),
            'condition_id' : data.get('condition_id'),
            'categ_id' : data.get('categ_id'),
            'warehouse_id' : data.get('warehouse_id'),
            'attachment_ids' : data.get('attachment_ids'),
            'monthly_service_charge' : data.get('monthly_service_charge'),
        })
        return True

    #line for picking
    # def create_mv_line(self,data,move,picking):
    #     wareKey = self.env['stock.location'].browse(data.get('location_dest_id')).warehouse_key
    #     location_dest_id = self.env['stock.location'].browse(data.get('location_dest_id'))
    #     warehouse = self.env['stock.warehouse'].search([('warehouse_key','=',int(wareKey))])
    #     pickingType = self.env['stock.picking.type'].search([('warehouse_id','=',warehouse.id),('name','=','Receipts')])
    #     moveLine = self.env['stock.move.line'].create({
    #         'picking_id':picking.id,
    #         'move_id':move.id,
    #         'lot_name':data.get('serial_number'),
    #         'product_id':data.get('product_id'),
    #         'location_dest_id':location_dest_id.id,
    #         'location_id':data.get('location_id'),
    #         'product_uom_id':data.get('product_uom'),
    #         'origin' : data.get('origin'),
    #         'tel_cod' : data.get('tel_cod'),
    #         'repalletize' : data.get('repalletize'),
    #         'order_from_receipt' : data.get('order_from_receipt'),
    #         'tel_note' : data.get('tel_note'),
    #         'tel_receipt_summary_id' : data.get('tel_receipt_summary_id'),
    #         'tel_unique_no' : data.get('tel_unique_no'),
    #         'received_date' : data.get('received_date'),
    #         'serial_number' : data.get('serial_number'),
    #         'xl_items' : data.get('xl_items'),
    #         'hr_employee_id' : data.get('hr_employee_id'),
    #         'cod_employee_id' : data.get('cod_employee_id'),
    #         'manufacturer_id' : data.get('manufacturer_id'),
    #         'condition_id' : data.get('condition_id'),
    #         'categ_id' : data.get('categ_id'),
    #         'warehouse_id' : data.get('warehouse_id'),
    #         'attachment_ids' : data.get('attachment_ids'),
    #         'monthly_service_charge' : data.get('monthly_service_charge'),
    #         'qty_done':1,
    #         #'state':'confirmed',
    #         'reference':picking.name,
    #     })
    #     return True
    
    def create_picking(self, data):
        wareKey = self.env['stock.location'].browse(data.get('location_dest_id')).name
        print("==wareKey===",wareKey)
        warehouse = self.env['stock.warehouse'].search([('name','=',wareKey)])
        print("==warehouse===",warehouse)
        pickingType = self.env['stock.picking.type'].search([('warehouse_id','=',warehouse.id),('name','=','Receipts')])
        name = self.env['product.product'].browse(int(data.get('product_id'))).name
        product_id = self.env['product.product'].browse(int(data.get('product_id')))
        move_ids_without_package = [(0,0,
                                    {'name':name,'product_uom':1,
                                      'product_id':data.get('product_id'),
                                      'product_uom_qty':data.get('product_uom_qty'),
                                      'quantity_done':data.get('product_uom_qty'),
                                      'manufacturer_id':product_id.manufacturer_id.id,
                                      'categ_id' : product_id.categ_id.id,
                                      # 'picking_type_id':pickingType.id,
                                      # 'location_id':data.get('location_id'),
                                     # 'location_dest_id': pickingType.default_location_dest_id.id,
#                                       'quantity_done':data.get('product_uom_qty')
                                    })]


        vals = {
            'location_dest_id':pickingType.default_location_dest_id.id,
            'picking_type_id':pickingType.id,
            'location_id':data.get('location_id'),
            'move_ids_without_package':move_ids_without_package,
            'move_type': 'direct',
            'state':'confirmed',
            'origin':self.name,
        }
        print('\n\n move_ids_without_package', vals)
        picking = self.env['stock.picking'].create(vals)
        del_move = self.env['stock.move'].search([('picking_id','=',picking.id)])
        del_move.unlink()
        return picking

    # This function for Warehouse Transfer
    def confirm_transfer(self):
        if self.receipt_type == 'warehouse_transfer':
            for s_num in self.ticl_receipt_summary_lines:
                move_id = self.env['stock.move'].search(
                    [('serial_number', '=', s_num.serial_number), ('status', '=', 'inventory')])
                # move_id.write({'status': 'transferred', 'transferred_warehouse': self.receiving_location_id.id})
            service = self.env['ticl.service.charge'].search([])
            self.env.cr.execute("""select 
                                            t1.name as origin,
                                            t2.tel_cod as tel_cod,
                                            t2.repalletize as repalletize, 
                                            true as order_from_receipt,
                                            t2.tel_note as tel_note,
                                            t2.count_number as product_uom_qty, 
                                            t1.id as tel_receipt_summary_id, 
                                            t2.tel_unique_no as tel_unique_no,
                                            t2.received_date as received_date, 
                                            t2.serial_number as serial_number,
                                            t2.xl_items as xl_items,
                                            t2.funding_doc_type as fund_doc_type,
                                            t2.funding_doc_number as fund_doc_number,
                                            t1.hr_employee_id as hr_employee_id,
                                            t2.cod_employee_id as cod_employee_id,
                                            
                                            t3.id as product_id, 
                                            t4.name as name,
                                            t5.id as product_uom,
                                            t6.id as location_id,
                                            t7.id as manufacturer_id,
                                            t8.id as condition_id,
                                            t9.id as categ_id,
                                            t11.id as warehouse_id,
                                            %s as location_dest_id
                                            from ticl_receipt_log_summary t1 
                                            inner join ticl_receipt_log_summary_line t2 on t1.id = t2.ticl_receipt_summary_id
                                            inner join product_product t3 on t2.product_id = t3.id
                                            inner join product_template t4 on t3.product_tmpl_id = t4.id
                                            inner join uom_uom t5 on t4.uom_id = t5.id
                                            inner join res_partner t6 on t1.sending_location_id = t6.id
                                            full outer join manufacturer_order t7 on t2.manufacturer_id = t7.id
                                            inner join ticl_condition t8 on t2.condition_id = t8.id
                                            inner join product_category t9 on t2.tel_type = t9.id
                                            inner join stock_warehouse t11 on t1.warehouse_id = t11.id
                                            FULL OUTER JOIN ir_attachment t10 on t1.id = t10.res_id and t10.res_model = 'ticl_receipt_log_summary'
                                            where t1.id = %s
                    """, [self.receiving_location_id.id, self.id])
            move_ids_without_packages = self.env.cr.dictfetchall()
            # move = []
            quarantine = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
            to_recommend = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
            ref_required = self.env['ticl.condition'].search([('name', '=', 'Refurb Required')])
            sig_damage = self.env['ticl.condition'].search([('name', '=', 'Significant Damage')])
            ref_required_l1 = self.env['ticl.condition'].search([('name', '=', 'Refurb Required - L1')])
            ref_required_l2 = self.env['ticl.condition'].search([('name', '=', 'Refurb Required - L2')])
            product_category = self.env['product.category'].search([('name', '=', 'ATM')])
            byepass_product = self.env['product.product'].search([('name', '=', '5285')])
            picking = self.create_picking(move_ids_without_packages[0])

            for move_ids_without_package in move_ids_without_packages:
                move_ids_without_package.update({
                    'attachment_ids': [(6, None, self.attachment_ids.ids)],
                    'picking_id': picking.id,
                    'picking_type_id': picking.picking_type_id.id,
                })
                x = self.env['ticl.receipt.log.summary'].search([('name', '=', move_ids_without_package['origin'])])
                service_cost = 0
                for k in x.ticl_receipt_summary_lines:
                    if k.product_id.name == move_ids_without_package['name']:
                        for i in service:
                            if i.monthly_service_charge == True:
                                if str(k.tel_type.name) == str(i.name):
                                    service_cost = i.service_price
                move_ids_without_package['monthly_service_charge'] = service_cost
                # if move_ids_without_package['condition_id'] != quarantine.id:
                # if move_ids_without_package['move_to_inv'] == 'n':
                #     if move_ids_without_package['categ_id'] == product_category.id:
                #         if move_ids_without_package['condition_id'] not in [to_recommend.id,ref_required.id,ref_required_l1.id,ref_required_l2.id,sig_damage.id,quarantine.id] \
                #                             or move_ids_without_package['product_id'] == byepass_product.id or (move_ids_without_package['tel_cod'] == "N" and  move_ids_without_package['condition_id'] in [to_recommend.id,ref_required.id,sig_damage.id,quarantine.id,ref_required_l1.id,ref_required_l2.id]) :
                #
                #             move_id = self.env['stock.move'].search([
                #                 ('origin', '=', self.name),
                #                 ('tel_unique_no', '=', move_ids_without_package['tel_unique_no'])])
                #
                #             if move_id.id != False:
                #                 raise UserError('These Records are already in Inventory')
                #
                #             move = self.env['stock.move'].create(move_ids_without_package)
                #             for ids in self.ticl_receipt_summary_lines:
                #                 if move.tel_unique_no == ids.tel_unique_no:
                #                     misc_lines = self.env['common.misc.line'].search(
                #                         [('receipt_log_summary_line_id', '=', ids.id)])
                #                     misc_lines = self.env['common.misc.line'].search(
                #                         [('receipt_log_summary_line_id', '=', ids.id)])
                #                     if misc_lines.ids != False:
                #                         for ids in misc_lines:
                #                             ids.write({'receiving_move_ids': move.id})
                #             self.create_mv_line(move_ids_without_package, move, picking)
                #             self.sent = True
                #             summary_line_id = self.env['ticl.receipt.log.summary.line'].search([
                #                 ('ticl_receipt_summary_id', '=',
                #                  int(move_ids_without_package['tel_receipt_summary_id'])),
                #                 ('tel_unique_no', '=', move_ids_without_package['tel_unique_no'])])
                #
                #             # summary_line_id.write({'move_to_inv': 'y'})
                #     else:
                #         move = self.env['stock.move'].create(move_ids_without_package)
                #         # move = self.env['stock.move'].create(move_ids_without_package)
                #         for ids in self.ticl_receipt_summary_lines:
                #             if move.tel_unique_no == ids.tel_unique_no:
                #                 misc_lines = self.env['common.misc.line'].search(
                #                     [('receipt_log_summary_line_id', '=', ids.id)])
                #                 misc_lines = self.env['common.misc.line'].search(
                #                     [('receipt_log_summary_line_id', '=', ids.id)])
                #                 if misc_lines.ids != False:
                #                     for ids in misc_lines:
                #                         ids.write({'receiving_move_ids': move.id})
                #         self.create_mv_line(move_ids_without_package, move, picking)
                #         summary_line_id = self.env['ticl.receipt.log.summary.line'].search(
                #             [('ticl_receipt_summary_id', '=', int(move_ids_without_package['tel_receipt_summary_id'])),
                #              ('tel_unique_no', '=', move_ids_without_package['tel_unique_no'])])
                #         # summary_line_id.write({'move_to_inv': 'y'})
                #         self.sent = True
            lst = []
            picking.with_context({'merge': False}).action_confirm()
            # for ids in self.ticl_receipt_summary_lines:
            #     lst.append(ids.move_to_inv)
            if 'n' not in lst:
                self.state = 'completed'
                self.tel_receipt_log_id.state = 'completed'
            for receiving_log in self:
                for line in receiving_log.ticl_receipt_summary_lines:
                    if line.product_id.name == '5285' or line.condition_id.name == "Factory Sealed" or line.condition_id.name == "Refurb Complete" or \
                            line.condition_id.name == "New" or (line.tel_type.name == "Signage") or \
                            (line.tel_type.name == "Accessory") or (line.tel_type.name == "XL") or \
                            (line.tel_type.name == "Lockbox") or (line.tel_cod == 'N' and  line.tel_type.name == "ATM" and line.condition_id.name in ["To Recommend", "Significant Damage", "Refurb Required", "Quarantine","Refurb Required - L1","Refurb Required - L2"]):
                        line.in_inventory = True
                        self.hide_button_move = True

            action = self.env.ref('stock.action_picking_tree_all')
            result = action.read()[0]
            result['context'] = {}
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = picking.id
            picking.action_confirm()
            picking.button_validate()
            # self.create_picking_out()
            return True








    # This function for Completed Shipment
    def confirm_shipment_order(self):
        if self.hide_button_move == True:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Items already Moved to the Inventory Successfully, Please process the remaining ATM's to Complete the Receipt!"
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

        service = self.env['ticl.service.charge'].search([])
        self.env.cr.execute("""select 
                                t1.name as origin,
                                t2.tel_cod as tel_cod,
                                t2.repalletize as repalletize, 
                                %s as order_from_receipt,
                                t2.tel_note as tel_note,
                                t2.count_number as product_uom_qty, 
                                t1.id as tel_receipt_summary_id, 
                                t2.tel_unique_no as tel_unique_no,
                                t2.received_date as received_date, 
                                t2.serial_number as serial_number,
                                t1.sending_location_id as sending_location_id,
                                t2.xl_items as xl_items,
                                t1.hr_employee_id as hr_employee_id,
                                t2.cod_employee_id as cod_employee_id,
                                t3.id as product_id, 
                                t4.name as name,
                                t5.id as product_uom,
                                t6.id as location_id,
                                t7.id as manufacturer_id,
                                t8.id as condition_id,
                                t2.move_to_inv as move_to_inv,
                                t9.id as categ_id,
                                t11.id as warehouse_id,
                                %s as location_dest_id
                                from ticl_receipt_log_summary t1 
                                inner join ticl_receipt_log_summary_line t2 on t1.id = t2.ticl_receipt_summary_id
                                inner join product_product t3 on t2.product_id = t3.id
                                inner join product_template t4 on t3.product_tmpl_id = t4.id
                                inner join uom_uom t5 on t4.uom_id = t5.id
                                inner join stock_location t6 on t1.property_stock_supplier = t6.id
                                full outer join manufacturer_order t7 on t2.manufacturer_id = t7.id
                                inner join ticl_condition t8 on t2.condition_id = t8.id
                                inner join product_category t9 on t2.tel_type = t9.id
                                inner join stock_warehouse t11 on t1.warehouse_id = t11.id
                                FULL OUTER JOIN ir_attachment t10 on t1.id = t10.res_id and t10.res_model = 'ticl_receipt_log_summary'
                                where t1.id = %s
        """, [True,self.receiving_location_id.id, self.id])


        move_ids_without_packages = self.env.cr.dictfetchall()
        print("====move_ids_without_packages====",move_ids_without_packages)
        # move = []
        quarantine = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
        to_recommend = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
        ref_required = self.env['ticl.condition'].search([('name', '=', 'Refurb Required')])
        sig_damage = self.env['ticl.condition'].search([('name', '=', 'Significant Damage')])
        ref_required_l1 = self.env['ticl.condition'].search([('name', '=', 'Refurb Required - L1')])
        ref_required_l2 = self.env['ticl.condition'].search([('name', '=', 'Refurb Required - L2')])
        product_category = self.env['product.category'].search([('name', '=', 'ATM')])
        byepass_product = self.env['product.product'].search([('name', '=', '5285')])
        picking = self.create_picking(move_ids_without_packages[0])

        
        for move_ids_without_package in move_ids_without_packages:
            move_ids_without_package.update({
                'attachment_ids': [(6, None, self.attachment_ids.ids)],
                'picking_id': picking.id,
                'picking_type_id': picking.picking_type_id.id,
            })
            x = self.env['ticl.receipt.log.summary'].search([('name', '=', move_ids_without_package['origin'])])
            service_cost = 0
            for k in x.ticl_receipt_summary_lines:
                if k.product_id.name == move_ids_without_package['name']:
                    for i in service:
                        if i.monthly_service_charge == True:
                            if str(k.tel_type.name) == str(i.name):
                                service_cost = i.service_price
            move_ids_without_package['monthly_service_charge'] = service_cost
            
            
            # if move_ids_without_package['condition_id'] != quarantine.id:
            if move_ids_without_package['move_to_inv'] == 'n':
                if move_ids_without_package['categ_id'] == product_category.id:
                    if move_ids_without_package['condition_id'] not in [to_recommend.id,ref_required.id,ref_required_l1.id,ref_required_l2.id,sig_damage.id,quarantine.id] \
                                        or move_ids_without_package['product_id'] == byepass_product.id or (move_ids_without_package['tel_cod'] == "N" and  move_ids_without_package['condition_id'] in [to_recommend.id,ref_required.id,sig_damage.id,quarantine.id,ref_required_l1.id,ref_required_l2.id]):

                        move_id = self.env['stock.move'].search([
                            ('origin','=',self.name),
                            ('tel_unique_no','=',move_ids_without_package['tel_unique_no'])])

                        if move_id.id != False:
                            raise UserError('These Records are already in Inventory')


                        move = self.env['stock.move'].create(move_ids_without_package)
                        print('ref_required_l2 if')
                        # for ids in self.ticl_receipt_summary_lines:
                            # if move.tel_unique_no == ids.tel_unique_no:
                        #         misc_lines = self.env['common.misc.line'].search(
                        #                 [('receipt_log_summary_line_id', '=', ids.id)])
                        #         misc_lines = self.env['common.misc.line'].search(
                        #             [('receipt_log_summary_line_id', '=', ids.id)])
                        #         if misc_lines.ids != False:
                        #             for ids in misc_lines:
                        #                 ids.write({'receiving_move_ids': move.id})
                        self.create_mv_line(move_ids_without_package, move, picking)
                        self.sent = True
                        summary_line_id = self.env['ticl.receipt.log.summary.line'].search([
                            ('ticl_receipt_summary_id', '=',
                             int(move_ids_without_package['tel_receipt_summary_id'])),
                            ('tel_unique_no', '=', move_ids_without_package['tel_unique_no'])])

                        summary_line_id.write({'move_to_inv': 'y'})
                else:
                    move = self.env['stock.move'].create(move_ids_without_package)
                    #move = self.env['stock.move'].create(move_ids_without_package)
                    # for ids in self.ticl_receipt_summary_lines:
                        # if move.tel_unique_no == ids.tel_unique_no:
                            # misc_lines = self.env['common.misc.line'].search(
                            #             [('receipt_log_summary_line_id', '=', ids.id)])
                            # misc_lines = self.env['common.misc.line'].search(
                            #     [('receipt_log_summary_line_id', '=', ids.id)])
                            # if misc_lines.ids != False:
                            #     for ids in misc_lines:
                            #         ids.write({'receiving_move_ids': move.id})
                    self.create_mv_line(move_ids_without_package,move,picking)
                    print('ref_required_l2 else')
                    summary_line_id = self.env['ticl.receipt.log.summary.line'].search(
                        [('ticl_receipt_summary_id', '=', int(move_ids_without_package['tel_receipt_summary_id'])),
                         ('tel_unique_no', '=', move_ids_without_package['tel_unique_no'])])
                    summary_line_id.write({'move_to_inv': 'y'})
                    self.sent = True
        lst = []
        picking.with_context({'merge':False}).action_confirm()
        for ids in self.ticl_receipt_summary_lines:
            lst.append(ids.move_to_inv)
        if 'n' not in lst:
            self.state = 'completed'
            self.tel_receipt_log_id.state = 'completed'

        for receiving_log in self:
            for line in receiving_log.ticl_receipt_summary_lines:
                if line.product_id.name == '5285' or line.condition_id.name == "Factory Sealed" or line.condition_id.name == "Refurb Complete" or \
                   line.condition_id.name == "New" or (line.tel_type.name == "Signage") or \
                   (line.tel_type.name == "Accessory") or (line.tel_type.name == "XL") or \
                   (line.tel_type.name == "Lockbox") or (line.tel_cod == 'N' and  line.tel_type.name == "ATM" and line.condition_id.name in ["To Recommend", "Significant Damage", "Refurb Required", "Quarantine","Refurb Required - L1","Refurb Required - L2"]):
                    line.in_inventory = True
                    self.hide_button_move = True

        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        result['context'] = {}
        res = self.env.ref('stock.view_picking_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = picking.id
        picking.action_confirm()
        picking.button_validate()
        self.hide_button_move=True
        # return result

# class ticl_receipt_log_summary_line_misc(models.Model):
#     _name = 'common.misc.line'

#     @api.depends('receipt_log_summary_line_id', 'shiplment_log_line_id', 'receiving_move_ids', 'work_time')
#     def _compute_warehouse(self):
#         warehouse = 0
#         for record in self:
#             if record.receipt_log_summary_line_id:
#                 warehouse = record.receipt_log_summary_line_id.ticl_receipt_summary_id.warehouse_id.id
#             elif record.shiplment_log_line_id:
#                 warehouse = record.shiplment_log_line_id.ticl_ship_id.warehouse_id.id
#             elif record.receiving_move_ids:
#                 str_warehouse = self.env['stock.warehouse'].search([('name','=',record.receiving_move_ids.location_dest_id.name)])
#                 warehouse = str_warehouse.id
#             record.warehouse_id = warehouse
            
#     receipt_log_summary_line_id = fields.Many2one('ticl.receipt.log.summary.line',string="Receipt log Summary Line Id")
#     shiplment_log_line_id = fields.Many2one('ticl.shipment.log.line', string="Shipment Log Line Id")
#     receiving_move_ids = fields.Many2one('stock.move',string="Stock Move")
#     document_date = fields.Date('Misc Date')
#     model_name = fields.Many2one('product.product','Model Name')
#     serial_number = fields.Char('Serial Number')
#     user_name = fields.Many2one('res.users','User Name')
#     work_time = fields.Integer("Work Time")
#     description = fields.Char("Description")
#     warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse Location', compute='_compute_warehouse', store=True)
#     one_charge = fields.Boolean(default=False)

#     @api.model
#     def create(self, vals):
#         if self._context['active_model'] == 'ticl.receipt.log.summary.line':
#             misc_ids =  self.env['common.misc.line'].search([('receipt_log_summary_line_id','=',vals['receipt_log_summary_line_id'])])
#             print('\n\n\n\n KKKKKKKKKKKKKKKK', misc_ids.ids)

#             if misc_ids.ids != []:
#                 receiving_move_ids = ''
#                 shiplment_log_line_id = ''
#                 for ids in misc_ids:
#                     if receiving_move_ids != False:
#                         receiving_move_ids = ids.receiving_move_ids
#                     if shiplment_log_line_id != False:
#                         shiplment_log_line_id = ids.shiplment_log_line_id
#                 print('\n\n 98765',receiving_move_ids,shiplment_log_line_id)
#                 vals['receiving_move_ids'] = int(receiving_move_ids)
#                 vals['shiplment_log_line_id'] = int(shiplment_log_line_id)
#         if self._context['active_model'] == 'stock.move':
#             misc_ids = self.env['common.misc.line'].search(
#                 [('receiving_move_ids', '=', vals['receiving_move_ids'])])
#             if misc_ids.ids != []:
#                 receipt_log_summary_line_id = ''
#                 shiplment_log_line_id = ''
#                 for ids in misc_ids:
#                     if receipt_log_summary_line_id != False:
#                         receipt_log_summary_line_id = ids.receipt_log_summary_line_id
#                     if shiplment_log_line_id != False:
#                         shiplment_log_line_id = ids.shiplment_log_line_id
#                 print('\n\n 98765',receipt_log_summary_line_id)
#                 vals['receipt_log_summary_line_id'] = int(receipt_log_summary_line_id)
#                 vals['shiplment_log_line_id'] = int(shiplment_log_line_id)
#         if self._context['active_model'] == 'ticl.shipment.log.line':
#             misc_ids = self.env['common.misc.line'].search(
#                 [('shiplment_log_line_id', '=', vals['shiplment_log_line_id'])])
#             if misc_ids.ids != []:
#                 receipt_log_summary_line_id = ''
#                 receiving_move_ids = ''
#                 for ids in misc_ids:
#                     if receipt_log_summary_line_id != False:
#                         receipt_log_summary_line_id = ids.receipt_log_summary_line_id
#                     if receiving_move_ids != False:
#                         receiving_move_ids = ids.receiving_move_ids
#                 print('\n\n 98765',receipt_log_summary_line_id)
#                 vals['receipt_log_summary_line_id'] = int(receipt_log_summary_line_id)
#                 vals['receiving_move_ids'] = int(receiving_move_ids)

#         return super(ticl_receipt_log_summary_line_misc, self).create(vals)






class ticl_receipt_log_summary_line(models.Model):
    _name = 'ticl.receipt.log.summary.line'
    _inherit = ['mail.thread']
    _description = "Receiving Summary Line"
    _order = "id desc, tel_unique_no desc"

    #ATM,EPP and HDD Images priniting in COD Report
#     @api.multi
    def get_report_images_1(self):
        from odoo import tools
        attachmnent = []
        attachmnents = self.env['ir.attachment'].search([
            ('res_model','=','ticl.receipt.log.summary.line'),
            ('res_id','=',self.id)],order="id asc", limit=9)
        for a in attachmnents:
            attachmnent.append(a.datas)
        return attachmnents

#     @api.multi
    # def ticl_action_show_details(self):
    #     self.ensure_one()
    #     view = self.env.ref('ticl_receiving.view_misc_details')
    #     return {
    #         'name': _('Misc Details'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'ticl.receipt.log.summary.line',
    #         'views': [(view.id, 'form')],
    #         'view_id': view.id,
    #         'target': 'new',
    #         'res_id': self.id,
    #         'context': {
    #             'default_model_name': self.product_id.id,
    #             'default_serial_number': self.serial_number,
    #             'default_warehouse_id': self.ticl_receipt_summary_id.warehouse_id.id,
    #         },

    #     }

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

    #onchnage for condition in Quarantine
    @api.onchange('condition_id')
    def hide_move_inventory_quarantine(self):
        if self.tel_type.name == "ATM" and self.status == 'quarantine' and (self.condition_id.name == "Refurb Required" or self.condition_id.name == "To Recommend" \
            or self.condition_id.name == "Significant Damage"):
            self.hide_mv_inv_button = True
        else:
            self.hide_mv_inv_button = False

    #  Misc Charges FUnction for TICL
    @api.onchange('misc_log_time', 'misc_charges')
    def _total_misc_charges(self):
        for line in self:
            rec_misc = self.env['ticl.service.charge'].search(
                [('name', '=', 'MISC Service Charge'), ('monthly_service_charge', '=', False)])
            count = []
            # for ids in self.ids:
            #     receipt_misc = self.env['common.misc.line'].search([('receipt_log_summary_line_id', '=', ids)])
                # for x in receipt_misc:
                #     count.append(x.work_time)
                # receipt_log_summary_id = self.env['ticl.receipt.log.summary.line'].search([('id', '=', ids)])
                # receipt_log_summary_id.write({'misc_log_time': sum(count)})
                # count = []
            misc_charges = 0.00
            if int(line.misc_log_time) >= 1:
                line.misc_charges = int(line.misc_log_time) * int(45)
            else:
                line.misc_charges = 0.00

    @api.depends('custom_hide_condition')
    def get_hide_condition_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        # self.user_has_groups('base.group_no_one')
        if res_user.has_group('base.group_no_one') and not res_user.has_group('base.group_erp_manager'):
            self.custom_hide_condition = True
        else:
            self.custom_hide_condition = False
    
    #Onchange for Repalletize Charge
    @api.onchange('repalletize', 'repalletize_charge')
    def _onchange_repalletize_charge(self):
        for line in self:
            if line.repalletize == 'y':
                repalletize = self.env['ticl.service.charge'].search([('name', '=', 'Repalletize'),('monthly_service_charge', '=', False)])
                line.repalletize_charge = repalletize.service_price
            else:
                line.repalletize_charge = 0.00


    #TICL Service Charges Function
    # @api.depends('tel_type','xl_items')
    def _ticl_service_price(self):
        for line in self:
            if line.tel_type.name == "ATM":
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Signage" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Accessory" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Signage" and line.xl_items == 'n':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Accessory" and line.xl_items =='n':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Lockbox" and line.xl_items =='n':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Lockbox" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "XL" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_summary_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
                    
    #This fumction for COD Charges                
    @api.onchange('atm_data_destroyed','cod_charges')
    def _ticl_cod_charges(self):
        for line in self:
            rec_cod_charges = self.env['ticl.service.charge'].search([('name', '=', 'Data Sanitization per ATM')])
            if line.atm_data_destroyed == True and line.condition_id.name == 'To Recommend' or line.condition_id.name == 'Significant Damage' or line.condition_id.name == 'Refurb Required':
                line.cod_charges = rec_cod_charges.service_price
            else:
                line.cod_charges = 0.00       

    name = fields.Text(string='Description')
    received_date = fields.Date(string='Received Date',track_visibility='onchange')
    processed_date = fields.Date(string='Date Processed',track_visibility='onchange')
    check_asn = fields.Boolean(string="Check ASN")
    ticl_receipt_summary_id = fields.Many2one('ticl.receipt.log.summary', string='Receiving Log Summary', required=True)
    delivery_date = fields.Date(related='ticl_receipt_summary_id.delivery_date', string='Delivery Date')
    sending_location_id = fields.Many2one('res.partner', related='ticl_receipt_summary_id.sending_location_id',
                                          ondelete='cascade',string='Sending Location')

    receiving_location_id = fields.Many2one('stock.location', related='ticl_receipt_summary_id.receiving_location_id',
                                          string='Receiving Location')
    
    warehouse_id = fields.Many2one('stock.warehouse', related='ticl_receipt_summary_id.warehouse_id',
                                   string='Warehouse Location')

    bill_of_lading_number = fields.Char(related='ticl_receipt_summary_id.bill_of_lading_number', string="BOL #")
    accepted_date = fields.Date(related='ticl_receipt_summary_id.accepted_date', string="Accepted Date")
    shipping_carrier_id = fields.Many2one('shipping.carrier', related='ticl_receipt_summary_id.shipping_carrier_id',
                                          string="Shipping Carrier")
    hr_employee_id = fields.Many2one('hr.employee', related='ticl_receipt_summary_id.hr_employee_id', string="Employee",track_visibility='onchange')
    status = fields.Selection(
        [('draft', 'Draft'), ('pending', 'Pending'), ('inprogress', 'In-Progress'), ('completed', 'Completed'),
         ('quarantine', 'Quarantine'), ('cancel', 'Cancelled')],
        related='ticl_receipt_summary_id.state'
        , string='Status',track_visibility='onchange')

    product_id = fields.Many2one('product.product', string='Model Name',track_visibility='onchange')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer",track_visibility='onchange')
    serial_number = fields.Char(string='Serial #   ',track_visibility='onchange')
    count_number = fields.Char(string='Count', default=1)
    condition_id = fields.Many2one('ticl.condition', string="Condition",track_visibility='onchange')
    tel_type = fields.Many2one('product.category', string="Type",track_visibility='onchange')
    funding_doc_type = fields.Char(string="Funding Doc Type")
    funding_doc_number = fields.Char(string="Funding Doc Number")
    ticl_project_id = fields.Char(string="Project Id")
    tel_receipt_log_id = fields.Many2one("ticl.receipt", string="TEL Received ID")
    tel_unique_no = fields.Char(string="Unique Id")
    tel_note = fields.Char(string='Comment/Note')
    ticl_lines_id = fields.Char('Ticl lines Id')

    tel_cod = fields.Selection([('Y', 'Y'), ('N', 'N')], string='COD')
    state = fields.Selection(
        [('cleaned', 'Waiting For Cleaning'), ('photographed', 'Cleaned'), ('destroyed', 'Photographed'),
         ('wrapped', 'Data Destroyed'), ('done', 'Wrapped And Done')],
        string='Status', default='cleaned')


    inbound_charges = fields.Float(string='Inbound Charges', compute=_ticl_service_price)
    misc_log_time = fields.Char(string='Misc Log Time')
    misc_charges = fields.Float(string='Misc Charges', compute=_total_misc_charges)
    associated_fees = fields.Float(string='Associated Fees')
    cod_charges = fields.Float(string='COD Charges')
    repalletize_charge = fields.Float(string="Repalletize Charge")
    service_price = fields.Float(string='Price')
    cod_comments = fields.Char(string='COD Comments')
    check_atm = fields.Boolean(string="ATM Check")
    check_move_inventory = fields.Boolean(string="Move Inventory")
    atm_cleaned = fields.Boolean(string="ATM Cleaned",track_visibility='onchange')
    atm_photographed = fields.Boolean(string="ATM Photographed",track_visibility='onchange')
    atm_data_destroyed = fields.Boolean(string="ATM Data Destroyed",track_visibility='onchange')
    atm_wrapped = fields.Boolean(string="ATM Wrapped",track_visibility='onchange')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')])
    hide_cod = fields.Boolean(string="Hide COD")
    hide_xl_items = fields.Boolean(string="Hide XL")
    repalletize = fields.Selection(string="Repalletize", selection=[('y', 'Y'), ('n', 'N')])
    cod_employee_id = fields.Many2one('hr.employee', string='COD Employee',default = lambda self: self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).id,track_visibility='onchange')
    move_to_inv = fields.Selection([('y', 'Y'), ('n', 'N')], string="Moved to Inventory",default="n")
    hide_mv_inv_button = fields.Boolean(string="Hide Move To Inventory", default=False)
    in_inventory = fields.Boolean(string="In Inventory", default=False)
    one_time_charge = fields.Boolean(default=False)
    # receipt_log_summary_misc = fields.One2many("common.misc.line", "receipt_log_summary_line_id",
    #                                            string="Receipt Log Summary Misc")

    inventory_status = fields.Char(string='Inventory Status',default='Inventory')
    check_sale =  fields.Boolean(string='Checkbox for Sale',default=False)    

    receipt_status = fields.Selection([('inventory', 'Inventory'),('assigned', 'Assigned'),('picked', 'Picked'),('packed', 'Packed'),('shipped', 'Shipped'),
        ('sold', 'Sold'),('cancel', 'Cancelled'),('recycled', 'Recycled')], string='Receipt Status', default='inventory')

    custom_hide_condition = fields.Boolean(string="Hide Condition", compute='get_hide_condition_user')

# This Function for CLeaned massege PopUP
    @api.onchange('atm_cleaned')
    def atm_cleaned_done(self):
        if self.atm_cleaned == False:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please First Check ATM Cleaned!"
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
        if self.atm_cleaned == True:
            self.state='photographed'
            
    #Onchange for ATM Photographed
    @api.onchange('atm_photographed')
    def atm_photographed_done(self):
        res = {}
        if self.epp_manufacturer == False:
            self.epp_manufacturer = ''
        if self.hdd_manufacturer == False:
            self.hdd_manufacturer = ''
        if self.epp_serial_num == False:
            self.epp_serial_num = ''
        if self.hdd_serial_num == False:
            self.hdd_serial_num = ''
        if len(self.epp_manufacturer) == 0 or len(self.hdd_manufacturer) == 0 or len(self.epp_serial_num) == 0 or len(self.hdd_serial_num) == 0 or self.cod_employee_id.id == False:
            self.atm_photographed = False
            res['warning'] = {'title': ('Warning'), 'message': (
                'Please fill the required Fields')}
            return res
        if len(self.attachment_ids) < 5 or len(self.attachment_ids_epp) < 2 or len(self.attachment_ids_hdd) < 2 :
            self.atm_photographed = False
            res['warning'] = {'title': ('Warning'), 'message': (
                'Please Upload 5 ATM Images,2 EPP# Images and 2 Hard Disk Images')}
            return res
        else:
            if self.atm_photographed == True:
                self.state = 'destroyed'
                self.processed_date = datetime.now()
    
    #Onchange for Data Destroyed
    @api.onchange('atm_data_destroyed')
    def data_destroyed_done(self):
        res={}
        if self.epp_manufacturer == False:
            self.epp_manufacturer = ''
        if self.hdd_manufacturer == False:
            self.hdd_manufacturer = ''
        if self.epp_serial_num == False:
            self.epp_serial_num = ''
        if self.hdd_serial_num == False:
            self.hdd_serial_num = ''
        if len(self.epp_manufacturer) == 0 or len(self.hdd_manufacturer) == 0 or len(self.epp_serial_num) == 0 or len(self.hdd_serial_num) == 0 or self.cod_employee_id.id == False:
            self.atm_data_destroyed = False
            res['warning'] = {'title': ('Warning'), 'message': (
                'Please fill the required Fields')}
            return res
        if self.atm_data_destroyed == True:
            if len(self.attachment_ids) < 5 or len(self.attachment_ids_epp) < 2 or len(self.attachment_ids_hdd) < 2 :
                self.atm_data_destroyed = False
                res['warning'] = {'title': ('Warning'), 'message': (
                    'Please Upload 5 ATM Images,2 EPP# Images and 2 Hard Disk Images')}
                return res
            else:
                self.state = 'wrapped'
            self.processed_date = datetime.now()

    # write method for check box 
#     @api.multi
    def write(self, values):
        if 'state' in values.keys():
            if values['state'] == 'photographed':
                values['atm_cleaned'] = True
            if values['state'] == 'destroyed':
                values['atm_photographed'] = True
                values['atm_cleaned'] = True
            if values['state'] == 'wrapped':
                # self.env['ticl.monthly.service.line'].create_detail_mnth_service_inv(self, 'destroyed')
                values['atm_cleaned'] = True
                values['atm_photographed'] = True
                values['atm_data_destroyed'] = True
            if values['state'] == 'done':
                values['atm_wrapped'] = True
                values['atm_cleaned'] = True
                values['atm_photographed'] = True
                values['atm_data_destroyed'] = True

        if 'processed_date' in values.keys():
            values['processed_date'] = datetime.now()
        if 'atm_wrapped' in values.keys() and self.in_inventory == True:
            values['state'] = 'done' 
        return super(ticl_receipt_log_summary_line, self).write(values)

    #Onchange for COD Report
#     @api.multi
    def download_cod(self):
        if len(self.attachment_ids) < 5 or len(self.attachment_ids_epp) < 2 or len(self.attachment_ids_hdd) < 2 :
            raise UserError("Please Upload 5 ATM Images,2 EPP# Images and 2 Hard Disk Images")
        report = {
            'type': 'ir.actions.report',
            'report_name': 'ticl_receiving.data_destruction_report_card',
            'report_type': 'qweb-pdf',
            'report_file': 'ticl_receiving.data_destruction_report_card',
            'name': 'ticl.receipt.log.summary.line',
        }
        return report

    #Onchange for Atm Wrapped    
    @api.onchange('atm_wrapped')
    def atm_wrapped_done(self):
        res = {}
        if self.atm_wrapped == False:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please First Check ATM Wrapped And Also Attached Photograph!"
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
        if self.atm_wrapped == True:
            if self.epp_manufacturer == False:
                self.epp_manufacturer = ''
            if self.hdd_manufacturer == False:
                self.hdd_manufacturer = ''
            if self.epp_serial_num == False:
                self.epp_serial_num = ''
            if self.hdd_serial_num == False:
                self.hdd_serial_num = ''
            if len(self.epp_manufacturer) == 0 or len(self.hdd_manufacturer) == 0 or len(
                    self.epp_serial_num) == 0 or len(self.hdd_serial_num) == 0 or self.cod_employee_id.id == False:
                self.atm_wrapped = False
                res['warning'] = {'title': ('Warning'), 'message': (
                    'Please fill the required Fields')}
                return res
            if len(self.attachment_ids) < 5 or len(self.attachment_ids_epp) < 2 or len(self.attachment_ids_hdd) < 2 :
                self.atm_wrapped = False
                res['warning'] = {'title': ('Warning'), 'message': (
                    'Please Upload 5 ATM Images,2 EPP# Images and 2 Hard Disk Images')}
                return res



    # Create Stock Move for Used ATM and wrapped and Done process
#     @api.multi
    def atm_process_done(self):
        res ={}
        x = [0]
        if len(self.attachment_ids) < 5 or len(self.attachment_ids_epp) < 2 or len(self.attachment_ids_hdd) < 2 :
            x[0]=1
            raise UserError("Please Upload 5 ATM Images,2 EPP# Images and 2 Hard Disk Images")
        if x[0]==0:
            if self.atm_wrapped == True or self.atm_data_destroyed:
                processed_date = datetime.now()
                if len(self.epp_manufacturer) == 0 or len(self.hdd_manufacturer) == 0 or len(
                        self.epp_serial_num) == 0 or len(self.hdd_serial_num) == 0 or self.cod_employee_id.id == False:
                    res['warning'] = {'title': ('Warning'), 'message': (
                        'Please fill the required Fields')}
                    return res
                self.processed_date = datetime.now()
                vals = {

                    'name': self.product_id.name,
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.count_number,
                    'product_uom': self.product_id.uom_id.id,
                    'location_id': self.ticl_receipt_summary_id.property_stock_supplier.id,
                    'location_dest_id': self.receiving_location_id.id,
                    'sending_location_id': self.sending_location_id.id,
                    'warehouse_id': self.warehouse_id.id,
                    'receive_date': self.received_date,
                    'processed_date': self.processed_date,
                    'cod_comments': self.cod_comments,
                    'received_date': self.received_date,
                    'serial_number': self.serial_number,
                    'tel_unique_no': self.tel_unique_no,
                    'manufacturer_id': self.manufacturer_id.id,
                    'condition_id': self.condition_id.id,
                    'categ_id': self.tel_type.id,
                    'order_from_receipt': True,
                    'origin': self.ticl_receipt_summary_id.name,
                    'hr_employee_id': self.hr_employee_id.id,
                    'cod_employee_id': self.cod_employee_id.id,
                    'tel_cod' : self.tel_cod,
                    'xl_items' : self.xl_items,
                    'repalletize' : self.repalletize,
                    'tel_note' : self.tel_note,
                    # 'inbound_charges':self.inbound_charges,
                    'cod_charges' : self.cod_charges,
                    'associated_fees':self.associated_fees,
                    'repalletize_charge':self.repalletize_charge,
                    'misc_log_time':self.misc_log_time,
                    'misc_charges':self.misc_charges,

                }
                service = self.env['ticl.service.charge'].search([])
                for service in service:
                    if self.tel_type.name == service.name:
                        vals['monthly_service_charge'] = service.service_price

                picking = self.ticl_receipt_summary_id.create_picking(vals)
                vals.update({
                    'picking_id': picking.id,
                    'picking_type_id': picking.picking_type_id.id,
                })
                move = self.env['stock.move'].create(vals)
                self.ticl_receipt_summary_id.create_mv_line(vals,move,picking)

                summary_line_id = self.env['ticl.receipt.log.summary.line'].search(
                    [('ticl_receipt_summary_id', '=', self.ticl_receipt_summary_id.id),
                     ('tel_unique_no', '=',self.tel_unique_no)])
                summary_line_id.write({'move_to_inv': 'y'})

                lst = []
                picking.with_context({'merge':False}).action_confirm()
                for ids in self.ticl_receipt_summary_id.ticl_receipt_summary_lines:
                    lst.append(ids.move_to_inv)
                if 'n' not in lst:
                    self.ticl_receipt_summary_id.state = 'completed'
                    self.env['ticl.receipt'].search([('name','=',self.ticl_receipt_summary_id.name)]).write({'state':'completed'})
                if self.atm_wrapped:
                    self.state = 'done'
                else:
                    self.hide_mv_inv_button = True 

                #self.state = 'done'
                self.in_inventory = True

            action = self.env.ref('stock.action_picking_tree_all')
            result = action.read()[0]
            result['context'] = {}
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = picking.id
            #picking.action_confirm()
            picking.button_validate()
            # return result

            # Generete Individual PDF Report for Clieck Button
            # return {
            #     'type': 'ir.actions.report',
            #     'report_name': 'ticl_report.individual_report_placards_label',
            #     'report_type': 'qweb-pdf',
            #     'report_file': 'ticl_report.individual_report_placards_label',
            #     'name': 'ticl.receipt.log.summary.line',
            # }


    #Create Unique ID in line items        
    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('ticl.receipt.log.summary.line') or '/'
        vals['tel_unique_no'] = seq
        return super(ticl_receipt_log_summary_line, self).create(vals)


    @api.model
    def import_atm_process_images(self, vals, unsplashurls=None, **kwargs):
        xl = vals.get('file').split(',')
        xlsx_file = xl[1].encode()
        xls_file = base64.decodestring(xlsx_file)
        wb = xlrd.open_workbook(file_contents=xls_file)
        for sheet in wb.sheets():
            for row in range(sheet.nrows):
                if row == 0:
                    continue
                serial_number = sheet.cell(row, 1).value
                atm_links = [sheet.cell(row, 7).value, sheet.cell(row, 8).value, sheet.cell(row, 9).value,
                             sheet.cell(row, 10).value, sheet.cell(row, 11).value]
                self.script_g_api(atm_links, serial_number, 'class_ir_attachments3_rel', 'attachment_id3')
                hdd_links = [sheet.cell(row, 14).value, sheet.cell(row, 15).value]
                self.script_g_api(hdd_links, serial_number, 'class_ir_attachments1_rel', 'attachment_id1')
                epp_links = [sheet.cell(row, 18).value, sheet.cell(row, 19).value]
                self.script_g_api(epp_links, serial_number, 'class_ir_attachments2_rel', 'attachment_id2')

        return {'message': 'Completed', 'status': 's'}

    # def script_g_api(self, atm_links, serial_number, table, field_id):
    #     for i in range(len(atm_links)):
    #         if atm_links[i] == '':
    #             continue
    #         drive_id = atm_links[i].split("id=")
    #         obj = lambda: None
    #         lmao = {"auth_host_name": 'localhost', 'noauth_local_webserver': 'store_true',
    #                 'auth_host_port': [8080, 8090], 'logging_level': 'ERROR'}
    #         for k, v in lmao.items():
    #             setattr(obj, k, v)
    #         # authorization boilerplate code
    #         SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
    #         store = file.Storage('token.json')
    #         creds = store.get()
    #         # The following will give you a link if token.json does not exist, the link allows the user to give this app permission
    #         if not creds or creds.invalid:
    #             flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    #             creds = tools.run_flow(flow, store, obj)
    #         DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    #         # if you get the shareable link, the link contains this id, replace the file_id below
    #         file_id = drive_id[1]
    #         # file_id = '1L78Ni8kWSTriEDSytLj-iiGSPZkOFqUS'
    #         request = DRIVE.files().get_media(fileId=file_id)
    #         # replace the filename and extension in the first field below
    #         name = '{0}_{1}.jpg'.format(serial_number, i)
    #         # name = str(serial_number)+'-'+str(i)+'.jpg'
    #         fh = io.FileIO('Tellerex_Dev/ticl_receiving/static/src/images/{0}'.format(name), mode='w')
    #         downloader = MediaIoBaseDownload(fh, request)
    #         done = False
    #         while done is False:
    #             status, done = downloader.next_chunk()
    #         with open("Tellerex_Dev/ticl_receiving/static/src/images/{0}".format(name), "rb") as imageFile:
    #             str = base64.b64encode(imageFile.read())
    #             photo_0 = str
    #
    #         receipt_log_id = self.env['ticl.receipt.log.summary.line'].search([('serial_number', '=', serial_number)])
    #         if receipt_log_id.atm_cleaned == False:
    #             receipt_log_id.sudo().write({'atm_cleaned': True, 'state': 'photographed'})
    #         attachment_id = self.env['ir.attachment'].sudo().create(
    #             {'mimetype': 'image/jpg', 'name': name, 'datas_fname': name,
    #              'res_model': 'ticl.receipt.log.summary.line',
    #              'res_id': 0, 'datas': photo_0, 'db_datas': photo_0})
    #         self._cr.execute("""
    #                                 INSERT INTO {0} (class_id,
    #                                 {1}) VALUES({2},{3});
    #                             """.format(table, field_id, receipt_log_id.id, attachment_id.id))
    #         os.remove("Tellerex_Dev/ticl_receiving/static/src/images/{0}".format(name))



    def dir_atm_process_images(self, unsplashurls=None, **kwargs):
        print('\n path',os.getcwd(),type(os.getcwd()),os.getcwd()+'/src/user/COD')
        dir = os.listdir(os.getcwd()+'/src/user/COD')
        for folder_name in dir:
            folder = os.listdir(os.getcwd()+'/src/user/COD'+"/{0}".format(folder_name))
            for sub_folder_name in folder:
                sub_folder = folder = os.listdir(os.getcwd()+'/COD'+"/{0}/{1}".format(folder_name,sub_folder_name))
                for file_name in sub_folder:
                    with open(os.getcwd()+'/src/user/COD'+"/{0}/{1}/{2}".format(folder_name,sub_folder_name,file_name), "rb") as imageFile:
                        str = base64.b64encode(imageFile.read())
                        # print('\n\n photo', str[:10])
                        photo_0 = str

                        # print('\n\n photo', photo_0)

                        # resized_images = o_tools.image_get_resized_images(photo_0, return_big=True,
                        #                                                 avoid_resize_medium=True)
                        # image_small = resized_images['image']

                        receipt_log_id = self.env['ticl.receipt.log.summary.line'].search(
                            [('serial_number', '=', folder_name)],limit=1)
                        receipt_log_id.sudo().write({'atm_cleaned':True})
                        if receipt_log_id.id == False:
                            continue
                        if receipt_log_id.atm_cleaned == False:
                            receipt_log_id.sudo().write({'atm_cleaned': True, 'state': 'photographed'})
                        attachment_id = self.env['ir.attachment'].sudo().create(
                            {'mimetype': 'image/jpg', 'name': file_name,
                             'res_model': 'ticl.receipt.log.summary.line',
                             'res_id': 0, 'datas': photo_0, 'checksum': photo_0})
                        if sub_folder_name == "ATM":
                            table = 'class_ir_attachmentsatm_rel'
                            field_id = 'attachment_ids'
                        if sub_folder_name == "HDD":
                            table = 'class_ir_attachmentsepp_rel'
                            field_id = 'attachment_ids_epp'
                        if sub_folder_name == "EPP":
                            table = 'class_ir_attachmentshdd_rel'
                            field_id = 'attachment_ids_hdd'
                        self._cr.execute("""
                                                INSERT INTO {0} (class_id,
                                                {1}) VALUES({2},{3});
                                            """.format(table, field_id, receipt_log_id.id, attachment_id.id))



#Ticl Receipts Payments 
class ticl_receipt_payment_log(models.Model):
    _name = 'ticl.receipt.payment.log'
    _description = "Ticl Receipts Payment"

    name = fields.Text(string='Description')
    ticl_receipt_log_payment_id = fields.Many2one('ticl.receipt.log.summary', string='Receipts Payment ID', invisible=1)
    payment_amount = fields.Char(string='Amount')
    payment_rate = fields.Char(string='Rate')
    ticl_units = fields.Char(string='Units')


# class ir_attachment_manual(models.Model):
#     _inherit = "ir.attachment"

#     image_type_for_cod = fields.Selection(
#         [('ATM', 'ATM'), ('EPP', 'EPP'), ('HDD', 'HDD')],
#         string='Image Type for COD')

    # @api.model
    # def create(self, vals):
    #     if vals.get('res_model') == 'ticl.receipt.log.summary.line':
    #         resized_images = tools.image_get_resized_images(vals.get('datas'), return_big=True,
    #                                                           avoid_resize_medium=True)
    #         datas = resized_images['image']
    #         vals['datas'] = datas
    #     return super(ir_attachment_manual, self).create(vals)
