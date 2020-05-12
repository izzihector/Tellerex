# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import time
from odoo.exceptions import UserError, Warning
import threading
import urllib3
import json
import requests
import logging

_logger = logging.getLogger(__name__)

class ticl_shipment_log(models.Model):
    _name = 'ticl.shipment.log'
    _inherit = ['mail.thread']
    _description = "Shipment Log"
    _order = 'id desc'

    #show bol carrier
    @api.depends('state','echo_call')
    def _is_visiable(self):
        if self.state == 'draft' and self.echo_call == 'no':
            self.show_bol_carr = True
        elif self.state not in ('draft','cancel') and self.echo_call == 'yes':
            self.show_bol_carr = True
        elif self.state not in ('draft','cancel') and self.echo_call == 'no':
            self.show_bol_carr = True
        else:
            self.show_bol_carr = False

    # This function is for Revert Shipment back to draft state
    def revert_shipment(self):
        self.state = 'draft'
        for ids in self.ticl_ship_lines:
            if ids.lot_id.name:
                tel_obj = self.env['stock.move.line']
                product_search = tel_obj.search(
                    [('ticl_warehouse_id', '=', self.sending_location_id.id), ('product_id', '=', ids.product_id.id),
                     ('serial_number', '=', ids.lot_id.name), ('status', '=', 'inventory')])
                if product_search:
                    ids.ship_stock_move_line_id.write({'status': 'assigned','shipment_id': self.name})
                    if ids.status_not_inventory == True :
                        ids.status_not_inventory = False
                else:
                    ids.status_not_inventory = True
            else:
                x = self.env['stock.move.line'].search(
                    [('product_id', '=', ids.product_id.id),('ticl_warehouse_id','=',self.sending_location_id.id),
                     ('status', '=', 'inventory'),('tel_unique_no','!=',False),('condition_id','!=',False)])
                if x.ids == []:
                    ids.status_not_inventory = True
                    # raise UserError('{0} is not available in Inventory.'.format(ids.product_id.name))
                else:
                    ids.status_not_inventory = False
                    ids.ship_stock_move_line_id = x.ids[0]
                    self.env['stock.move'].search([('id','=',x.ids[0])]).write({'status': 'assigned','shipment_id': self.name})

    #Total Pallet Count
    @api.model
    @api.depends('ticl_ship_lines.count_number')
    def count_total_pallet(self):
        pallet_list = []
        other_list = []
        for ship in self.ticl_ship_lines:
            if ship.pallet_id_name:
                pallet_list.append(ship.pallet_id_name.name)
            else:
                other_list.append(ship.id)
        count_pallet = list(set(pallet_list))
        # self.pallet_quantity = len(count_pallet) + len(other_list)
        # self.total_pallet = len(count_pallet) + len(other_list)
        self.update({'total_pallet':len(count_pallet) + len(other_list),'pallet_quantity':len(count_pallet) + len(other_list)})


    #Total Pallet Weight
    @api.depends('ticl_ship_lines.product_weight')
    def count_total_weight(self):  
        for ship in self:      
            total_weight = 0 
            for line in ship.ticl_ship_lines:
                if line.product_weight:
                    total_weight += int(line.product_weight)
                    print("===total_weight==",total_weight)
            ship.update({'total_weight': total_weight })

    #Total Signage
    @api.depends('ticl_ship_lines.count_number','total_signage')
    def count_total_signage(self):  
        for shipment in self:      
            total_signage = 0
            for line in shipment.ticl_ship_lines:
                if line.tel_type.name == 'Signage':
                    total_signage += int(line.count_number)  
            shipment.update({'total_signage': total_signage })

    #Total Accessory
    @api.depends('ticl_ship_lines.count_number','total_accessory')
    def count_total_accessory(self):  
        for shipment in self:      
            total_accessory = 0
            for line in shipment.ticl_ship_lines:
                if line.tel_type.name == 'Accessory':
                    total_accessory += int(line.count_number)  
            shipment.update({'total_accessory': total_accessory })

    
    def _get_origin_location(self):
        for record in self:
            if record.dropship_state == 'yes':
                record.origin_location = record.sending_rigger_id.name
            if record.dropship_state == 'no':
                record.origin_location = record.sending_location_id.name
    # Filter Location Basis of dropship_state
    # @api.onchange('dropship_state')
    # def onchange_product_type(self):
    #     res = {}
    #     if self.dropship_state == 'no':
    #         res['domain']={'sending_location_id':[('is_warehouse', '=', True)],
    #         'receiving_location_id':['|',('is_warehouse', '=', True),('is_rigger', '=', True)]}
    #     else:
    #         res['domain']={'sending_location_id':[('is_rigger', '=', True)],
    #         'receiving_location_id':[('is_rigger', '=', True)]}
    #     return res


    name = fields.Char(string='Shipment Number', index=True )
    pallet_id = fields.Many2many('ticl.shipment',string='Pallet ID',track_visibility='onchange')
    tel_note = fields.Char(string='Comment/Note')
    appointment_date_new = fields.Date(string='Pickup Date',track_visibility='onchange')
    shipment_date = fields.Date(string='Shipped Date')
    delivery_date_new = fields.Date(string='Delivery NEW Date')
    activity_date_new = fields.Date(string='Activity Date')
    delivery_date = fields.Date(string='Delivery Date')
    shipment_status = fields.Char(string="Shipment Status")
    appointment_date = fields.Date(string='Pickup Date',track_visibility='onchange') 
    equipment_date =  fields.Date(string='Equipment Shipping Request Date')
    echo_tracking_id = fields.Char(string="Shipment Id")
    shipment_mode = fields.Selection([('TL', 'TL'),
                                      ('LTL', 'LTL')], string='ShipmentMode')
    shipment_type = fields.Selection([('Regular', 'Regular'),('Inventory Transfer', 'Inventory Transfer'),('Re-Consignment', 'Re-Consignment'),
                                      ('Guaranteed', 'Guaranteed'),('Expedited', 'Expedited'),('Non Freight','Non Freight'),('warehouse_transfer', 'Warehouse Transfer')], string='Shipment Type'
                                      ,default='Regular',track_visibility='onchange')
    old_name = fields.Char(string='Old Shipment Number', index=True )
    total_weight = fields.Char(string="Total Weight", compute='count_total_weight')
    pallet_quantity = fields.Char(string="Pallet Quantity")
    total_echo_cost = fields.Char(string="Total Cost")
    unit_of_weight = fields.Char(string="UnitOfWeight")
    request_pick_date = fields.Date(string='Req PickUP Date')
    request_delivery_date = fields.Date(string='Req Delivery Date')
    estimated_delivery_date = fields.Date(string='Est Delivery Date')
    bill_of_lading_number = fields.Char(string='BOL #',track_visibility='onchange')
    sending_location_id = fields.Many2one('stock.location', string='Origin Location',default='',track_visibility='onchange')
    sending_rigger_id = fields.Many2one('res.partner', string="Origin Location", default='')
    receiving_location_id = fields.Many2one('res.partner', string='Destination Location',default='',track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse', string='warehouse', default=lambda self: self.env.user.warehouse_id.id)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier',track_visibility='onchange')
    asn_bol_type = fields.Selection([('asn', 'ASN'),('bol','BOL')], string='Type', default='bol')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('picked', 'Picked'),
        ('packed', 'Packed'),('shipped', 'Shipped')],
        string='Status', default='draft',track_visibility='onchange')
    dropship_state = fields.Selection([('yes', 'YES'),('no', 'NO')],string='Drop Ship', default='no')
    ticl_ship_lines = fields.One2many('ticl.shipment.log.line', 'ticl_ship_id',track_visibility='onchange')
    ticl_payment_lines = fields.One2many('ticl.shipment.payment', 'ticl_payment_id', ondelete='cascade')
    start_quarantine_date = fields.Date(string='Start Quarantine Date')
    end_quarantine_date = fields.Date(string='End Quarantine Date')
    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier',track_visibility='onchange')
    shipping_carrier_name = fields.Char(string='Shipping Carrier Name')
    pick_up_date = fields.Date(string='Pick up Date')
    accepted_date =  fields.Date(string='Accepted Date')
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    response_message = fields.Char(string='Responce Message') 
    error_code = fields.Char(string='Error Code')   
    error_message = fields.Char(string='Error Message')   
    error_field_name = fields.Char(string='Error Field Name')
    is_error = fields.Boolean(string='Is Error', default=False, copy=False)
    total_pallet = fields.Char(string="Total Pallet", compute='count_total_pallet')
    ship_stock_move = fields.Many2one('stock.move', string="Stock Move")
    ship_stock_move_line = fields.Many2one('stock.move.line', string="Move Line Name")
    tender_stock_move_id = fields.Many2one('ticl.shipment.log.ext', string="Tender Name")
    origin_location = fields.Char(string="Origin Location", compute='_get_origin_location')
    #sending_rigger_id = fields.Many2one('res.partner', string="Origin Location", default='')
    #receiving_rigger_id = fields.Many2one('res.partner', string="Receiving Location", default='')
    total_signage = fields.Char(string='Total Signage', compute='count_total_signage')
    total_accessory = fields.Char(string='Total Accessory', compute='count_total_accessory')
    pallet_id_name_visible = fields.Char(string='Pallet ID',track_visibility='onchange')
    echo_call = fields.Selection([('yes', 'YES'),('no', 'NO')], string='Call Echo(Optional)')
    activity_date =  fields.Date(string='Activity Start Date')
    chase_fright_cost = fields.Float(string='Chase Fright Charge')
    miles = fields.Integer(string='Miles')
    is_validate = fields.Boolean(string='Is Validate', default=False, copy=False)
    is_invoice = fields.Boolean(string='Is Invoice', default=False, copy=False)
    validate_date = fields.Date(string='Validate Date')
    validate_by = fields.Many2one('res.users', string="Validate By")
    pick_name = fields.Char(string="Picking Name")
    approval_authority = fields.Char(string='Approval Authority')
    is_from_inventory = fields.Boolean(string='Is From Inventory', default=False)
    show_bol_carr = fields.Boolean(compute='_is_visiable')
    approved_date = fields.Date(string='Approved date')


    # @api.onchange('shipment_type')
    # def on_change_shipment_type(self):
    #     res = {}
    #     if self.shipment_type == 'warehouse_transfer':
    #         res['domain'] = {'receiving_location_id': [('is_warehouse', '=', True)]}
    #     return res
        
    @api.model
    def unlink(self):
        move_id = self.env['stock.move'].search([('shipment_id', '=', self.name)])
        if move_id:
            for mv in move_id:
                mv.write({'status': 'inventory', 'shipment_id':''})
        return super(ticl_shipment_log, self).unlink()

    # Validate Fright Charge Fucntion
    @api.model
    def validate_fright_charge(self):
        for record in self:
            if not record.approval_authority and record.shipment_type == 'Guaranteed' or record.shipment_type == 'Expedited' or record.shipment_type == 'Re-Consignment':
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
                          'validate_date':fields.Datetime.now(),
                          'validate_by':self.env.user.id})
            self.env['ticl.fright.service.line'].create_detail_mnth_fright_inv(self, 'shipment')

    #Employee Auto Update in
    @api.onchange('user_id')
    def on_change_user(self):
        if not self.user_id:
            return {}
        emp = self.env['hr.employee'].search([('user_id','=',self.user_id.id)])
        self.hr_employee_id = emp

    # @api.onchange('appointment_date_new')
    # def on_change_pickup_date(self):
    #     if self.appointment_date_new:
    #         app_date = str(datetime.strptime(str(self.appointment_date_new),'%Y-%m-%d'))
    #         self.shipment_date = app_date

    #change in warehouse
    # @api.onchange('sending_location_id')
    # def on_change_destination(self):
    #     if self.dropship_state == 'no':
    #         warehouse_id = self.env['stock.warehouse'].search([('name', '=', self.sending_location_id.name )])
    #         self.warehouse_id = warehouse_id.id

            
    #Create method in shipment draft status
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('ticl.shipment.log') or '/'
        vals['name'] = sequence
        if 'ticl_ship_lines' in vals:
            for i in range(len(self.pallet_id.ids), len(vals['ticl_ship_lines'])):
                if vals['ticl_ship_lines'][i][2] != False or '':
                    if 'funding_doc_type' in vals['ticl_ship_lines'][i][2] and 'funding_doc_number' in \
                        vals['ticl_ship_lines'][i][2] and 'ticl_project_id' in vals['ticl_ship_lines'][i][2]:
                        if vals['ticl_ship_lines'][i][2]['funding_doc_type'] == False or vals['ticl_ship_lines'][i][2][
                            'funding_doc_number'] == False or vals['ticl_ship_lines'][i][2]['ticl_project_id'] == False:
                            raise UserError('Please fill the Funding Doc Type, Funding Doc No & Project Id for all Shipment Log lines')
            for i in range(len(vals['ticl_ship_lines'])):
                if 'funding_doc_type' in vals['ticl_ship_lines'][i][2] and 'funding_doc_number' in vals['ticl_ship_lines'][i][2] and 'ticl_project_id' in vals['ticl_ship_lines'][i][2]:
                    if vals['ticl_ship_lines'][i][2]['funding_doc_type'] == False or vals['ticl_ship_lines'][i][2]['funding_doc_number'] == False or vals['ticl_ship_lines'][i][2]['ticl_project_id'] == False:
                        raise UserError('Please fill the Funding Doc Type, Funding Doc No & Project Id for all Shipment Log lines')
        if 'pallet_id' in vals.keys():
            for ids in vals['pallet_id'][0][2]:
                self.env['ticl.shipment'].search([('id', '=', ids)]).write({'state': 'in_ship_log'})
                for j in range(len(vals['ticl_ship_lines'])):
                    vals['ticl_ship_lines'][j][2]['pallet_id_name_visible'] = self.env['ticl.shipment'].search([('id', '=', int(vals['ticl_ship_lines'][j][2]['pallet_id_name']))]).name
        
        if 'ticl_ship_lines' in vals.keys():
            for lines in range(len(vals['ticl_ship_lines'])):
                type_id = self.env['product.category'].search([('id','=',vals['ticl_ship_lines'][lines][2]['tel_type'])])
                condition_id = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
                if type_id.name != 'ATM':
                    if vals['ticl_ship_lines'][lines][2].get('ship_stock_move_line_id',False):
                        x = self.env['stock.move.line'].search(
                            [('id', '=', vals['ticl_ship_lines'][lines][2]['ship_stock_move_line_id'])],limit=1)
                    else:
                        x = self.env['stock.move.line'].search(
                            [('product_id', '=', vals['ticl_ship_lines'][lines][2]['product_id']),
                             ('ticl_warehouse_id', '=', vals['sending_location_id']), 
                             ('status', '=', 'inventory'),
                             ('condition_id','!=',condition_id.id)],limit=1)
                    #x = self.env['stock.move'].search([('product_id','=',vals['ticl_ship_lines'][lines][2]['product_id']),('location_dest_id','=',vals['sending_location_id']),('status','=','inventory')])
                    
                    vals['ticl_ship_lines'][lines][2]['ship_stock_move_line_id'] = x.id
                    move = self.env['stock.move.line'].search([('id','=',x.id)],limit=1)
                    vals['ticl_ship_lines'][lines][2]['state'] = 'draft'
                    vals['ticl_ship_lines'][lines][2]['receipt_id'] = move.origin
                    self.env['stock.move.line'].search(
                        [('id', '=',x.id)]).write(
                        {'status': 'assigned','shipment_id': vals['name']})
                else:
                    if 'ship_stock_move_line_id' in vals['ticl_ship_lines'][lines][2]:
                            self.env['stock.move.line'].search([('id','=',vals['ticl_ship_lines'][lines][2]['ship_stock_move_line_id'])]).write({'status':'assigned','shipment_id': vals['name']})       

                if type_id.name != 'XL' and self.dropship_state == 'no':
                    if type_id.name == 'ATM' and vals['ticl_ship_lines'][lines][2]['lot_id'] == False:
                        product = self.env['product.product'].search([('id','=',vals['ticl_ship_lines'][lines][2]['product_id'])])
                        raise UserError("Please enter Serial Number for the Model ({0})".format(product.name))

        if self.ticl_ship_lines:
            for lines in self.ticl_ship_lines:
                lines.state = self.state
                lines.receipt_id = lines.ship_stock_move_line_id.origin
        res = super(ticl_shipment_log, self).create(vals)
        action = self.env.ref('ticl_shipment.action_ticl_shipment_model')
        # action.sudo().context = {}
        if res.echo_tracking_id is not None:
            prod = res.ticl_ship_lines.filtered(
                lambda z: z.tel_type.name == 'ATM' and z.product_id.ticl_product_id.name != False)

            # if res.shipment_type != 'warehouse_transfer' and res.dropship_state == 'no':
            #     if prod:
            #         stand_lines = res.create_stand(res, prod)
            #         res.ticl_ship_lines = stand_lines
        return res

    #write method in Shipment Log
    def write(self, values):
        if 'ticl_ship_lines' in values.keys():
            for i in range(len(self.pallet_id.ids),len(values['ticl_ship_lines'])):
                if values['ticl_ship_lines'][i][2] != False or '':
                    if 'funding_doc_type' in values['ticl_ship_lines'][i][2] and 'funding_doc_number' in values['ticl_ship_lines'][i][2] and 'ticl_project_id' in values['ticl_ship_lines'][i][2]:
                        if values['ticl_ship_lines'][i][2]['funding_doc_type'] == False or values['ticl_ship_lines'][i][2]['funding_doc_number'] == False or values['ticl_ship_lines'][i][2]['ticl_project_id'] == False:
                            raise UserError('Please fill the Funding Doc Type, Funding Doc No & Project Id for all Shipment Log lines')
        if 'pallet_id' in values.keys():
            uniq_id = [elem for elem in self.pallet_id.ids if elem not in values['pallet_id'][0][2]]
            if len(uniq_id) > 0:
                for ids in uniq_id:
                    self.env['ticl.shipment'].search([('id', '=', ids)]).write({'state': 'draft'})
            for i in range(len(self.pallet_id),len(values['pallet_id'][0][2])):
                self.env['ticl.shipment'].search([('id', '=', values['pallet_id'][0][2][i])]).write({'state': 'in_ship_log'})
                for j in range(len(self.ticl_ship_lines),len(values['ticl_ship_lines'])):
                    values['ticl_ship_lines'][j][2]['pallet_id_name_visible'] = self.env['ticl.shipment'].search([('id', '=', int(values['ticl_ship_lines'][j][2]['pallet_id_name']))]).name
        for record in self:
            if record.ticl_ship_lines:
                for lines in record.ticl_ship_lines:
                    lines.state = record.state
                    lines.receipt_id = lines.ship_stock_move_line_id.origin
        if 'is_invoice' not in values.keys():
            if self.dropship_state == 'no':
                if 'ticl_ship_lines' in values.keys():
                    for lines in range(len(self.ticl_ship_lines),len(values['ticl_ship_lines'])):
                        if values['ticl_ship_lines'][lines][2] !=False:
                            type_id = self.env['product.category'].search(
                                [('id', '=', values['ticl_ship_lines'][lines][2]['tel_type'])])
                            condition_id = self.env['ticl.condition'].search([('name', 'in', ('To Recommend','Quarantine'))])
                            if values['ticl_ship_lines'][lines][2]['ship_stock_move_line_id']:
                                x = self.env['stock.move.line'].search(
                                    [('id', '=', values['ticl_ship_lines'][lines][2]['ship_stock_move_line_id'])])
                                print("===1111111111111======",x)
                            else:
                                x = self.env['stock.move.line'].search(
                                    [('product_id', '=', values['ticl_ship_lines'][lines][2]['product_id']),
                                     ('ticl_warehouse_id', '=', self.sending_location_id.id), ('status', '=', 'inventory'),('condition_id','not in',condition_id.ids)])
                                print("===222222222222222222======",x)
                            # if x.id == False:
                            #     raise UserError("Selected Item is not available in the Inventory")
                            #print("===XXXXXXXXXXXXXXXXX======",x.ids[0])
                            values['ticl_ship_lines'][lines][2]['ship_stock_move_line_id'][0] =x.ids[0]
                            move = self.env['stock.move.line'].search([('id','=',x.ids[0])],limit=1)
                            values['ticl_ship_lines'][lines][2]['state'] = 'draft'
                            values['ticl_ship_lines'][lines][2]['receipt_id'] = move.origin
                            self.env['stock.move.line'].search(
                                [('id', '=', x.ids[0])]).write(
                                {'status': 'assigned','shipment_id':self.name})

        res = super(ticl_shipment_log, self).write(values)
        action = self.env.ref('ticl_shipment.action_ticl_shipment_model')
        # action.sudo().context={}
        return res



    #Onchange Pallet Id in Shipment Log  
    @api.depends('pallet_id')
    @api.onchange('pallet_id')
    def on_change_pallet(self):
        rmv_lines = self.ticl_ship_lines.filtered(lambda x: x.pallet_id_name)
        rmvLst = []
        for rmv_line in rmv_lines:
            if rmv_line.pallet_id_name.id not in self.pallet_id.ids:
                rmvLst.append((2, rmv_line.id))
        self.ticl_ship_lines = rmvLst
        lst = []
        lines =[]
        for x in self.pallet_id:
            ext_lines = self.ticl_ship_lines.filtered(lambda y: y.pallet_id_name.id == y.id)
            if not ext_lines:
                for pal_ids in self.ticl_ship_lines:
                    lines.append(pal_ids.pallet_id_name.id)
                if x.id not in lines:
                    for ids in x.ticl_shipment_lines:
                        ticl_ship_lines = {
                            'pallet_id_name': x.id,
                            'tel_type': ids.tel_type.id,
                            'product_id': ids.product_id.id,
                            'manufacturer_id': ids.manufacturer_id.id,
                            'count_number': ids.count_number,
                            'tel_note': ids.tel_note,
                            'product_weight': ids.product_weight,
                            'ship_stock_move_line_id': ids.stock_move_id.id,
                        }
                        lst.append((0, 0, ticl_ship_lines))
        self.ticl_ship_lines = lst

#Basic RTE3MDU1OTpiMjRmYWRmYS0yNjkwLTQ3NDgtOThjMi1lYWEzNTViNTViMjQ=
#Echo API POST INTEGRATION With Shipment Creations
    def ticl_echo_shipment(self):

        if not self.ticl_ship_lines:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please fill the Shipment line"
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
            
        if self.shipment_type != 'warehouse_transfer':
            if self.echo_tracking_id is not None:
                prod = self.ticl_ship_lines.filtered(
                    lambda z: z.tel_type.name == 'ATM' and z.product_id.ticl_product_id.name != False)
                if prod:
                    stand_lines = self.create_stand(self, prod)
                    if type(stand_lines) == dict:
                        return stand_lines
                    self.ticl_ship_lines = stand_lines
        if self.echo_tracking_id:
            return True
      
        for ids in self.ticl_ship_lines:
            if ids.status_not_inventory == True:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view or False
                context = dict(self._context or {})
                context['message'] = "Please remove the red color items !"
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
            if ids.funding_doc_number == False or '' or ids.funding_doc_type == False or '' or ids.ticl_project_id == False or '':
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view or False
                context = dict(self._context or {})
                context['message'] = "Please fill the Funding Doc Type, Funding Doc No & Project Id for all Shipment Log lines"
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

        if int(self.total_pallet) > 20 and self.echo_call == 'yes':
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "'Pallet Quantity' must be a positive integer. '0' is acceptable. Max value is '12'."
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

        #LTL Shipment Creation API
        if int(self.total_pallet) < 13 and int(self.total_weight) < 20000 and self.echo_call == 'yes':
            print("===LTL===")
            data = {}
            data["Origin"] = {}
            data["Destination"] = {}
            data["Origin"].update({
                "LocationType" : "BUSINESS",
                "LocationName" : self.sending_location_id.name,
                "AppointmentDate" : self.appointment_date_new.strftime('%m/%d/%Y'),
                "AppointmentStart" : self.sending_location_id.warehouse_id.checkin_time or "12:59",
                "AppointmentEnd" : self.sending_location_id.warehouse_id.checkout_time or "13:59",
                "AddressLine1" : self.sending_location_id.warehouse_id.street,
                "AddressLine2" : self.sending_location_id.warehouse_id.street2 or "",
                "City" : self.sending_location_id.warehouse_id.city_id.name or "",
                "StateProvince" : self.sending_location_id.warehouse_id.state_id.code or "",
                "PostalCode" : self.sending_location_id.warehouse_id.zip_code or "",
                "CountryCode" : "US",
                "ContactName" : self.sending_location_id.warehouse_id.contact_name or "",
                "ContactPhone" : self.sending_location_id.warehouse_id.warehouse_phone or "",
                "BolNumber" : self.name,
                "ReferenceNumber" : "00000000",
                "IsBlind": False,
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
                "BlindCity" : "Chicago",
                "BlindStateProvince" : "",
                "BlindPostalCode" : "",
                "BlindCountryCode" : "",
                "Accessorials" : [],                       
            })

            data["Destination"].update({
                "LocationType" : "BUSINESS",
                "LocationName" : self.receiving_location_id.name,
                "AppointmentDate" : self.delivery_date_new.strftime('%m/%d/%Y'),
                "AppointmentStart" : "12:59",
                "AppointmentEnd" : "13:59",
                "AddressLine1" : self.receiving_location_id.street or "",
                "AddressLine2" : self.receiving_location_id.street2 or "",
                "City" : self.receiving_location_id.city_id.name or False,
                "StateProvince" : self.receiving_location_id.state_id.code or "",
                "PostalCode" : self.receiving_location_id.zip or "",
                "ContactName": self.receiving_location_id.contact_name or "",
                "CountryCode" : "US",
                "ContactPhone" : self.receiving_location_id.phone or "",
                "BolNumber" : self.name,
                "ReferenceNumber" : "0000000000",
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
            })

            ticl_lines = []
            for line in self.ticl_ship_lines:
                ticl_lines.append({
                    "ItemId":"",
                    "Description" : line.product_id.categ_id.name,
                    "NmfcClass" : "70",
                    "NmfcNumber" : "116030-09",
                    "Weight" : int(line.product_weight),
                    "PackageType" : "PIECES",
                    "PackageQuantity" : 1,
                    "HandlingUnitType" : "PALLETS",
                    "HandlingUnitQuantity" : 1,
                    "HazardousMaterial" : False
                    })
            data["Items"] = ticl_lines
            #References Fields 
            ticl_references = []
            ticl_references.append({
                    "Name":"Funding Type",  
                    "Value":"CERP"
                    })
            model_inc = []
            serial_inc = []
            num = 0
            for line in self.ticl_ship_lines:
                num = num + 1
                model_inc = "Model Number" + ' ' + str(num)
                serial_inc = "Serial #" + '' + str(num)
                ticl_references.append({
                    "Name" : model_inc,
                    "value" : line.product_id.name,
                    })
                ticl_references.append({
                    "Name" : serial_inc,
                    "value" : line.lot_id.name,
                    })

            line_no = []    
            for line in self.ticl_ship_lines:
                line_search = self.env['ticl.shipment.log.line'].search([('ticl_ship_id','=',self.id)], limit=1)
                print("==line_search===",line_search)
                line_no = line_search.funding_doc_number
            ticl_references.append({
                    "Name":"Work Order #",  
                    "Value":line_no
                    })

            data.update({
                    "PalletType" : "CORRUGATED",
                    "PalletQuantity" : self.total_pallet,
                    "PalletType" : "CORRUGATED",
                    "PalletStackable" : False,
                    "SkidSpotQuantity" : 1,
                    "UnitOfWeight" : "LB",
                    "CustomerNotes" : self.tel_note or "",
                    "ShipmentNotes" : self.tel_note or "",
                    "CarrierSCAC" : "HMES",
                    "CarrierGuarantee" : "G5PM",
                    "QuoteId" : "",
                    "BolNumber" : self.name,
                    "OrderNumber" : "",
                    "PoNumber" : self.name,
                    "ProNumber" : "",
                    "PodSignature" : "",
                    "GlCode" : "",
                    "AckNotification" : "ssingh@delaplex.in;",
                    "AsnNotification" : "ssingh@delaplex.in;",
                    "References" : ticl_references
                }) 

            double_quote_data = json.dumps(data)
            print("====double_quote_data===",double_quote_data)
            # Echo Connection
            warning_message = ""
            url = "https://restapi.echo.com/v2/Shipments/LTL"
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            if not autontication_key:
                raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
            if autontication_key:
                headers = {
                            'Content-Type': 'application/json',
                            'Authorization': autontication_key,
                        }
                try:
                    request1 = requests.post(url, data=double_quote_data, headers=headers)
                    request_data = request1.json()
                    #Responce Update in Odoo
                    if str(request1) != "<Response [200]>" or str(request1) == "<Response [400]>":
                        response_message = False
                        error_code = False
                        error_message = False
                        error_field_name = False
                        if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message'):
                            response_message = request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message')                
                            if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Errors') and request_data.get('ResponseStatus').get('Errors')[0]:
                                if request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode'):
                                    error_code = request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode')
                                    warning_message += 'Error Code : ' + request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('FieldName'):
                                    error_field_name = request_data.get('ResponseStatus').get('Errors')[0].get('FieldName')
                                    warning_message += 'Field Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('FieldName') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('Message'):
                                    error_message = request_data.get('ResponseStatus').get('Errors')[0].get('Message')
                                    warning_message += 'Message Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('Message') + '\n'

                            self.update({
                                    'error_code' : error_code, 
                                    'error_field_name' : error_field_name, 
                                    'error_message' : error_message, 
                                    'response_message' : response_message, 
                                    'echo_tracking_id' : "",
                                    'shipment_mode' : "",
                                    'is_error' : True,
                                })

                    if str(request1) == "<Response [200]>": 
                        if request_data and request_data.get('ShipmentId') and request_data.get('ShipmentMode'):
                            self.write({
                                'echo_tracking_id' : request_data.get('ShipmentId'),
                                'shipment_mode' : request_data.get('ShipmentMode'),
                                'error_code' : "", 
                                'error_field_name' : "", 
                                'error_message' : "", 
                                'response_message' : "",
                                'is_error' : False,
                            })
                            #Status Update
                            if self.dropship_state == 'no':
                                if len(self.ticl_ship_lines) == 0:
                                    raise Warning(_('You can not shipped shipment without inventory lines.'))
                                self.state = 'picked'

                                for ticl in self.ticl_ship_lines:
                                    if ticl.ship_stock_move_line_id:
                                        ticl.ship_stock_move_line_id.write({'status' : self.state,'shipment_id':self.name})

                                # if self.tender_stock_move_id:
                                #     self.tender_stock_move_id.write({'state' : self.state,'echo_tracking_id' : self.echo_tracking_id})

                                # for ticl in self.ticl_ship_lines:
                                #     if ticl.serial_number:
                                #         tel_obj = self.env['stock.move']
                                #         product_search = tel_obj.search([('serial_number', '=', ticl.serial_number),('warehouse_id', '=', self.warehouse_id.id),('status', '=', 'inventory'),('product_id', '=', ticl.product_id.id)])
                                #         if product_search.product_id.id == ticl.product_id.id:
                                #             product_search.write({'status' : 'picked'})
                                #     else:
                                #         tel_obj = self.env['stock.move']
                                #         product_search = tel_obj.search([('status', '=', 'inventory'),('product_id', '=', ticl.product_id.id),('warehouse_id', '=', self.warehouse_id.id)], limit=1)
                                #         if product_search.product_id.id == ticl.product_id.id:
                                #             product_search.write({'status' : 'picked'})
                            else:
                                if len(self.ticl_ship_lines) == 0:
                                    raise Warning(_('You can not shipped shipment without inventory lines.'))
                                for ticl in self.ticl_ship_lines:
                                    if ticl.ship_stock_move_line_id:
                                        ticl.ship_stock_move_line_id.write({'status' : self.state,'shipment_id':self.name})
                                self.state = 'picked'

                            # if self.shipment_type != 'warehouse_transfer':
                            #     if self.echo_tracking_id is not None:
                            #         prod = self.ticl_ship_lines.filtered(lambda z: z.tel_type.name == 'ATM' and z.product_id.ticl_product_id.name != False)
                            #         if prod:
                            #             stand_lines = self.create_stand(self,prod)
                            #             if type(stand_lines) == dict:
                            #                 return stand_lines
                            #             self.ticl_ship_lines = stand_lines

                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                    #_logger.exception('Echo connection failed')
                if self.is_error:
                    # Raise Error in Odoo Pop up.
                    raise Warning(_(warning_message))

        #TL shipment Creation API
        elif ((int(self.total_pallet) > 12) and (int(self.total_pallet) < 21) and self.echo_call == 'yes') or ((int(self.total_weight) > 19999) and (int(self.total_weight) < 45001) and self.echo_call == 'yes'):
        #elif (int(self.total_pallet) > 12 and int(self.total_pallet) < 21) or (int(self.total_weight) > 19999 and int(self.total_weight) < 45001) and self.echo_call == 'yes':            
            print("===TL=====")
            data = {}
            ticl_tl = [{
                "LocationType" : "BUSINESS",
                "LocationName" : self.sending_location_id.name or False,
                "AppointmentDate" : self.appointment_date_new.strftime('%m/%d/%Y') or False,
                "AppointmentStart" : self.sending_location_id.warehouse_id.checkin_time or "12:59",
                "AppointmentEnd" : self.sending_location_id.warehouse_id.checkout_time or "13:59",
                "AddressLine1" : self.sending_location_id.warehouse_id.street or "",
                "AddressLine2" : self.sending_location_id.warehouse_id.street2 or "",
                "City" : self.sending_location_id.warehouse_id.city_id.name or "",
                "StateProvince" : self.sending_location_id.warehouse_id.state_id.code or "",
                "PostalCode" : self.sending_location_id.warehouse_id.zip_code or "",
                "CountryCode" : "US",
                "IsBlind": False,
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
                "BlindCity" : "BLCITY",
                "BlindStateProvince" : "",
                "BlindPostalCode" : "",
                "BlindCountryCode" : "",
                "Accessorials" : [],
                "ContactName" : self.sending_location_id.warehouse_id.contact_name or "",
                "ContactPhone" : self.sending_location_id.warehouse_id.warehouse_phone or "",
                "BolNumber" : self.name,
                "ReferenceNumber" : "00000000",
                "StopType" : "PICK",
                "StopNumber" : 1
                },
                {
                  "LocationType" : "CONSTRUCTIONSITE",
                  "LocationName" : self.receiving_location_id.name or "",
                  "AppointmentDate" : self.delivery_date_new.strftime('%m/%d/%Y') or "",
                  "AppointmentStart" : "12:59",
                  "AppointmentEnd" : "13:59",
                  "AddressLine1" : self.receiving_location_id.street or "",
                  "AddressLine2" : self.receiving_location_id.street2 or "",
                  "City" : self.receiving_location_id.city_id.name or False,
                  "StateProvince" : self.receiving_location_id.state_id.code or False,
                  "PostalCode" : self.receiving_location_id.zip or False,
                  "CountryCode" : "US",
                  "Accessorials" : ["INSIDEDELIVERY", "LIFTGATEREQUIRED", "NOTIFYPRIORTODELIVERY"],
                  "ContactName" : self.receiving_location_id.contact_name or "",
                  "ContactPhone" : self.receiving_location_id.phone or False,
                  "BolNumber" : self.name,
                  "ReferenceNumber" : "00000000",
                  "IsBlind": False,
                  "BlindLocationName" : "",
                  "BlindAddressLine1" : "",
                  "BlindAddressLine2" : "",
                  "BlindCity" : "BLCITY",
                  "BlindStateProvince" : "",
                  "BlindPostalCode" : "",
                  "BlindCountryCode" : "",
                  "StopType" : "DROP",
                  "StopNumber" : 2
                }]
            data["Stops"] = ticl_tl

            ticl_lines = []
            for line in self.ticl_ship_lines:
                ticl_lines.append({
                      "ItemId" : "",
                      "Description" : line.product_id.categ_id.name or False,
                      "NmfcClass" : "70",
                      "NmfcNumber" : "116030-09",
                      "Weight" : int(line.product_id.product_weight) or "",
                      "PackageType" : "PIECES",
                      "PackageQuantity" : 1,
                      "HandlingUnitType" : "PALLETS",
                      "HandlingUnitQuantity" : 1,
                      "HazardousMaterial" : False,
                      "StopPickNumber" : 1,
                      "StopDropNumber" : 2
                    })
            data["Items"] = ticl_lines
            #References Fields 
            ticl_references = []
            ticl_references.append({
                    "Name":"Funding Type",  
                    "Value":"CERP"
                    })

            model_inc = []
            serial_inc = []
            num = 0
            for line in self.ticl_ship_lines:
                num = num + 1
                model_inc = "Model Number" + ' ' + str(num)
                serial_inc = "Serial #" + '' + str(num)
                ticl_references.append({
                    "Name" : model_inc,
                    "value" : line.product_id.name,
                    })
                ticl_references.append({
                    "Name" : serial_inc,
                    "value" : line.lot_id.name,
                    })

            line_no = []    
            for line in self.ticl_ship_lines:
                line_search = self.env['ticl.shipment.log.line'].search([('ticl_ship_id','=',self.id)], limit=1)
                print("==line_search===",line_search)
                line_no = line_search.funding_doc_number
            ticl_references.append({
                    "Name":"Work Order #",  
                    "Value":line_no
                    })

            data.update({
                  "CubicSize" : 10,
                  "UnitOfWeight" : "LB",
                  "CustomerNotes" : self.tel_note or "",
                  "ShipmentNotes" : self.tel_note or "",
                  "EquipmentMinTemp" : "",
                  "EquipmentMaxTemp" : "",
                  "EquipmentTypes" : ["FLATBED48", "FLATBED53"],
                  "EquipmentAccessorials" : ["TEAMSERVICES", "PALLETEXCHANGE"],
                  "EquipmentTarps" : ["T4"],
                  "EquipmentNotes" : "TestEquipmentNotes11/18/2015",
                  "BolNumber" : self.name,
                  "OrderNumber" : " ",
                  "PoNumber" : self.name,
                  "ProNumber" : "",
                  "PodSignature" : "",
                  "GlCode" : " ",
                  "AckNotification" : "ssingh@delaplex.in;",
                  "AsnNotification" : "ssingh@delaplex.in;",
                  "References" : ticl_references
                })

            double_quote_data = json.dumps(data)
            # Echo TL Connection
            warning_message = ""
            url = "https://restapi.echo.com/v2/Shipments/TL"
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            if not autontication_key:
                raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
            if autontication_key:
                headers = {
                            'Content-Type': 'application/json',
                            'Authorization': autontication_key,
                        }
                try:
                    request1 = requests.post(url, data=double_quote_data, headers=headers)
                    request_data = request1.json()        
                    #Responce Update in Odoo
                    if str(request1) != "<Response [200]>" or str(request1) == "<Response [400]>":
                        response_message = False
                        error_code = False
                        error_message = False
                        error_field_name = False
                        if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message'):
                            response_message = request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message')                
                            if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Errors') and request_data.get('ResponseStatus').get('Errors')[0]:
                                if request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode'):
                                    error_code = request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode')
                                    warning_message += 'Error Code : ' + request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('FieldName'):
                                    error_field_name = request_data.get('ResponseStatus').get('Errors')[0].get('FieldName')
                                    warning_message += 'Field Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('FieldName') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('Message'):
                                    error_message = request_data.get('ResponseStatus').get('Errors')[0].get('Message')
                                    warning_message += 'Message Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('Message') + '\n'

                            self.update({
                                    'error_code' : error_code, 
                                    'error_field_name' : error_field_name, 
                                    'error_message' : error_message, 
                                    'response_message' : response_message, 
                                    'echo_tracking_id' : "",
                                    'shipment_mode' : "",
                                    'is_error' : True,
                                })

                    if str(request1) == "<Response [200]>": 
                        if request_data and request_data.get('ShipmentId') and request_data.get('ShipmentMode'):
                            self.write({
                                'echo_tracking_id' : request_data.get('ShipmentId'),
                                'shipment_mode' : request_data.get('ShipmentMode'),
                                'error_code' : "", 
                                'error_field_name' : "", 
                                'error_message' : "", 
                                'response_message' : "",
                                'is_error' : False,
                            })
                            #Status Update
                            if self.dropship_state == 'no':
                                if len(self.ticl_ship_lines) == 0:
                                    raise Warning(_('You can not shipped shipment without inventory lines.'))
                                self.state = 'picked'

                                for ticl in self.ticl_ship_lines:
                                    if ticl.ship_stock_move_line_id:
                                        ticl.ship_stock_move_line_id.write({'status' : self.state,'shipment_id': self.name})

                            else:
                                if len(self.ticl_ship_lines) == 0:
                                    raise Warning(_('You can not shipped shipment without inventory lines.'))
                                self.state = 'picked'

                            # if self.shipment_type != 'warehouse_transfer':
                            #     if self.echo_tracking_id is not None:
                            #         prod = self.ticl_ship_lines.filtered(lambda z: z.tel_type.name == 'ATM' and z.product_id.ticl_product_id.name != False)
                            #         if prod:
                            #             stand_lines = self.create_stand(self,prod)
                            #             if type(stand_lines) == dict:
                            #                 return stand_lines
                            #             self.ticl_ship_lines = stand_lines

                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                   # _logger.exception('Echo connection failed')
                # Raise Error in Odoo Pop up.
                if self.is_error:
                    raise Warning(_(warning_message))

        elif self.echo_call == 'no':
            self.state = 'picked'
            for ticl in self.ticl_ship_lines:
                if ticl.ship_stock_move_line_id:
                    ticl.ship_stock_move_line_id.write({'status' : "picked",'shipment_id':self.name})
                else:
                    tel_obj = self.env['stock.move']
                    product_search = tel_obj.search([('status', 'in', ('picked', 'packed', 'shipped')),('product_id', '=', ticl.product_id.id),('location_dest_id', '=', self.sending_location_id.id)], limit=1)
                    if product_search:
                        product_search.write({'status' : 'picked','shipment_id':self.name})

                # if self.shipment_type != 'warehouse_transfer':
                #     if self.echo_tracking_id is not None:
                #         prod = self.ticl_ship_lines.filtered(lambda z: z.tel_type.name == 'ATM' and z.product_id.ticl_product_id.name != False)
                #         if prod:
                #             stand_lines = self.create_stand(self,prod)
                #             if type(stand_lines) == dict:
                #                 return stand_lines
                #             self.ticl_ship_lines = stand_lines
                # self.state = 'picked'

            if ids.status_not_inventory == True:
                raise UserError("Please Delete the Red Item first")

        else:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view  or False
            context = dict(self._context or {})
            context['message']="Please check this shipment is above TL capacity 45000LB"
            return{
                 'name':'Warning',
                 'type':'ir.actions.act_window',
                 'view_type':'form',
                 'view_mode':'form',
                 'res_model':'sh.message.wizard',
                 'view':[('view','form')],
                 'target':'new',
                 'context' : context,
            }

    #wizard stand for stand
    def exception_wizard_stand(self, message):
        context = dict(self._context or {})
        context['message'] = message
        return {
            'name': 'Stand not Available',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stand.not.available',
            'view': [('view', 'form')],
            'target': 'new',
            'context': context,
        }

    #Create Stand for ATM        
    def create_stand(self, obj, lines):
        pr_list = []
        custom_list = []
        byepass_stand = True
        condition_id = self.env['ticl.condition'].search([('name', '=', 'New')])
        stand_line =  []
        rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound per ATM / Pallet')])
        outbound_charges = rec_log.shipment_service_charges
        for ticl in lines:
            loc_id = self.sending_location_id.id
            if loc_id is False and self.receiving_location_id.id is False:
                loc_id = ticl.ticl_ship_id.receiving_location_id.id
            move_id = self.env['stock.move.line'].search([('product_id', '=', ticl.product_id.ticl_product_id.id),('ticl_warehouse_id','=',loc_id),('status','=','inventory')])
            if not move_id:
                pr_list.append(ticl.product_id.name)
            elif move_id:
                product_id = self.env['product.product'].search([('name', '=', ticl.product_id.ticl_product_id.name)])
                vals = {
                    'tel_type': product_id.categ_id.id,
                    'product_id': product_id.id,
                    'count_number': 1,
                    'manufacturer_id': product_id.manufacturer_id.id,
                    'condition_id': condition_id.id,
                    'xl_items': 'n',
                    'product_weight': product_id.product_weight,
                    'funding_doc_type': ticl.funding_doc_type,
                    'funding_doc_number': ticl.funding_doc_number,
                    'ticl_project_id': ticl.ticl_project_id,
                    'common_name': ticl.common_name,
                    'outbound_charges': outbound_charges,
                    'tid': ticl.tid,
                    'ship_stock_move_line_id': move_id.ids[0],
                }
                stand_line.append((0, 0, vals))
                move_id[0].write({'status': 'assigned', 'shipment_id': self.name})
                custom_list.append(move_id[0].id)
        pr_list = list(set(pr_list))
        if pr_list != []:
            if 'byepass' not in dict(self._context):
                byepass_stand = False
                move_ids = self.env['stock.move.line'].browse(custom_list)
                move_ids.write({'status':'inventory','shipment_id': ''})
        if 'byepass' in dict(self._context) or byepass_stand == True:
            return stand_line
        return self.exception_wizard_stand("<b>Stand for {0} is not available in the inventory!</b><br/> Do you want to Continue?".format(pr_list))


#Echo API POST INTEGRATION With Shipment Creations With Dropship
    #@api.model
    def ticl_echo_rigger_shipment(self):
        if int(self.total_pallet) < 13 and int(self.total_weight) < 20000 and self.echo_call == 'yes':
            print("===LTL===")
            data = {}
            data["Origin"] = {}
            data["Destination"] = {}
            data["Origin"].update({
                "LocationType" : "BUSINESS",
                "LocationName" : self.sending_location_id.name,
                "AppointmentDate" : self.appointment_date_new.strftime('%m/%d/%Y'),
                "AppointmentStart" : self.sending_location_id.checkin_time or "08:00",
                "AppointmentEnd" : self.sending_location_id.checkout_time or "17:00",
                "AddressLine1" : self.sending_location_id.street,
                "AddressLine2" : self.sending_location_id.street2 or "",
                "City" : self.sending_location_id.city.name or "",
                "StateProvince" : self.sending_location_id.state.code or "",
                "PostalCode" : self.sending_location_id.zip or "",
                "CountryCode" : "US",
                "ContactName" : self.sending_location_id.contact_name or "",
                "ContactPhone" : self.sending_location_id.phone or "",
                "BolNumber" : "0000000000",
                "ReferenceNumber" : "0000000000",
                "IsBlind": False,
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
                "BlindCity" : "Chicago",
                "BlindStateProvince" : "",
                "BlindPostalCode" : "",
                "BlindCountryCode" : "",
                "Accessorials" : ["LIFTGATEREQUIRED", "INSIDEPICKUP", "HAZARDOUSMATERIALS", "LIMITEDACCESSFEE", "SINGLESHIPMENT", "PROTECTFROMFREEZING", "EXTREMELENGTH"],                       
            })

            data["Destination"].update({
                "LocationType" : "BUSINESS",
                "LocationName" : self.receiving_location_id.name,
                "AppointmentDate" : self.appointment_date_new.strftime('%m/%d/%Y'),
                "AppointmentStart" : self.receiving_location_id.checkin_time or "08:00",
                "AppointmentEnd" : self.receiving_location_id.checkout_time or "17:00",
                "AddressLine1" : self.receiving_location_id.street or "",
                "AddressLine2" : self.receiving_location_id.street2 or "",
                "City" : self.receiving_location_id.city.name or False,
                "StateProvince" : self.receiving_location_id.state.code or "",
                "PostalCode" : self.receiving_location_id.zip or "",
                "ContactName": self.receiving_location_id.contact_name or "",
                "CountryCode" : "US",
                "ContactPhone" : self.receiving_location_id.phone or "",
                "BolNumber" : self.name,
                "ReferenceNumber" : "0000000000",
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
            })

            ticl_lines = []
            for line in self.ticl_ship_lines:
                ticl_lines.append({
                    "ItemId":"",
                    "Description" : line.product_id.name or False,
                    "NmfcClass" : "50",
                    "NmfcNumber" : "100240-07",
                    "Weight" : int(line.product_weight) or False,
                    "PackageType" : "PIECES",
                    "PackageQuantity" : 1,
                    "HandlingUnitType" : "PALLETS",
                    "HandlingUnitQuantity" : 1,
                    "HazardousMaterial" : 'False'
                    })
            data["Items"] = ticl_lines
            #References Fields 
            ticl_references = []
            ticl_references.append({
                    "Name":"Funding Type",  
                    "Value":"CERP"
                    })
            model_inc = []
            serial_inc = []
            num = 0
            for line in self.ticl_ship_lines:
                num = num + 1
                model_inc = "Model Number" + ' ' + str(num)
                serial_inc = "Serial #" + '' + str(num)
                ticl_references.append({
                    "Name" : model_inc,
                    "value" : line.product_id.name,
                    })
                ticl_references.append({
                    "Name" : serial_inc,
                    "value" : line.lot_id.name,
                    })

            data.update({
                    "PalletType" : "CORRUGATED",
                    "PalletQuantity" : 1,
                    "PalletType" : "CORRUGATED",
                    "PalletStackable" : False,
                    "SkidSpotQuantity" : 1,
                    "UnitOfWeight" : "LB",
                    "CustomerNotes" : self.tel_note or "",
                    "ShipmentNotes" : self.tel_note or "",
                    "CarrierSCAC" : "HMES",
                    "CarrierGuarantee" : "G5PM",
                    "QuoteId" : "",
                    "BolNumber" : self.name,
                    "OrderNumber" : "",
                    "PoNumber" : self.name,
                    "ProNumber" : "",
                    "PodSignature" : "",
                    "GlCode" : "",
                    "AckNotification" : "ssingh@delaplex.com;",
                    "AsnNotification" : "ssingh@delaplex.com;",
                    "References" : ticl_references
                }) 

            double_quote_data = json.dumps(data)
            print("====double_quote_data====",double_quote_data)
            # Echo Connection
            warning_message = ""
            url = "https://restapi.echo.com/v2/Shipments/LTL"
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            if not autontication_key:
                raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
            if autontication_key:
                headers = {
                            'Content-Type': 'application/json',
                            'Authorization': autontication_key,
                        }
                try:
                    request1 = requests.post(url, data=double_quote_data, headers=headers)
                    request_data = request1.json()
                    #Responce Update in Odoo
                    if str(request1) != "<Response [200]>" or str(request1) == "<Response [400]>":
                        response_message = False
                        error_code = False
                        error_message = False
                        error_field_name = False
                        if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message'):
                            response_message = request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message')                
                            if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Errors') and request_data.get('ResponseStatus').get('Errors')[0]:
                                if request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode'):
                                    error_code = request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode')
                                    warning_message += 'Error Code : ' + request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('FieldName'):
                                    error_field_name = request_data.get('ResponseStatus').get('Errors')[0].get('FieldName')
                                    warning_message += 'Field Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('FieldName') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('Message'):
                                    error_message = request_data.get('ResponseStatus').get('Errors')[0].get('Message')
                                    warning_message += 'Message Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('Message') + '\n'

                            self.update({
                                    'error_code' : error_code, 
                                    'error_field_name' : error_field_name, 
                                    'error_message' : error_message, 
                                    'response_message' : response_message, 
                                    'echo_tracking_id' : "",
                                    'shipment_mode' : "",
                                    'is_error' : True,
                                })

                    if str(request1) == "<Response [200]>": 
                        if request_data and request_data.get('ShipmentId') and request_data.get('ShipmentMode'):
                            self.write({
                                'echo_tracking_id' : request_data.get('ShipmentId'),
                                'shipment_mode' : request_data.get('ShipmentMode'),
                                'error_code' : "", 
                                'error_field_name' : "", 
                                'error_message' : "", 
                                'response_message' : "",
                                'is_error' : False,
                            })
                            self.state = 'picked'
                            if len(self.ticl_ship_lines) == 0:
                                raise Warning(_('You can not shipped shipment without inventory lines.'))


                            if self.echo_tracking_id is not None:
                                for ticl in self.ticl_ship_lines:
                                    product_id = self.env['product.product'].search([('name', '=', 'Stand')])
                                    condition_id = self.env['ticl.condition'].search([('name', '=', 'Factory Sealed')])
                                    if ticl.tel_type.name == 'ATM' and ticl.manufacturer_id.name == 'NCR' and (ticl.product_id.name =='6634' or ticl.product_id.name =='2045'):
                                        self.env['ticl.shipment.log.line'].create({
                                            'ticl_ship_id' : self.id,
                                            'tel_type': product_id.categ_id.id,
                                            'product_id': product_id.id,
                                            'count_number' : 1,      
                                            'manufacturer_id': product_id.manufacturer_id.id,
                                            'condition_id': condition_id.id,
                                            'xl_items': 'n'
                                            })

                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                if self.is_error:
                    raise Warning(_(warning_message))
        #Rigger TL Shipment Process
        elif int(self.total_pallet) < 13 and int(self.total_weight) > 19999 and int(self.total_weight) < 45001 and self.echo_call == 'yes':
            print("===TL=====")
            data = {}
            ticl_tl = [{
                "LocationType" : "BUSINESS",
                "LocationName" : self.sending_location_id.name or False,
                "AppointmentDate" : self.appointment_date_new.strftime('%m/%d/%Y') or False,
                "AppointmentStart" : self.sending_location_id.checkin_time or "08:00",
                "AppointmentEnd" : self.sending_location_id.checkout_time or "17:00",
                "AddressLine1" : self.sending_location_id.street or "",
                "AddressLine2" : self.sending_location_id.street2 or "",
                "City" : self.sending_location_id.city.name or "",
                "StateProvince" : self.sending_location_id.state.code or "",
                "PostalCode" : self.sending_location_id.zip or "",
                "CountryCode" : "US",
                "IsBlind": False,
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
                "BlindCity" : "BLCITY",
                "BlindStateProvince" : "",
                "BlindPostalCode" : "",
                "BlindCountryCode" : "US",
                "Accessorials" : ["INSIDEPICKUP", "HAZARDOUSMATERIALS",  "LIFTGATEREQUIRED", "SINGLESHIPMENT"],
                "ContactName" : self.sending_location_id.company_name or "Contact Name",
                "ContactPhone" : self.sending_location_id.phone or "",
                "BolNumber" : self.name,
                "ReferenceNumber" : "00000000",
                "StopType" : "PICK",
                "StopNumber" : 1
                },
                {
                  "LocationType" : "CONSTRUCTIONSITE",
                  "LocationName" : self.receiving_location_id.name or "",
                  "AppointmentDate" : self.appointment_date_new.strftime('%m/%d/%Y') or "",
                  "AppointmentStart" : self.receiving_location_id.checkin_time or "08:00",
                  "AppointmentEnd" : self.receiving_location_id.checkout_time or "17:00",
                  "AddressLine1" : self.receiving_location_id.street or "",
                  "AddressLine2" : self.receiving_location_id.street2 or "",
                  "City" : self.receiving_location_id.city.name or "",
                  "StateProvince" : self.receiving_location_id.state.code or "",
                  "PostalCode" : self.receiving_location_id.zip or "",
                  "CountryCode" : "US",
                  "Accessorials" : ["INSIDEDELIVERY", "LIFTGATEREQUIRED", "NOTIFYPRIORTODELIVERY"],
                  "ContactName" : self.receiving_location_id.company_name or "Contact Name",
                  "ContactPhone" : self.receiving_location_id.phone or False,
                  "BolNumber" : self.name,
                  "ReferenceNumber" : "00000000",
                  "IsBlind": False,
                  "BlindLocationName" : "",
                  "BlindAddressLine1" : "",
                  "BlindAddressLine2" : "",
                  "BlindCity" : "BLCITY",
                  "BlindStateProvince" : "",
                  "BlindPostalCode" : "",
                  "BlindCountryCode" : "US",
                  "StopType" : "DROP",
                  "StopNumber" : 2
                }]
            data["Stops"] = ticl_tl

            ticl_lines = []
            for line in self.ticl_ship_lines:
                ticl_lines.append({
                      "ItemId" : "",
                      "Description" : line.product_id.name or False,
                      "NmfcClass" : "70",
                      "NmfcNumber" : "116030-09",
                      "Weight" : int(line.product_weight) or False,
                      "PackageType" : "PIECES",
                      "PackageQuantity" : 7,
                      "HandlingUnitType" : "PALLETS",
                      "HandlingUnitQuantity" : 8,
                      "HazardousMaterial" : True,
                      "StopPickNumber" : 1,
                      "StopDropNumber" : 2
                    })
            data["Items"] = ticl_lines
            #References Fields 
            ticl_references = []
            ticl_references.append({
                    "Name":"Funding Type",  
                    "Value":"CERP"
                    })
            model_inc = []
            serial_inc = []
            num = 0
            for line in self.ticl_ship_lines:
                num = num + 1
                model_inc = "Model Number" + ' ' + str(num)
                serial_inc = "Serial #" + '' + str(num)
                ticl_references.append({
                    "Name" : model_inc,
                    "value" : line.product_id.name,
                    })
                ticl_references.append({
                    "Name" : serial_inc,
                    "value" : line.lot_id.name,
                    })

            data.update({
                  "CubicSize" : 10,
                  "UnitOfWeight" : "LB",
                  "CustomerNotes" : self.tel_note or "",
                  "ShipmentNotes" : self.tel_note or "",
                  "EquipmentMinTemp" : " ",
                  "EquipmentMaxTemp" : " ",
                  "EquipmentTypes" : ["FLATBED48", "FLATBED53"],
                  "EquipmentAccessorials" : ["TEAMSERVICES", "PALLETEXCHANGE"],
                  "EquipmentTarps" : ["T4"],
                  "EquipmentNotes" : "TestEquipmentNotes11/18/2015",
                  "BolNumber" : self.name,
                  "OrderNumber" : "",
                  "PoNumber" : self.name,
                  "ProNumber" : "",
                  "PodSignature" : "",
                  "GlCode" : " ",
                  "AckNotification" : "ssingh@delaplex.com;",
                  "AsnNotification" : "ssingh@delaplex.com;",
                  "References" :ticl_references
                })

            double_quote_data = json.dumps(data)
            # Echo TL Connection
            warning_message = ""
            url = "https://restapi.echo.com/v2/Shipments/TL"
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            if not autontication_key:
                raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
            if autontication_key:
                headers = {
                            'Content-Type': 'application/json',
                            'Authorization': autontication_key,
                        }
                try:
                    request1 = requests.post(url, data=double_quote_data, headers=headers)
                    request_data = request1.json()        
                    #Responce Update in Odoo
                    if str(request1) != "<Response [200]>" or str(request1) == "<Response [400]>":
                        response_message = False
                        error_code = False
                        error_message = False
                        error_field_name = False
                        if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message'):
                            response_message = request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Message')                
                            if request_data.get('ResponseStatus') and request_data.get('ResponseStatus').get('Errors') and request_data.get('ResponseStatus').get('Errors')[0]:
                                if request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode'):
                                    error_code = request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode')
                                    warning_message += 'Error Code : ' + request_data.get('ResponseStatus').get('Errors')[0].get('ErrorCode') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('FieldName'):
                                    error_field_name = request_data.get('ResponseStatus').get('Errors')[0].get('FieldName')
                                    warning_message += 'Field Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('FieldName') + '\n'
                                if request_data.get('ResponseStatus').get('Errors')[0].get('Message'):
                                    error_message = request_data.get('ResponseStatus').get('Errors')[0].get('Message')
                                    warning_message += 'Message Name : ' + request_data.get('ResponseStatus').get('Errors')[0].get('Message') + '\n'

                            self.update({
                                    'error_code' : error_code, 
                                    'error_field_name' : error_field_name, 
                                    'error_message' : error_message, 
                                    'response_message' : response_message, 
                                    'echo_tracking_id' : "",
                                    'shipment_mode' : "",
                                    'is_error' : True,
                                })

                    if str(request1) == "<Response [200]>": 
                        if request_data and request_data.get('ShipmentId') and request_data.get('ShipmentMode'):
                            self.write({
                                'echo_tracking_id' : request_data.get('ShipmentId'),
                                'shipment_mode' : request_data.get('ShipmentMode'),
                                'error_code' : "", 
                                'error_field_name' : "", 
                                'error_message' : "", 
                                'response_message' : "",
                                'is_error' : False,
                            })
                            self.state = 'packed'
                            if len(self.ticl_ship_lines) == 0:
                                raise Warning(_('You can not shipped shipment without inventory lines.'))

                            if self.echo_tracking_id is not None:
                                for ticl in self.ticl_ship_lines:
                                    product_id = self.env['product.product'].search([('name', '=', 'Stand')])
                                    condition_id = self.env['ticl.condition'].search([('name', '=', 'Factory Sealed')])
                                    if ticl.tel_type.name == 'ATM' and ticl.manufacturer_id.name == 'NCR' and (ticl.product_id.name =='6634' or ticl.product_id.name =='2045'):
                                        self.env['ticl.shipment.log.line'].create({
                                            'ticl_ship_id' : self.id,
                                            'tel_type': product_id.categ_id.id,
                                            'product_id': product_id.id,
                                            'count_number' : 1,      
                                            'manufacturer_id': product_id.manufacturer_id.id,
                                            'condition_id': condition_id.id,
                                            'xl_items': 'n'
                                            })

                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                    #_logger.exception('Echo connection failed')
                # Raise Error in Odoo Pop up.
                if self.is_error:
                    raise Warning(_(warning_message))

        else:
            self.state='picked'
            if len(self.ticl_ship_lines) == 0:
                raise Warning(_('You can not shipped shipment without inventory lines.'))

    #QUERY SHIPMENT (LOAD SUMMARY AND DOCUMENTION) POST API      
    @api.model
    def echo_packed_shipment_log(self):

        est_search = self.search([('state', '=', 'picked'),('echo_call', '=', 'yes')])  
        #_logger.info("===est_search====",est_search)
        for ship in est_search:
            #if ship.shipping_carrier_name is not None:
            shipment = ship.shipping_carrier_name
            ship_search = self.env['shipping.carrier'].search([('name', '=', shipment),('active', '=', True)])
            print("==ship_search====",ship_search)
            if not ship_search:
                shipment_new = self.env['shipping.carrier'].create({'name': shipment})
            else:
                ship.shipping_carrier_id = ship_search

        records_search = self.search([('state', '=', 'picked'),('echo_call', '=', 'yes')])
        for log in records_search:
            if not log.estimated_delivery_date:
                echo_data = {}
                echo_data.update({
                        "EchoShipmentId" : log.echo_tracking_id,
                        "IncludeActivities" : True,
                        "IncludeDocuments" : True,
                    })
                double_quote_echo = json.dumps(echo_data)
                # Connection from Echo
                URL = 'http://restapi.echo.com/V2/query/shipmentdetail'
                autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
                if not autontication_key:
                    raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
                if autontication_key:
                    headers = {
                                'Content-Type': 'application/json',
                                'Authorization': autontication_key,
                             }
                    try:  
                        echo_request = requests.post(URL, data=double_quote_echo, headers=headers)
                        if str(echo_request) == "<Response [409]>":
                            view = self.env.ref('sh_message.sh_message_wizard')
                            view_id = view or False
                            context = dict(self._context or {})
                            context['message'] = "Please Try After Sometime This Shipment!"
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
                        request_data = echo_request.json()

                        #change here 409 status
                        if str(echo_request) == "<Response [409]>":
                            request5 = requests.post(URL, data=double_quote_echo, headers=headers)
                            request_data_2 = request5.json()
                            # Again Call 
                            if str(request5) == "<Response [200]>" and request_data_2 and request_data_2.get('Costs'):
                                # Update Shipment Cost
                                for line in request_data_2.get('Costs'):
                                    cost_lines = {                
                                                "name": line.get("Description"),
                                                "payment_amount": line.get("Amount"),
                                                "payment_rate": line.get("Rate"),
                                                "ticl_units": line.get("Units")
                                            }
                                    log.ticl_payment_lines = [(0, 0, cost_lines)]
                                # Update Other Fields
                                log.write({
                                    'shipment_status' : request_data.get('ShipmentStatus'),
                                    'shipping_carrier_name' : request_data.get('CarrierName'),
                                    'unit_of_weight' : request_data.get('UnitOfWeight'),
                                    'total_weight' : request_data.get('TotalWeight'),
                                    'pallet_quantity' : request_data.get('PalletQuantity'),
                                    #'request_pick_date' : request_data.get('RequestedPickUpDate'),
                                    #'request_delivery_date' : request_data.get('RequestedDeliveryDate'),
                                    'estimated_delivery_date' : request_data.get('EstimatedDeliveryDate'),
                                    'total_echo_cost' : request_data.get('TotalCost'),
                                       
                                    })


                        if str(echo_request) == "<Response [200]>" and request_data and request_data.get('Costs'):
                            # Update Shipment Cost
                            for line in request_data.get('Costs'):
                                cost_lines = {                
                                            "name": line.get("Description"),
                                            "payment_amount": line.get("Amount"),
                                            "payment_rate": line.get("Rate"),
                                            "ticl_units": line.get("Units")
                                        }
                                log.ticl_payment_lines = [(0, 0, cost_lines)]

                            EstimatedDeliveryDate = request_data.get('EstimatedDeliveryDate')
                            delivery_date = datetime.strptime(str(EstimatedDeliveryDate),'%m/%d/%Y').strftime("%Y-%m-%d")
                            log.write({'estimated_delivery_date': delivery_date})

                            # Update Other Fields
                            log.write({
                                    'shipment_status' : request_data.get('ShipmentStatus'),
                                    'shipping_carrier_name' : request_data.get('CarrierName'),
                                    'unit_of_weight' : request_data.get('UnitOfWeight'),
                                    'total_weight' : request_data.get('TotalWeight'),
                                    'pallet_quantity' : request_data.get('PalletQuantity'),
                                    'total_echo_cost' : request_data.get('TotalCost'),
                                })
                   

                    except Exception as e:
                        #raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                        _logger.exception('Echo connection failed')



    #Cron Job For Receipt for post api Here
    @api.model
    def cron_shipment_echo_token(self):
        records_search = self.search([
            ('state', '=', 'picked'),('echo_call', '=', 'yes')])
        print("====5555555555===",records_search)
        for receipt in records_search:
            self.echo_packed_shipment_log()

    #Picked Function
    #@api.model
    def ticl_packed_shipment(self):    
        for ship in self:
            for ticl in self.ticl_ship_lines:
                if ship.dropship_state == 'no':
                    ship.state = 'packed'
                    if ticl.ship_stock_move_line_id:
                        ticl.ship_stock_move_line_id.write({'status' : ship.state})
                    else:
                        tel_obj = self.env['stock.move.line']
                        product_search = tel_obj.search([('status', '=', 'picked'),('product_id', '=', ticl.product_id.id),('ticl_warehouse_id', '=', ship.sending_location_id.id)],limit=1)
                        if product_search.product_id.id == ticl.product_id.id:
                            product_search.write({'status' : 'shipped'})
                else:
                    ship.state = 'packed'

            if ship.tender_stock_move_id:
                ship.tender_stock_move_id.write({'state' : ship.state,'echo_tracking_id' : ship.echo_tracking_id})        

    #Picked Function
    @api.model
    def ticl_echo_packed_shipment(self):
        self.state = 'shipped'
        for ticl in self.ticl_ship_lines:
            if ticl.ship_stock_move_line_id:
                ticl.ship_stock_move_line_id.write({'status' : self.state})
        if self.tender_stock_move_id:
            self.tender_stock_move_id.write({'state' : self.state,'echo_tracking_id' : self.echo_tracking_id})



    #link serial number
    def create_mv_line(self,moves,picking):

        wareKey = self.env['stock.location'].browse(self.sending_location_id.id).warehouse_key
        warehouse = self.env['stock.warehouse'].search([('warehouse_key','=',int(wareKey))])
        print("====warehouse===",warehouse)
        pickingType = self.env['stock.picking.type'].search([('warehouse_id','=',warehouse.id),('name','=','Delivery Orders')])
        moveLine = self.env['stock.move.line']
        loc = self.env['stock.location'].search([('usage','=','customer')])
        loc1 = self.env['stock.location'].search([('location_id','=',warehouse.view_location_id.id),('name','=','Stock')])
        moveLst = []
        for line in self.ticl_ship_lines:
            for move in moves:
                _logger.warning('Create a %s and b %s',move,picking)
                if move.product_id == line.product_id and move.id not in moveLst:
                    moveLst.append(move.id)
                    lot_id = self.env['stock.production.lot'].search([('name','=',line.lot_id.name)], limit=1)
                    moveLine.create({
                        'picking_id':picking.id,
                        'move_id':move.id,
                        'lot_name':line.lot_id.name,
                        'product_id':line.product_id.id,
                        'categ_id':line.tel_type.id,
                        'manufacturer_id':line.manufacturer_id.id,
                        'location_dest_id':loc.id,
                        'location_id':loc1.id,
                        'product_uom_id':line.product_id.uom_id.id,
                        'qty_done':int(line.count_number),
                        'state':'confirmed',
                        'reference':picking.name,
                        'lot_id':lot_id.id,
                    })
                    
        return True
    
    #outgoing picking
    def create_picking(self):
        wareKey = self.env['stock.location'].browse(self.sending_location_id.id).warehouse_key
        warehouse = self.env['stock.warehouse'].search([('warehouse_key','=',int(wareKey))])
        print("dfgdfgfdgdfgwwwwwwwwwwwwwwwww",warehouse)
        pickingType = self.env['stock.picking.type'].search([('warehouse_id','=',warehouse.id),('name','=','Delivery Orders')])
        loc = self.env['stock.location'].search([('usage','=','customer')])
        warehouse_loc = self.env['stock.location'].search([('location_id','=',warehouse.view_location_id.id),('name','=','Stock')])
        print("==warehouse_loc===",warehouse_loc)
        move_ids_without_package = []
        for line in self.ticl_ship_lines:
            name = self.env['product.product'].browse(line.product_id.id).name
            move_ids_without_package.append((0,0,
                                        {'name':name,
                                          'product_uom':1,
                                          'product_id':line.product_id.id,
                                          'categ_id':line.tel_type.id,
                                          'manufacturer_id':line.manufacturer_id.id,
                                          'product_uom_qty':int(line.count_number),
                                          'location_dest_id':loc.id,
                                          'picking_type_id':pickingType.id,
                                          #'location_id':loc.id
    #                                       'quantity_done':data.get('product_uom_qty')
                                        }))
        vals = {
            'location_dest_id':loc.id,
            'picking_type_id':pickingType.id,
            'location_id':warehouse_loc.id,
            'move_ids_without_package':move_ids_without_package,
            'move_type': 'direct',
            'state':'assigned',
            'origin':self.name
        }
        #print("===vals===",vals)
        _logger.warning('Create a %s',vals)
        picking = self.env['stock.picking'].create(vals)
        self.pick_name = vals['name']
        picking.with_context({'merge':False}).action_confirm()
        moves = self.env['stock.move'].search([('picking_id','=',picking.id)])
        _logger.warning('Create m %s',moves)
        self.create_mv_line(moves, picking)
        picking.button_validate()
        return picking



    #Confirmed Shipment Log
    def shipped_shipment_log(self):
        if self.shipment_status == 'CANCELLED':
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please cancel shipment because CANCELLED Shipment from ECHO side!"
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

        if self.dropship_state == 'no':
            if len(self.ticl_ship_lines) == 0:
                raise Warning(_('You can not shipped shipment without inventory lines.'))
            self.state = 'shipped'
            if self.tender_stock_move_id:
                self.tender_stock_move_id.write({'state' : self.state,'echo_tracking_id' : self.echo_tracking_id})
            
            for ticl in self.ticl_ship_lines:
                if ticl.ship_stock_move_line_id:
                    ticl.ship_stock_move_line_id.write({
                        'status' : 'shipped',
                        'outbound_charges':ticl.outbound_charges, 
                        'outbound_associated_fees':ticl.outbound_associated_fees,
                        'shipment_date':ticl.ticl_ship_id.appointment_date_new
                        })
                if ticl.lot_id:
                    tel_obj = self.env['stock.move.line']
                    product_search = tel_obj.search([('serial_number', '=', ticl.serial_number),('warehouse_id', '=', self.warehouse_id.id),('status', '=', 'packed'),('product_id', '=', ticl.product_id.id)])
                    if product_search.product_id.id == ticl.product_id.id:
                        product_search.write({
                            'status' : 'shipped',
                            'outbound_charges':ticl.outbound_charges, 
                            'outbound_associated_fees':ticl.outbound_associated_fees,
                            'shipment_date':ticl.ticl_ship_id.appointment_date_new,
                            })
                else:
                    tel_obj = self.env['stock.move.line']   
                    product_search = tel_obj.search([('status', '=', 'packed'),('product_id', '=', ticl.product_id.id),('warehouse_id', '=', self.warehouse_id.id)],limit=1)
                    if product_search.product_id.id == ticl.product_id.id:
                        product_search.write({
                            'status' : 'shipped',
                            'outbound_charges':ticl.outbound_charges,
                            'outbound_associated_fees':ticl.outbound_associated_fees,
                            'shipment_date':ticl.ticl_ship_id.appointment_date_new,
                            })

            picking = self.create_picking()
            if self.shipment_type != "warehouse_transfer":
                self.env['ticl.monthly.service.line'].create_detail_mnth_service_inv(self, 'shipment')
        else:
            if len(self.ticl_ship_lines) == 0:
                raise Warning(_('You can not shipped shipment without inventory lines.'))
            self.state = 'shipped'

        for ticl in self.ticl_ship_lines:
            move_id = self.env['stock.move.line'].search([('id','=',ticl.ship_stock_move_line_id.id)])
            self.env['ticl.receipt.log.summary.line'].search([('tel_unique_no','=',move_id.tel_unique_no)]).write({'check_sale':True})    





#QUERY SHIPMENT (LOAD SUMMARY AND DOCUMENTION) POST API      
    @api.model
    def update_shipment_status(self):
        # Connection from Echo
        if self.echo_tracking_id:
            echo_tracking = self.echo_tracking_id
            URL = 'https://restapi.echo.com/v2/Shipments/' + '' + echo_tracking
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            if not autontication_key:
                raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
            if autontication_key:
                headers = {
                            'Content-Type': 'application/json',
                            'Authorization': autontication_key,
                         }
                try:  
                    request1 = requests.get(URL, headers=headers)
                    request_data = request1.json()
                    if str(request1) == "<Response [200]>" and request_data and request_data.get('ShipmentStatus'):
                        # Update Shipment Status
                        self.write({
                                'shipment_status' : request_data.get('ShipmentStatus')
                            })

                        for ticl in self.ticl_ship_lines:
                            if ticl.ship_stock_move_line_id:
                                ticl.ship_stock_move_line_id.write({'status' : self.state})   

                        self.tender_stock_move_id.write({'state' : self.state,'echo_tracking_id' : self.echo_tracking_id})


                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                    #_logger.exception('Echo connection failed')
        else:
            raise Warning(_('shipped Id Not Found in System Please Contact To Admin'))



    def update_shipment_status_shipment_cron(self):
        receipt_search = self.search([('state', '=', 'packed'),('echo_call', '=', 'yes'),('estimated_delivery_date','!=',None)])
        for receipt in receipt_search:
            if receipt.echo_tracking_id:
                echo_tracking = receipt.echo_tracking_id
                print("shipment Cron",echo_tracking)
                URL = 'https://restapi.echo.com/v2/Shipments/' + '' + echo_tracking
                autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
                if not autontication_key:
                    raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
                if autontication_key:
                    headers = {
                                'Content-Type': 'application/json',
                                'Authorization': autontication_key,
                             }
                    try:  
                        request1 = requests.get(URL, headers=headers)
                        print("==request1====",request1)
                        request_data = request1.json()
                        if str(request1) == "<Response [200]>" and request_data and request_data.get('ShipmentStatus'):
                            # Update Shipment Status

                            receipt.write({
                                    'shipment_status' : request_data.get('ShipmentStatus')
                                })


                    except Exception as e:
                        raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                        #_logger.exception('Echo connection failed')
            else:
                raise Warning(_('shipped Id Not Found in System Please Contact To Admin'))
                
    #Cron Job for shipment Update
    @api.model
    def _cron_update_shipment_status(self):
        records_search = self.search([('state', '=', 'packed'),('echo_call', '=', 'yes'),('shipment_status', '!=', 'CANCELLED')])
        print("====receivg record===",records_search)
        for receipt in records_search:
            self.update_shipment_status_shipment_cron()



    #Redirect shipment from inventory
    @api.model
    def redirect_shipment(self, vals):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action = self.env.ref('ticl_shipment.action_ticl_shipment_model')
        menu = self.env.ref('ticl_shipment.ticl_ship_order_sub').id
        ship_lines = self.env['stock.move'].search([
            ('shippable','=',True),
            ('tel_user_ids','in',self.env.user.ids),
           # ('company_id','=',self.env.user.company_id.id),
            ('status','=','inventory')
            ])
        ship_lst = []
        location_dest = 0
        for ship_line in ship_lines:
            lot = self.env['stock.production.lot'].search([('name', '=', ship_line.serial_number)])
            location_dest = ship_line.location_dest_id
            ship_lst.append([0,0,{'service_price':ship_line.service_price,
                                  'xl_items': ship_line.xl_items,
                                  'condition_id':ship_line.condition_id.id,
                                 # 'tel_note':ship_line.tel_note,
                                  'tel_type':ship_line.categ_id.id,
                                  'tel_cod':ship_line.tel_cod,
                                  'count_number':int(ship_line.product_uom_qty) if ship_line.product_uom_qty else 0,
                                  'manufacturer_id':ship_line.manufacturer_id.id,
                                  'product_id':ship_line.product_id.id,
                                  'lot_id':lot.id,
                                  'product_weight':ship_line.product_id.product_weight,
                                  'ship_stock_move_line_id':ship_line.id

                }])
            if len(ship_line.tel_user_ids) == 1:
                ship_line.shippable = False
            else:
                ship_line.tel_user_ids = [(3, self.env.user.id)]
        if vals.get('ship_id'):      
            shipment = self.browse(int(vals.get('ship_id'))) 
            shipment.ticl_ship_lines = ship_lst
            url = base_url+'/web#id='+vals.get('ship_id')+'&action='+str(action.id)+'&model=ticl.shipment.log&view_type=form&menu_id='+str(menu)
        else:
            action.sudo().context={'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'}
            logId = self.env['ticl.shipment.log'].sudo().create({'ticl_ship_lines':ship_lst,'is_from_inventory': True,'sending_location_id':location_dest.id})
            url = base_url+'/web#id='+str(logId.id) + '&action='+str(action.id)+'&model=ticl.shipment.log&view_type=form&menu_id='+str(menu)
        return url
    
    
        
    @api.model
    def get_shipment(self):
        ships = []
        shipments = self.search([('state','=','draft')])
        for shipment in shipments:
            ships.append({
                    'id':shipment.id,
                    'shipment':shipment.name,
                    'location':shipment.sending_location_id.name,
                    
                    })
        return ships
    
    
class ticl_shipment_log_line(models.Model):
    _name = 'ticl.shipment.log.line'
    _inherit = ['mail.thread']
    _description = "Shipping Log Line"
    _order = "name desc"

    @api.onchange('tel_type', 'ticl_checked')
    def _all_checked(self):
        for line in self:
            if line.tel_type.name == 'ATM':
                self.ticl_checked = True
                self.count_number = 1
            else:
                self.ticl_checked = False
                self.count_number = 1

    # onchange for serail Number
    @api.depends('lot_id')
    @api.onchange('lot_id')
    def onchange_filter_lot_id(self):
        domain = {}
        lots = []
        if self.ticl_ship_id.sending_location_id and self.product_id.id == False:
            condition_id = self.env['ticl.condition'].search([('name', 'in', ('To Recommend','Quarantine'))])
            move = self.env['stock.move.line'].search([('status', '=', 'inventory'),
                                                  ('ticl_warehouse_id', '=',self.ticl_ship_id.sending_location_id.id),
                                                  ('condition_id', 'not in', condition_id.ids)])
            if move:
                for ids in move:
                    lot_ids = self.env['stock.production.lot'].search([('name', '=', ids.serial_number)])
                    if lot_ids:
                        for ids in lot_ids:
                            lots.append(ids.id)
                            domain = {'lot_id': [('id', 'in', lots)]}
                return {'domain': domain}
            else:
                domain = {'lot_id': [('id', 'in', '')]}
                return {'domain': domain}


    #NCR FUnction for Validation
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
            if len(self.serial_number) != 10 and self.manufacturer_id.name in ["Nautilus Hyosung", "Wincor"]:
                self.serial_number = ''
                return {
                    'warning': {
                        'title': "Warning",
                        'message': "Serial number should be 10 Digit for " + self.manufacturer_id.name + " ATM's !"
                    }

                }
            if len(self.serial_number) != 12 and self.manufacturer_id.name == "Diebold":
                self.serial_number = ''
                return {
                    'warning': {
                        'title': "Warning",
                        'message': "Serial number should be 12 Digit for DieboldATM's !"
                    }

                }



    #TICL Service Charges Function 
    @api.onchange('tel_type','product_id')
    def onchange_service_price(self):
        for ship in self.ticl_ship_id:      
            for line in self:
                if line.tel_type.name == "ATM" and ship.dropship_state=='no':                   
                    rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound per ATM / Pallet')])
                    if line.ticl_ship_id.shipment_type != "warehouse_transfer":
                        line.outbound_charges = rec_log.shipment_service_charges
                
                if line.tel_type.name == "Signage" and ship.dropship_state=='no':            
                    rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound Services per Signage Piece')])
                    if line.ticl_ship_id.shipment_type != "warehouse_transfer":
                        line.outbound_charges = rec_log.shipment_service_charges

                if line.tel_type.name == "XL" and ship.dropship_state=='no':
                    rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound Services for XL Items')])
                    if line.ticl_ship_id.shipment_type != "warehouse_transfer":
                        line.outbound_charges = rec_log.shipment_service_charges

                if line.tel_type.name == "Accessory" and ship.dropship_state=='no':
                    rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound per ATM / Pallet')])
                    if line.ticl_ship_id.shipment_type != "warehouse_transfer":
                        line.outbound_charges = rec_log.shipment_service_charges

                if line.tel_type.name == "Lockbox" and ship.dropship_state=='no':
                    rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound Small Item (non-freight)')])
                    if line.ticl_ship_id.shipment_type != "warehouse_transfer":
                        line.outbound_charges = rec_log.shipment_service_charges
                

    name = fields.Text(string='Description')
    shipment_date = fields.Date(string='Shipped Date')
    ticl_ship_id = fields.Many2one('ticl.shipment.log', string='Shipment ID', readonly=True)
    product_id = fields.Many2one('product.product', string='Model Name',track_visibility='onchange')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer",track_visibility='onchange')
    serial_number = fields.Char(string='Serial#',track_visibility='onchange')
    lot_id = fields.Many2one('stock.production.lot', string='Serial#')

    count_number = fields.Char(string='Count', default=1)
    condition_id = fields.Many2one('ticl.condition', string="Condition",track_visibility='onchange')
    tel_type = fields.Many2one('product.category', string="Type",track_visibility='onchange')

    type_dup = fields.Many2one('product.category', string="Type Duplicate")
    manufacturer_id_dup = fields.Many2one('manufacturer.order', string="Manufacturer Duplicate")
    funding_doc_type = fields.Char(string = "Funding Doc Type")
    funding_doc_number = fields.Char(string = "Funding Doc No.")
    ticl_project_id = fields.Char(string = "Project Id")
    ticl_checked = fields.Boolean(string="Check")
    tel_note = fields.Char(string='Comments')
    tel_cod = fields.Selection([('Y', 'Y'),('N','N')], string='COD')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')], default='y')
    hide_cod = fields.Boolean(string="Hide COD")
    shipment_service_charges = fields.Float(string='Charges')
    hide_xl_items = fields.Boolean(string="Hide XL")
    ship_stock_move_id = fields.Many2one('stock.move', string="Stock Name")
    ship_stock_move_line_id = fields.Many2one('stock.move.line', string="Stock Move Line")
    product_weight = fields.Char(string="Weight")
    warehouse_id = fields.Many2one('stock.warehouse', string='warehouse', default=lambda self: self.env.user.warehouse_id.id)
    tel_unique_no = fields.Char(string="Unique No")
    pallet_id_name = fields.Many2one('ticl.shipment',string='Pallet Name')
    pallet_id_name_visible = fields.Char(string='Pallet ID')
    tid = fields.Char(string='TID')
    common_name = fields.Char(string='Comm Name')

    outbound_charges = fields.Float(string='charges')
#     misc_log_time = fields.Char(string='Misc Log Time', default=0)
#     misc_charges = fields.Float(string='Misc Charges')
    outbound_associated_fees = fields.Float(string='Associated Fees') 
    service_price = fields.Float(string='Price')
    one_time_charge = fields.Boolean(default=False)
#     ticl_shipment_log_line_misc = fields.One2many("common.misc.line", "shiplment_log_line_id",
#                                                   string="Ticl Shipment Log Misc")
    state_parent = fields.Boolean('State from Parent', default=False)
    status_not_inventory = fields.Boolean(string="status_not_inventory", default=False)
    receipt_id = fields.Char(string='Receipt ID')
    state = fields.Char(string="Status")
    
    @api.model
    def ticl_action_show_details(self):
        self.ensure_one()
        view = self.env.ref('ticl_shipment.view_misc_details')
        return {
            'name': _('Misc Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ticl.shipment.log.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': {
                'default_model_name': self.product_id.id,
                'default_serial_number': self.serial_number,
                'default_warehouse_id': self.ticl_ship_id.warehouse_id.id,
            },

        }

    # @api.model
    # def create(self, vals):
    #     x = super(ticl_shipment_log_line, self).create(vals)
    #     if 'ship_stock_move_id' in vals.keys():
    #         ship_id = self.env['ticl.shipment.log'].search([('id','=',vals['ticl_ship_id'])])
    #         if ship_id.shipment_type != 'warehouse_transfer':
    #             misc_inv_id = self.env['common.misc.line'].search(
    #                 [('receiving_move_ids', '=', vals['ship_stock_move_id'])])
    #             print('\n\n\n\n 09876543456', '\n ====valssss', misc_inv_id, '\n\n',vals)
    #             for ids in misc_inv_id:
    #                 print('\n\n\n\n 456789876544567876543rtyuiolm', ids)
    #                 ids.write({'shiplment_log_line_id':x.id})

    #     return x

    # @api.model
    # def write(self, vals):
    #     x = super(ticl_shipment_log_line, self).write(vals)
    #     if 'ship_stock_move_id' in vals.keys():
    #         misc_inv_id = self.env['common.misc.line'].search(
    #             [('receiving_move_ids', '=', vals['ship_stock_move_id'])])
    #         for ids in misc_inv_id:
    #             ids.write({'shiplment_log_line_id': x.id})

    #     return x


    # def change_state_l(self):
    #     for ids in self:
    #         if ids.ticl_ship_id.state in ('shipped', 'cancel'):
    #             for x in self:
    #                 x.state_parent = True

    #  Misc Charges FUnction for TICL
    # @api.onchange('misc_log_time', 'misc_charges')
    # def _total_misc_charges(self):
    #     for line in self:
    #         rec_misc = self.env['ticl.shipment.charge'].search([('name', '=', 'Misc Charges')])
            
    #         count = []
    #         for ids in self:
    #             receipt_misc = self.env['common.misc.line'].search([('shiplment_log_line_id', '=', ids.id)])
    #             for x in receipt_misc:
    #                 count.append(x.work_time)
    #             if ids.id :
    #                 shipment_log_summary_id = self.env['ticl.shipment.log.line'].search([('id', '=', ids.id)])
    #                 shipment_log_summary_id.write({'misc_log_time': sum(count)})
    #             # ids.misc_log_time = sum(count)
    #             count = []
    #         if int(line.misc_log_time) >= 1:
    #             # line.misc_charges = int(line.misc_log_time) * int(rec_misc.shipment_service_charges)
    #             line.misc_charges = int(line.misc_log_time) * int(45)
    #         else:
    #             line.misc_charges = 0.00


    # @api.onchange('tel_type')
    # def on_change_type(self):
    #     if self.tel_type:
    #         condition_id = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
    #         inv_check = self.env['stock.move'].search(
    #             [('categ_id', '=', self.tel_type.id),('condition_id','!=',condition_id.id), ('status', '=', 'inventory')])
    #
    #         products = []
    #         for ids in inv_check:
    #             products.append(ids.product_id.id)
    #         return {'domain': {'product_id': [('id', 'in', list(set(products)))]}}

    #onchange Product Name
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     self.xl_items = self.product_id.xl_items
    #     res={}
    #     if self.product_id:
    #         tel_obj = self.env['stock.move']
    #         condition_id = self.env['ticl.condition'].search([('name', 'in', ('To Recommend','Quarantine'))])
    #         product_search_count = tel_obj.search_count([
    #             ('status', '=', 'inventory'),
    #             ('product_id','=', self.product_id.id),
    #             ('location_dest_id', '=', self.ticl_ship_id.sending_location_id.id),
    #             ('condition_id','not in',condition_id.ids)
    #         ])
    #         ship_line_items = self.ticl_ship_id.ticl_ship_lines
    #         product_id = ship_line_items.filtered(lambda x: x.product_id == self.product_id)                
    #         if self.ticl_ship_id.dropship_state == 'no':
    #             if len(product_id) - 1 > product_search_count:
    #                 raise Warning('Total available product ' + str(self.product_id.name) + ' in inventory is ' + str(product_search_count))

    #             tel_obj = self.env['stock.move']
    #             product_search = tel_obj.search([('status', '=', 'inventory'),('product_id','=',self.product_id.id)])
    #             if product_search:
    #                 self.manufacturer_id = self.product_id.manufacturer_id.id or False
    #                 self.tel_type = self.product_id.categ_id.id or False
    #                 self.type_dup = self.product_id.categ_id.id or False
    #                 self.manufacturer_id_dup = self.product_id.manufacturer_id.id or False
    #                 self.product_weight = self.product_id.product_weight or False
    #             else:
    #                 raise Warning('There is no Product Name In Inventory')
    #         else:
    #             self.manufacturer_id = self.product_id.manufacturer_id.id or False
    #             self.tel_type = self.product_id.categ_id.id or False
    #             self.type_dup = self.product_id.categ_id.id or False
    #             self.manufacturer_id_dup = self.product_id.manufacturer_id.id or False
    #             self.product_weight = self.product_id.product_weight or False

    #         res['domain']={'lot_id':[
    #         ('product_id', '=', self.product_id.id),('receiving_location_id','=',self.ticl_ship_id.sending_location_id.id),
    #             ('is_scraped', '=', False),('condition_id','not in',condition_id.ids)
    #         ]}
            
    #         return res


    @api.onchange('product_id')
    def onchange_product_id(self):
        condition_id = self.env['ticl.condition'].search([('name', 'in', ('To Recommend', 'Quarantine'))])
        tel_obj = self.env['stock.move.line']
        lots = []
        if self.product_id:
            product_search_count = tel_obj.search_count([
                ('status', '=', 'inventory'),
                ('product_id','=', self.product_id.id),
                ('ticl_warehouse_id', '=', self.ticl_ship_id.sending_location_id.id),
                ('condition_id','not in',condition_id.ids)
            ])
            ship_line_items = self.ticl_ship_id.ticl_ship_lines
            product_id = ship_line_items.filtered(lambda x: x.product_id == self.product_id)
            if self.ticl_ship_id.dropship_state == 'no':
                if len(product_id) - 1 > product_search_count:
                    raise Warning('Total available product ' + str(self.product_id.name) + ' in inventory is ' + str(product_search_count))
            self.xl_items = self.product_id.xl_items
            self.manufacturer_id = self.product_id.manufacturer_id.id or False
            self.tel_type = self.product_id.categ_id.id or False
            self.type_dup = self.product_id.categ_id.id or False
            self.manufacturer_id_dup = self.product_id.manufacturer_id.id or False
            self.product_weight = self.product_id.product_weight or False

            condition_id = self.env['ticl.condition'].search([('name', 'in', ('To Recommend', 'Quarantine'))])
            move = self.env['stock.move.line'].search([('status', '=', 'inventory'), ('product_id', '=', self.product_id.id),
                                                  
                                                  ('condition_id', 'not in', condition_id.ids)])
            if move:
                for ids in move:
                    lot_ids = self.env['stock.production.lot'].search(
                        [('name', '=', ids.serial_number), ('is_scraped', '=', False),
                         ('product_id', '=', self.product_id.id),
                         ('receiving_location_id', '=', self.ticl_ship_id.sending_location_id.id)])
                    if lot_ids:
                        for ids in lot_ids:
                            lots.append(ids.id)
                domain = {'lot_id': [('id', 'in', lots)]}
                return {'domain': domain}
            else:
                domain = {'lot_id': [('id', 'in', '')]}
                return {'domain': domain}


    #unlink Fucntion for delete line            
    @api.model
    def unlink(self):
        for ids in self:
           if ids.status_not_inventory == False:
                self.env['stock.move.line'].search([('id', '=', ids.ship_stock_move_line_id.id)]).write(
                    {'status': 'inventory','shipment_id':''})
        return super(ticl_shipment_log_line, self).unlink()



    #onchange Serials Number             
    @api.onchange('lot_id')
    def onchange_serial_number(self):   
        if self.ticl_ship_id.dropship_state == 'no':
            if self.lot_id.name:
                msg = {}
                tel_obj = self.env['stock.move.line']
                lot_obj = self.env['stock.production.lot'].search([('name','=',self.lot_id.name)])
                print("====onchange_serial_number===",lot_obj)
                if tel_obj.serial_number != None:
                    tel_no = tel_obj.search([('serial_number', '!=', None),('serial_number', '=', self.lot_id.name),('status', '=', 'inventory'),('ticl_warehouse_id', '=', self.ticl_ship_id.sending_location_id.id)], limit=1)
                    print("====tel_no===",tel_no)
                    tel_no_shipped = tel_obj.search([('serial_number', '!=', None),('serial_number', '=', self.lot_id.name),('status', 'in', ['assigned','picked', 'packed', 'shipped']),('ticl_warehouse_id', '=', self.ticl_ship_id.sending_location_id.id)], limit=1)
                    for res in self:
                        if res.lot_id.name == tel_no.serial_number or None:
                            for tel in tel_no:
                                vals = {
                                        'product_id' : tel.product_id.id or False,
                                        'manufacturer_id' : tel.product_id.manufacturer_id.id or False,
                                        'condition_id' : tel.product_id.condition_id.id or False,
                                        'tel_type' : tel.product_id.categ_id.id or False,
                                        'product_weight' : tel.product_id.product_weight or False,
                                        'ship_stock_move_line_id':tel.id,
                                         }
                                record = self.update(vals)
                        elif res.lot_id.name == tel_no_shipped.serial_number:
                            msg['warning'] = {'title': ('Warning'), 'message': (
                                            'ATM is already associated with another Shipment!')}
                            return msg
                        else:
                            msg['warning'] = {'title': ('Warning'), 'message': (
                                            'Selected ATM Serial Number is not available in Inventory,Please select another Serial Number!')}
                            return msg
                 
    #Filter serial number as Warehouse Basis                        
    @api.onchange('tel_type')
    def filter_lot(self):
        for shipment in self.ticl_ship_id:
            if self.tel_type.name == "ATM" and shipment.dropship_state=="no":
                if shipment.sending_location_id.id == False:
                    raise UserError('Please Select the Origin Location !')
                products = []
                condition_id =  self.env['ticl.condition'].search([('name','in',('To Recommend','Quarantine'))])
                p_id =  self.env['product.product'].search([('id','=',self.product_id.id)])
                print("====p_id====",p_id)
                production_id = self.env['stock.production.lot'].search([('condition_id','not in',condition_id.ids),('product_id','=',p_id.id),
                                                                         ('receiving_location_id','=',shipment.sending_location_id.id)])
                print("====production_id====",production_id)
                for lot_ids in production_id:
                    if lot_ids.product_id.active == True:
                            move_id = self.env['stock.move.line'].search([
                                                                 ('serial_number','=',lot_ids.name),('status','=','inventory')],limit=1)
                            print("====move_id====",move_id)
                            if move_id.status == 'inventory':
                                products.append(lot_ids.id)
                return {'domain': {'lot_id': [('id', 'in', list(set(products)))]}}



#Ticl Shipment Payments 
class ticl_shipment_payment(models.Model):
    _name = 'ticl.shipment.payment'
    _description = "Ticl Shipments Payment"

    name = fields.Text(string='Description')
    ticl_payment_id = fields.Many2one('ticl.shipment.log', string='Shipment Payment ID', invisible=1)
    payment_amount = fields.Char(string='Amount')
    payment_rate = fields.Char(string='Rate')
    ticl_units = fields.Char(string='Units')




    

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('quantity')
    def check_quantity(self):
        if self.lot_id.sale_order_count:
            res = super(StockQuant, self).check_quantity()
        return True
