# -*- coding: utf-8 -*-
###################################################################################
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning
import threading
import urllib3
import json
import requests
import logging
from datetime import datetime, timedelta
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class ticl_receipt(models.Model):
    _name = 'ticl.receipt'
    _inherit = ['mail.thread']
    _description = "Receiving Order"
    _order = 'delivery_date desc, id desc'

    #Unique Receiving Number
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('ticl.receipt') or '/'
        vals['name'] = sequence
        if 'ticl_receipt_lines' in vals.keys():
            for recs in range(len(vals['ticl_receipt_lines'])):
                vals['ticl_receipt_lines'][recs][2]['tel_type'] = vals['ticl_receipt_lines'][recs][2]['type_dup']
                vals['ticl_receipt_lines'][recs][2]['manufacturer_id'] = vals['ticl_receipt_lines'][recs][2]['manufacturer_id_dup']
                tel_type =  self.env['product.category'].search([('id','=',vals['ticl_receipt_lines'][recs][2]['tel_type'])])
                if tel_type.name == 'ATM' and vals['ticl_receipt_lines'][recs][2]['serial_number'] == False:
                    product = self.env['product.product'].search([('id','=',vals['ticl_receipt_lines'][recs][2]['product_id'])])
                    raise UserError("Please enter Serial Number for the Model ({0})".format(product.name))
        return super(ticl_receipt, self).create(vals)

#     @api.multi
    def write(self, vals):
        if 'ticl_receipt_lines' in vals.keys():
            for recs in range(len(vals['ticl_receipt_lines'])):
                if vals['ticl_receipt_lines'][recs][2] != False and isinstance(vals['ticl_receipt_lines'][recs][1],int) == True :
                    line_id = self.env['ticl.receipt.line'].search([('id','=',vals['ticl_receipt_lines'][recs][1])])
                    if 'serial_number' in vals['ticl_receipt_lines'][recs][2].keys():
                        if vals['ticl_receipt_lines'][recs][2]['serial_number'] == False :
                            raise UserError("Please enter Serial Number for the Model ({0})".format(line_id.product_id.name))
                if vals['ticl_receipt_lines'][recs][2] != False and isinstance(vals['ticl_receipt_lines'][recs][1],int) == False:
                    vals['ticl_receipt_lines'][recs][2]['tel_type'] = vals['ticl_receipt_lines'][recs][2]['type_dup']
                    vals['ticl_receipt_lines'][recs][2]['manufacturer_id'] = vals['ticl_receipt_lines'][recs][2]['manufacturer_id_dup']
                    tel_type =  self.env['product.category'].search([('id','=',vals['ticl_receipt_lines'][recs][2]['tel_type'])])
                    if tel_type.name == 'ATM' and vals['ticl_receipt_lines'][recs][2]['serial_number'] == False:
                        product = self.env['product.product'].search([('id','=',vals['ticl_receipt_lines'][recs][2]['product_id'])])
                        raise UserError("Please enter Serial Number for the Model ({0})".format(product.name))

        return super(ticl_receipt, self).write(vals)



    # This function is for Revert Receipt back to draft state
    def revert_receipt(self):
        for record in self:
            for line in record.ticl_receipt_lines:
                receipt_record = self.env['ticl.receipt.line'].sudo().search(
                    [('serial_number', '=', line.serial_number)])
                move_id = self.env['stock.move'].sudo().search([('serial_number', '=', line.serial_number)],
                                                               limit=1)
                receipt_status = []
                status = []
                for rec in receipt_record:
                    if rec.serial_number:
                        if receipt_record:
                            for ids2 in receipt_record:
                                receipt_status.append(ids2.ticl_receipt_id.state)

                        if 'draft' in receipt_status:
                            raise UserError('Serial Number already exists in Draft !')
                        elif 'pending' in receipt_status:
                            raise UserError('Serial Number already exists in Pending !')
                        elif 'inprogress' in receipt_status:
                            raise UserError('Serial Number already exists in In-progress !')

                        if move_id :
                            for ids in move_id:
                                status.append(ids.status)

                        if 'inventory' in status:
                            raise UserError('Serial Number already exists in Inventory !')
                        elif 'assigned' in status:
                            raise UserError('Serial Number already exists in Assigned !')
                        elif 'picked' in status:
                            raise UserError('Serial Number already exists in Picked !')
                        elif 'packed' in status:
                            raise UserError('Serial Number already exists in Packed !')
                        else:
                            record.state = 'draft'
                            break
                    else:
                        record.state = 'draft'
        
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

#Total Lockbox
    @api.depends('ticl_receipt_lines.count_number')
    def count_total_lockbox(self):  
        for receving in self:      
            total_lockbox = 0
            for line in receving.ticl_receipt_lines:
                if line.tel_type.name == 'Lockbox':
                    total_lockbox += int(line.count_number)  
            receving.update({'total_lockbox': total_lockbox })

    #Total XL
    @api.depends('ticl_receipt_lines.count_number')
    def count_total_xl(self):  
        for receving in self:      
            total_xl = 0
            for line in receving.ticl_receipt_lines:
                if line.tel_type.name == 'XL':
                    total_xl += int(line.count_number)  
            receving.update({'total_xl': total_xl })

    #delivery date       
    # def _get_delivery_date(self):
    #     today_date = datetime.today()
    #     return today_date

    #Write method
    # @api.multi
    # def write(self, values):
    #     if 'delivery_date' in values.keys():
    #         for line in self.ticl_receipt_lines:
    #             line.received_date = values['delivery_date']
    #     return super(ticl_receipt, self).write(values)

    #Total Pallet Weight
    @api.depends('ticl_receipt_lines.product_weight')
    def count_total_weight(self):
        for ship in self:      
            total_weight = 0 
            for line in ship.ticl_receipt_lines:
                if float(line.product_weight) > 0.0:
                    total_weight += int(line.line_item_weight)
            ship.update({'total_weight': total_weight })

    #Total monitory alue
    @api.depends('ticl_receipt_lines.monitory_value')
    def count_total_monitory_value(self):
        for ship in self:      
            total_monitory_value = 0 
            for line in ship.ticl_receipt_lines:
                if float(line.product_id.monitory_value) > 0.0:
                    total_monitory_value += (int(line.product_id.monitory_value) * int(line.count_number))
            ship.update({'total_monitory_value': total_monitory_value })

    #Echo date more than 2 weeks from pickup_date date        
    #@api.depends('pickup_date')
    def check_estimated_delivery_date(self):
        if self.pickup_date:
            self.echo_estimated_delivery_date = self.pickup_date + relativedelta(weeks=+2)  

    # @api.multi
    # @api.onchange('ticl_receipt_lines')
    # def _check_serial_no(self):
    #     for rec in self:
    #         exist_serial_no = []
    #         for line in rec.ticl_receipt_lines:
    #             if line.serial_number in exist_serial_no:
    #                 raise UserError(_('Duplicate serial number not allowed'))
    #             exist_serial_no.append(line.serial_number)            

    name = fields.Char(string='Receipt', index=True, readonly=True)
    tel_note = fields.Char(string='Comment/Note')
    asn_received_date = fields.Date(string='Received Date')
    pickup_date = fields.Date(string='PickUp Date')
    delivery_date = fields.Date(string='Delivery Date',track_visibility='onchange')
    echo_estimated_delivery_date = fields.Date(string='Required Deliver By Date',compute='check_estimated_delivery_date')

    estimated_delivery_date = fields.Date(string='Est Delivery Date')
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)',track_visibility='onchange')
    unit_of_weight = fields.Char(string="UnitOfWeight")

    sending_location_id = fields.Many2one('res.partner', string='Origin Location',ondelete='cascade', default='',track_visibility='onchange')
    receiving_location_id = fields.Many2one('stock.location', string='Destination Location',default='',track_visibility='onchange')

    receiving_id = fields.Many2one('tel.asn.receiving', string="ASN Number")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse Name', default=lambda self: self.env.user.warehouse_id.id,track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    asn_bol_type = fields.Selection([('asn', 'ASN'),('bol','BOL')], string='Type', default='bol')

    state = fields.Selection([('draft', 'Draft'),('pending','Pending'),('inprogress','In-Progress'),('completed','Completed'),('quarantine','Quarantine'),('cancel', 'Cancelled')],
        string='Status', default='draft',track_visibility='onchange')

    total_atm = fields.Char(string='Total ATM', compute='count_total_atm')
    total_signage = fields.Char(string='Total Signage', compute='count_total_signage')
    total_accessory = fields.Char(string='Total Accessory', compute='count_total_accessory')
    total_lockbox = fields.Char(string='Total Lockbox', compute='count_total_lockbox')
    total_xl = fields.Char(string="Total XL", compute='count_total_xl')

    ticl_receipt_lines = fields.One2many('ticl.receipt.line', 'ticl_receipt_id', ondelete='cascade',track_visibility='onchange')
    ticl_receipt_payment_lines = fields.One2many('ticl.receipt.payment', 'ticl_receipt_payment_id', ondelete='cascade')

    total_quarantine = fields.Char(string='Quarantine', compute='count_total_quarantine')
    start_quarantine_date = fields.Date(string='Start Quarantine Date')
    end_quarantine_date = fields.Date(string='End Quarantine Date')
    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier')
    shipping_carrier_name = fields.Char(string='Shipping Carrier Name')
    shipment_status = fields.Char(string="Shipment Status")
    
    accepted_date =  fields.Date(string='Accepted Date',track_visibility='onchange')
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee',track_visibility='onchange')
    old_name = fields.Char(string='Old Receipt Id', index=True)

    total_cost = fields.Char(string='Total Cost')
    total_weight = fields.Char(string="Total Weight", compute='count_total_weight')
    total_pieces = fields.Char(string='Total Pieces')
    total_monitory_value = fields.Char(string="Monitory Value", compute='count_total_monitory_value')


    total_pallet = fields.Char(string='Total Pallet')
    echo_tracking_id = fields.Char(string="Echo Receipt Id")
    shipment_mode = fields.Selection([('TL', 'TL'),
                                      ('LTL', 'LTL')], string='Shipment Mode')

    echo_call = fields.Selection([('yes', 'YES'),
                                      ('no', 'NO')], string='Call Echo(Optional)', default='no')
    response_message = fields.Char(string='Responce Message') 
    error_code = fields.Char(string='Error Code')   
    error_message = fields.Char(string='Error Message')   
    error_field_name = fields.Char(string='Error Field Name')
    is_error = fields.Boolean(string='Is Error', default=False, copy=False)

    miles = fields.Integer(string='Miles')   
    chase_fright_cost = fields.Float(string='Chase Fright Charge')
    receipt_type = fields.Selection([('Regular', 'Regular'),('Inventory Transfer', 'Inventory Transfer'),
                                      ('Guaranteed', 'Guaranteed'),
                                      ('Expedited', 'Expedited'),('Non Freight','Non Freight'),
                                      ('Re-Consignment', 'Re-Consignment'),('warehouse_transfer', 'Warehouse Transfer')], 
                                       string='Receipt Type'
                                      ,default='Regular',track_visibility='onchange')


    #onchange Receipt Type
    # @api.onchange('receipt_type')
    # def on_change_receipt_type(self):
    #     res = {}
    #     if self.receipt_type == 'warehouse_transfer':
    #         res['domain'] = {'sending_location_id': [('is_warehouse','=',True)]}
    #     elif self.receipt_type != 'warehouse_transfer':
    #         res['domain'] = {'sending_location_id': ['|','|',('is_rigger','=',True),('is_warehouse','=',True),
    #                         ('is_location','=',True)]}
    #     return res

# Employee Auto Update in
    @api.onchange('user_id')
    def on_change_user(self):
        if not self.user_id:
            return {}
        emp = self.env['hr.employee'].search([('user_id','=',self.user_id.id)])
        self.hr_employee_id = emp

    @api.onchange('receiving_location_id')
    def on_change_destination(self):
        warehouse_id = self.env['stock.warehouse'].search([('name', '=', self.receiving_location_id.name )])
        self.warehouse_id = warehouse_id.id


    # @api.onchange('delivery_date')
    # def on_change_delivery_date(self):     
    #     for line in self.ticl_receipt_lines:
    #         line.received_date = self.delivery_date

    #Confirm Receipt function
    # @api.multi
    # def confirm_receipt(self):
    #     self.write({'state': 'pending'})


    #import receipt
    def import_receipt(self):
        view = self.env.ref('ticl_import.wizard_import_work_order')
        return {
            'name': 'Warning',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.work.order',
            'view': [('view', 'form')],
            'target': 'new',
        }

#Basic RTE3MDU1OTpiMjRmYWRmYS0yNjkwLTQ3NDgtOThjMi1lYWEzNTViNTViMjQ=
#Echo API POST INTEGRATION With Receipts Creations
#     @api.multi
    def confirm_receipt(self):
        print('total weight',int(self.total_weight))
        if not self.ticl_receipt_lines:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please fill the Receipts Lines"
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
        elif self.echo_call == 'no':
            self.write({'state': 'pending'})

        elif (int(self.total_pallet) > 21 or int(self.total_weight) > 45000) and self.echo_call == 'yes':
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
        #Basic RTE3MDU1OTpiMjRmYWRmYS0yNjkwLTQ3NDgtOThjMi1lYWEzNTViNTViMjQ=
        elif int(self.total_pallet) < 13 and int(self.total_weight) <= 19999 and self.echo_call == 'yes':
            print("===LTL===")
            data = {}
            data["Origin"] = {}
            data["Destination"] = {}
            data["Origin"].update({
                "LocationType" : "BUSINESS",
                "LocationName" : self.sending_location_id.name,
                "AppointmentDate" : self.pickup_date.strftime('%m/%d/%Y'),
                "AppointmentStart" : "12:59",
                "AppointmentEnd" : "13:59",
                "AddressLine1" : self.sending_location_id.street,
                "AddressLine2" : self.sending_location_id.street2 or "",
                "City" : self.sending_location_id.city_id.name or "",
                "StateProvince" : self.sending_location_id.state_id.code or "",
                "PostalCode" : self.sending_location_id.zip or "",
                "CountryCode" : "US",
                "ContactName" : self.sending_location_id.contact_name or "",
                "ContactPhone" : self.sending_location_id.phone or "",
                "BolNumber" : self.name or "",
                "ReferenceNumber" : "00000000",
                "IsBlind": False,
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
                "BlindCity" : "BLCITY",
                "BlindStateProvince" : "",
                "BlindPostalCode" : "",
                "BlindCountryCode" : "",
                "Accessorials" : [],                       
            })

            data["Destination"].update({
                "LocationType" : "BUSINESS",
                "LocationName" : self.receiving_location_id.warehouse_id.name,
                "AppointmentDate" : self.echo_estimated_delivery_date.strftime('%m/%d/%Y'),
                "AppointmentStart" : self.receiving_location_id.warehouse_id.checkin_time or "12:59",
                "AppointmentEnd" : self.receiving_location_id.warehouse_id.checkout_time or "13:59",
                "AddressLine1" : self.receiving_location_id.warehouse_id.street or "",
                "AddressLine2" : self.receiving_location_id.warehouse_id.street2 or "",
                "City" : self.receiving_location_id.warehouse_id.city_id.name or False,
                "StateProvince" : self.receiving_location_id.warehouse_id.state_id.code or "",
                "PostalCode" : self.receiving_location_id.warehouse_id.zip_code or "",
                "ContactName": self.receiving_location_id.warehouse_id.contact_name or "",
                "CountryCode" : "US",
                "ContactPhone" : self.receiving_location_id.warehouse_id.warehouse_phone or "",
                "BolNumber" : self.name or "",
                "ReferenceNumber" : "00000000",
                "BlindLocationName" : "",
                "BlindAddressLine1" : "",
                "BlindAddressLine2" : "",
            })

            ticl_lines = []
            for line in self.ticl_receipt_lines:
                ticl_lines.append({
                    "ItemId":"",
                    "Description" : line.product_id.categ_id.name,
                    "NmfcClass" : "70",
                    "NmfcNumber" : "116030-09",
                    "Weight" : int(line.line_item_weight) or "",
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
            ticl_references.append({
                    "Name":"Work Order #",  
                    "Value":self.name
                    })
            model_inc = []
            serial_inc = []
            num = 0
            for line in self.ticl_receipt_lines:
                num = num + 1
                model_inc = "Model Number" + ' ' + str(num)
                serial_inc = "Serial #" + '' + str(num)
                ticl_references.append({
                    "Name" : model_inc,
                    "value" : line.product_id.name,
                    })
                ticl_references.append({
                    "Name" : serial_inc,
                    "value" : line.serial_number,
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
                    "BolNumber" : self.name or "",
                    "OrderNumber" : "",
                    "PoNumber" : self.name or "",
                    "ProNumber" : "",
                    "PodSignature" : "",
                    "GlCode" : "",
                    "AckNotification" : "ssingh@delaplex.in",
                    "AsnNotification" : "ssingh@delaplex.in",
                    "References" : ticl_references
                }) 

            double_quote_data = json.dumps(data)
            print("===double_quote_data====",double_quote_data)
            # Echo Connection
            warning_message = ""
            url = "https://restapi.echo.com/v2/Shipments/LTL"
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            print("===autontication_key===",autontication_key)
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
                                    'bill_of_lading_number' : "",
                                    'shipment_mode' : "",
                                    'is_error' : True,
                                })

                    if str(request1) == "<Response [200]>": 
                        if request_data and request_data.get('ShipmentId') and request_data.get('ShipmentMode'):
                            self.write({
                                'bill_of_lading_number' : request_data.get('ShipmentId'),
                                'shipment_mode' : request_data.get('ShipmentMode'),
                                'error_code' : "", 
                                'error_field_name' : "", 
                                'error_message' : "", 
                                'response_message' : "",
                                'is_error' : False,
                            })
                            print("request_data.getShipmentId",request_data.get('ShipmentId'))
                        self.write({'state': 'pending'})
 
                            # if self.echo_tracking_id is not None:
                            #     for ticl in self.ticl_receipt_lines:
                            #         product_id = self.env['product.product'].search([('name', '=', 'Stand')])
                            #         condition_id = self.env['ticl.condition'].search([('name', '=', 'Factory Sealed')])
                            #         if ticl.tel_type.name == 'ATM' and ticl.manufacturer_id.name == 'NCR' and (ticl.product_id.name =='6634' or ticl.product_id.name =='2045'):
                            #             self.env['ticl.receipt.line'].create({
                            #                 'ticl_ship_id' : self.id,
                            #                 'tel_type': product_id.categ_id.id,
                            #                 'product_id': product_id.id,
                            #                 'count_number' : 1,      
                            #                 'manufacturer_id': product_id.manufacturer_id.id,
                            #                 'condition_id': condition_id.id,
                            #                 'xl_items': 'n'
                            #                 })
                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                    #_logger.exception('Echo connection failed')
                if self.is_error:
                    # Raise Error in Odoo Pop up.
                    raise Warning(_(warning_message))

        #TL shipment Creation API
        elif ((int(self.total_pallet) > 12) and (int(self.total_pallet) < 21) and self.echo_call == 'yes') or ((int(self.total_weight) > 19999) and (int(self.total_weight) < 45001) and self.echo_call == 'yes'):
            print("===TL=====")
            data = {}
            ticl_tl = [{
                "LocationType" : "BUSINESS",
                "LocationName" : self.sending_location_id.name or False,
                "AppointmentDate" : self.pickup_date.strftime('%m/%d/%Y') or False,
                "AppointmentStart" : "12:59",
                "AppointmentEnd" : "13:59",
                "AddressLine1" : self.sending_location_id.street or "",
                "AddressLine2" : self.sending_location_id.street2 or "",
                "City" : self.sending_location_id.city_id.name or "",
                "StateProvince" : self.sending_location_id.state_id.code or "",
                "PostalCode" : self.sending_location_id.zip or "",
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
                "ContactName" : self.sending_location_id.contact_name or "",
                "ContactPhone" : self.sending_location_id.phone or "",
                "BolNumber" : self.name or "",
                "ReferenceNumber" : "00000000",
                "StopType" : "PICK",
                "StopNumber" : 1
                },
                {
                  "LocationType" : "CONSTRUCTIONSITE",
                  "LocationName" : self.receiving_location_id.name or "",
                  "AppointmentDate" : self.echo_estimated_delivery_date.strftime('%m/%d/%Y') or "",
                  "AppointmentStart" : "12:59",
                  "AppointmentEnd" : "13:59",
                  "AddressLine1" : self.receiving_location_id.warehouse_id.street or "",
                  "AddressLine2" : self.receiving_location_id.warehouse_id.street2 or "",
                  "City" : self.receiving_location_id.warehouse_id.city_id.name or False,
                  "StateProvince" : self.receiving_location_id.warehouse_id.state_id.code or False,
                  "PostalCode" : self.receiving_location_id.warehouse_id.zip_code or False,
                  "CountryCode" : "US",
                  "Accessorials" : [],
                  "ContactName" : self.receiving_location_id.warehouse_id.contact_name or "",
                  "ContactPhone" : self.receiving_location_id.warehouse_id.warehouse_phone or False,
                  "BolNumber" : self.name or "",
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
            for line in self.ticl_receipt_lines:
                ticl_lines.append({
                      "ItemId" : "",
                      "Description" : line.product_id.categ_id.name or False,
                      "NmfcClass" : "70",
                      "NmfcNumber" : "116030-09",
                      "Weight" : int(line.line_item_weight) or "",
                      "PackageType" : "PIECES",
                      "PackageQuantity" : 1,
                      "HandlingUnitType" : "PALLETS",
                      "HandlingUnitQuantity" : 1,
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
            ticl_references.append({
                    "Name":"Work Order #",  
                    "Value":self.name
                    })
            model_inc = []
            serial_inc = []
            num = 0
            for line in self.ticl_receipt_lines:
                num = num + 1
                model_inc = "Model Number" + ' ' + str(num)
                serial_inc = "Serial #" + '' + str(num)
                ticl_references.append({
                    "Name" : model_inc,
                    "value" : line.product_id.name,
                    })
                ticl_references.append({
                    "Name" : serial_inc,
                    "value" : line.serial_number,
                    })
            
            data.update({
                  "CubicSize" : 10,
                  "UnitOfWeight" : "LB",
                  "CustomerNotes" : self.tel_note or "",
                  "ShipmentNotes" : self.tel_note or "",
                  "EquipmentMinTemp" : " ",
                  "EquipmentMaxTemp" : " ",
                  "EquipmentTypes" : ["FLATBED48", "FLATBED53"],
                  "EquipmentAccessorials" : [],
                  "EquipmentTarps" : ["T4"],
                  "EquipmentNotes" : "",
                  "BolNumber" : self.name or "",
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
            print("====double_quote_data===",double_quote_data)
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
                                    'bill_of_lading_number' : "",
                                    'shipment_mode' : "",
                                    'is_error' : True,
                                })

                    if str(request1) == "<Response [200]>": 
                        print("===TL22222=====")
                        if request_data and request_data.get('ShipmentId') and request_data.get('ShipmentMode'):
                            self.write({
                                'bill_of_lading_number' : request_data.get('ShipmentId'),
                                'shipment_mode' : request_data.get('ShipmentMode'),
                                'error_code' : "", 
                                'error_field_name' : "", 
                                'error_message' : "", 
                                'response_message' : "",
                                'is_error' : False,
                            })
                        self.write({'state': 'pending'})

                            # if self.echo_tracking_id is not None:
                            #     for ticl in self.ticl_ship_lines:
                            #         product_id = self.env['product.product'].search([('name', '=', 'Stand')])
                            #         condition_id = self.env['ticl.condition'].search([('name', '=', 'Factory Sealed')])
                            #         if ticl.tel_type.name == 'ATM' and ticl.manufacturer_id.name == 'NCR' and (ticl.product_id.name =='6634' or ticl.product_id.name =='2045'):
                            #             self.env['ticl.shipment.log.line'].create({
                            #                 'ticl_receipt_id' : self.id,
                            #                 'tel_type': product_id.categ_id.id,
                            #                 'product_id': product_id.id,
                            #                 'count_number' : 1,      
                            #                 'manufacturer_id': product_id.manufacturer_id.id,
                            #                 'condition_id': condition_id.id,
                            #                 'xl_items': 'n'
                            #                 })

                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                    #_logger.exception('Echo connection failed')
                # Raise Error in Odoo Pop up.
                if self.is_error:
                    raise Warning(_(warning_message))

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


        receipt_ids = self.env['ticl.receipt'].search(
            [('name', '=', self.name)], limit=1)
        action =self.env.ref('ticl_receiving.action_ticl_pending_receipts').read()[0]
        action['views'] = [(self.env.ref('ticl_receiving.ticl_receipts_pending_form_view').id, 'form')]
        action['res_id'] = receipt_ids.id
        return action


    #QUERY SHIPMENT (LOAD SUMMARY AND DOCUMENTION) POST API      
#     @api.multi
    def ticl_receipt_post_log(self):
        est_search = self.search([('state', '=', 'pending'),('echo_call', '=', 'yes')])  
        for ship in est_search:
            #if ship.shipping_carrier_name is not None:
            shipment = ship.shipping_carrier_name
            ship_search = self.env['shipping.carrier'].search([('name', '=', shipment),('active', '=', True)])
            print("==ship_search===",ship_search)
            if not ship_search:
                shipment_new = self.env['shipping.carrier'].create({'name': shipment})
            else:
                ship.shipping_carrier_id = ship_search

        records_search = self.search([('state', '=', 'pending'),('echo_call', '=', 'yes')])
        for log in records_search:
            if not log.estimated_delivery_date:
                echo_data = {}
                echo_data.update({
                        "EchoShipmentId" : log.bill_of_lading_number,
                        "IncludeActivities" : True,
                        "IncludeDocuments" : True,
                    })
                double_quote_echo = json.dumps(echo_data)
                #print("===double_quote_echo==",double_quote_echo)
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
                        #print("===echo_request==",echo_request)
                        request_data = echo_request.json()
                        #print("===request_data==",request_data)
                        #change here 409 status
                        if str(echo_request) == "<Response [409]>":
                            #print("===400==")
                            request5 = requests.post(URL, data=double_quote_echo, headers=headers)
                            request_data_2 = request5.json()
                            # Again Call 
                            if str(request5) == "<Response [200]>" and request_data_2 and request_data_2.get('Costs'):
                                #print("===400200==")
                                # Update Shipment Cost
                                for line in request_data_2.get('Costs'):
                                    cost_lines = {                
                                                "name": line.get("Description"),
                                                "payment_amount": line.get("Amount"),
                                                "payment_rate": line.get("Rate"),
                                                "ticl_units": line.get("Units")
                                            }
                                    log.ticl_receipt_payment_lines = [(0, 0, cost_lines)]
                                # if request_data.get('CarrierName') and request_data.get('CarrierName')[0]:
                                #     self.write({
                                #                 'shipping_carrier_id' : request_data.get('CarrierName')[0].get('Id')
                                #             })

                                # Update Other Fields

                                EstimatedDeliveryDate = request_data.get('EstimatedDeliveryDate')
                                delivery_date = datetime.strptime(str(EstimatedDeliveryDate),'%m/%d/%Y').strftime("%Y-%m-%d")
                                log.write({'estimated_delivery_date': delivery_date})

                                log.write({
                                    'shipment_status' : request_data.get('ShipmentStatus'),
                                    'shipping_carrier_name' : request_data.get('CarrierName'),
                                    'unit_of_weight' : request_data.get('UnitOfWeight'),
                                    'total_weight' : request_data.get('TotalWeight'),
                                    #'estimated_delivery_date' : request_data.get('EstimatedDeliveryDate'),
                                    'total_cost' : request_data.get('TotalCost'),
                                       
                                    })

                        if str(echo_request) == "<Response [200]>" and request_data and request_data.get('Costs'):
                            # Update Shipment Cost
                            #print("===200==")
                            for line in request_data.get('Costs'):
                                cost_lines = {                
                                            "name": line.get("Description"),
                                            "payment_amount": line.get("Amount"),
                                            "payment_rate": line.get("Rate"),
                                            "ticl_units": line.get("Units")
                                        }
                                log.ticl_receipt_payment_lines = [(0, 0, cost_lines)]

                            EstimatedDeliveryDate = request_data.get('EstimatedDeliveryDate')
                            delivery_date = datetime.strptime(str(EstimatedDeliveryDate),'%m/%d/%Y').strftime("%Y-%m-%d")
                            log.write({'estimated_delivery_date': delivery_date})

                            # Update Other Fields
                            log.write({
                                    'shipment_status' : request_data.get('ShipmentStatus'),
                                    'shipping_carrier_name' : request_data.get('CarrierName'),
                                    'unit_of_weight' : request_data.get('UnitOfWeight'),
                                    'total_weight' : request_data.get('TotalWeight'),
                                    #'estimated_delivery_date' : request_data.get('EstimatedDeliveryDate').strftime('%m/%d/%Y'),
                                    'total_cost' : request_data.get('TotalCost'),
                                })

                    except Exception as e:
                        _logger.exception('Echo connection failed')



    #Cron Job For Receipt for post api Here
    @api.model
    def _cron_receipt_echo_tokens(self):
        records_search = self.search([('state', '=', 'pending'),('echo_call', '=', 'yes')])
        for receipt in records_search:
            self.ticl_receipt_post_log()


    #QUERY SHIPMENT (LOAD SUMMARY AND DOCUMENTION) POST API      
#     @api.multi
    def update_receipt_status(self):
        # Connection from Echo
        if self.bill_of_lading_number:
            echo_tracking = self.bill_of_lading_number
            print("===receipt",echo_tracking)
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

                        self.write({
                                'shipment_status' : request_data.get('ShipmentStatus')
                            })


                except Exception as e:
                    raise Warning(_('Echo connection failed, Please contact with Echo Admin'))
                    #_logger.exception('Echo connection failed')
        else:
            raise Warning(_('shipped Id Not Found in System Please Contact To Admin'))

    #QUERY SHIPMENT (LOAD SUMMARY AND DOCUMENTION) POST API With Cron job       
    def update_receipt_status_with_cron(self):
        receipt_search = self.search([('state', '=', 'pending'),('echo_call', '=', 'yes'),('estimated_delivery_date','!=',None)])
        for receipt in receipt_search:
            if receipt.bill_of_lading_number:
                echo_tracking = receipt.bill_of_lading_number
                print("cronnnnnnnnnnnnnnnnnn",echo_tracking)
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
    #Cron job for update receipts status            
    @api.model
    def _cron_update_receipt_status(self):
        records_search = self.search([('state', '=', 'pending'),('echo_call', '=', 'yes'),('shipment_status', '!=', 'CANCELLED')])
        print("====receivg record===",records_search)
        for receipt in records_search:
            self.update_receipt_status_with_cron()




    #Receiving Log Entry Function
    def confirm_receipt_log(self):

        if not self.delivery_date:
            print("====test====")
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please Fill The Delivery Date!"
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
        if not self.ticl_receipt_lines:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please enter shipment inventory items to proceed!"
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

        if self.echo_call == 'yes' and (self.bill_of_lading_number == False or self.shipment_mode == False \
            or self.estimated_delivery_date == False or self.shipping_carrier_id.id == False):
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Echo Details not found!"
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

        for tel_line in self.ticl_receipt_lines:
            if int(tel_line.count_number) <= 0:
                raise UserError('Count should not accept 0 or Less value')

            receipt = self.env['ticl.receipt.log.summary'].search([('name', '=' ,self.name)])
            print("====receipt==",receipt)
            if receipt.id == False:
                state = 'inprogress'
                # q_count,quarantine = [],[]
                # for ids in self.ticl_receipt_lines:
                #     q_count.append(ids.quarantine_count)
                #     if ids.condition_id.name == 'Quarantine':
                #         quarantine.append('y')
                # if sum(q_count) > 0 or quarantine:
                #     state = 'quarantine'
                # else:
                #     state = 'inprogress'

                vals = {
                    'tel_receipt_log_id': self.id,
                    'name': self.name,
                    'delivery_date': self.delivery_date,
                    'sending_location_id': self.sending_location_id.id,
                    'receiving_location_id':self.receiving_location_id.id,
                    'warehouse_id': self.warehouse_id.id,
                    'receipt_type' : self.receipt_type,
                    'name': self.name,
                    'tel_note':self.tel_note,
                    'total_atm':self.total_atm,
                    'total_signage':self.total_signage,
                    'total_accessory':self.total_accessory,
                    'total_lockbox':self.total_lockbox,
                    'total_xl':self.total_xl,
                    'pickup_date': self.pickup_date,
                    'accepted_date': self.accepted_date,
                    'shipping_carrier_id': self.shipping_carrier_id.id,
                    'bill_of_lading_number': self.bill_of_lading_number,
                    'attachment_ids': [(6, None, self.attachment_ids.ids)],
                    'hr_employee_id': self.hr_employee_id.id,
                    'state' : state,
                    'old_name':self.old_name,
                    'total_pallet':self.total_pallet,
                    'total_weight':self.total_weight,
                    'total_cost':self.total_cost,
                    'shipment_mode':self.shipment_mode,
                    'estimated_delivery_date':self.estimated_delivery_date,
                    'echo_call':self.echo_call,
                }
                log_id = self.env['ticl.receipt.log.summary'].create(vals)
                print("====log_id====",log_id)
            if tel_line.condition_id.name != 'Quarantine' and receipt.id != False :
                receipt_number = self.env['ticl.receipt.log.summary'].search([('name', '=' ,self.name)])
                log_id = receipt_number

        Qln = self.ticl_receipt_lines.filtered(lambda x:x.condition_id.name == 'Quarantine' or int(x.quarantine_count) > 0)
        self.state = 'inprogress'

        # if Qln:
        #     self.state = 'quarantine'
        # else:
        #     self.state = 'inprogress'

        for tel_line in self.ticl_receipt_lines:
            if tel_line.condition_id.name == 'Quarantine':
                tel_line.not_quarantine = 'f'
            if int(tel_line.count_number) > 0 and tel_line.status_inv != 'y' and tel_line.not_quarantine not in ['t']:
                if tel_line.product_id :
                    if tel_line.tel_type.name == "ATM":
                        tel_line.check_atm = False
                    else:
                        tel_line.check_atm = True
                    ticl_receipt_summary_lines = {
                        'tel_receipt_log_id': self.id,
                        'name' : tel_line.product_id.name,
                        'product_id' : tel_line.product_id.id,
                        'received_date': tel_line.received_date,
                        'serial_number': tel_line.serial_number,
                        'funding_doc_type': tel_line.funding_doc_type,
                        'funding_doc_number': tel_line.funding_doc_number,
                        'ticl_project_id': tel_line.ticl_project_id,
                        'manufacturer_id': tel_line.manufacturer_id.id,
                        'condition_id': tel_line.condition_id.id,
                        'tel_type': tel_line.tel_type.id,
                        'tel_note':tel_line.tel_note,
                        'tel_cod':tel_line.tel_cod,
                        'xl_items': tel_line.xl_items,
                        'check_atm': tel_line.check_atm,
                        'inbound_charges':tel_line.inbound_charges,
                        'associated_fees':tel_line.associated_fees,
                        'misc_log_time':tel_line.misc_log_time,
                        'misc_charges':tel_line.misc_charges,
                        'service_price':tel_line.service_price,
                        'tel_unique_no':tel_line.tel_unique_no,
                        'check_move_inventory': True,
                        'repalletize': tel_line.repalletize,
                        'repalletize_charge':tel_line.repalletize_charge,
                    }
                    #print("===ticl_receipt_summary_lines==",ticl_receipt_summary_lines)
                    #count_number = int(tel_line.count_number) - tel_line.quarantine_count
                    tel_line.status_inv = 'y'

                    condition = self.env['ticl.condition'].sudo().search([('name','=','Quarantine')],limit=1)
                    lineCount,totalLnc,quaraCount = int(tel_line.count_number),int(tel_line.count_number),int(tel_line.quarantine_count)
                    if quaraCount > 0:
                        # if lineCount == quaraCount:
                        #     ticl_receipt_summary_lines['condition_id'] = condition.id
                        # else:
                        totalLnc = lineCount - quaraCount
                        ticl_receipt_summary_lines['condition_id'] = condition.id
                        log_id.ticl_receipt_summary_lines = [(0, 0, ticl_receipt_summary_lines)] * quaraCount
                    ticl_receipt_summary_lines['condition_id'] = tel_line.condition_id.id
                    log_id.ticl_receipt_summary_lines = [(0, 0, ticl_receipt_summary_lines)] * totalLnc



                if tel_line.condition_id.name != 'Quarantine':
                    tel_line.not_quarantine = 't'

        for echo_line in self.ticl_receipt_payment_lines:
            ticl_receipt_payment_lines_log = {
            'ticl_receipt_log_payment_id': self.id,
            'name' : echo_line.name,
            'ticl_units' : echo_line.ticl_units,
            'payment_rate': echo_line.payment_rate,
            'payment_amount': echo_line.payment_amount
            }
            log_id.ticl_receipt_payment_lines_log = [(0, 0, ticl_receipt_payment_lines_log)]

        receipt_log_ids = self.env['ticl.receipt'].search(
                       [('name', '=', self.name)], limit=1)
        if self.receipt_type != 'warehouse_transfer':
            self.env['ticl.monthly.service.line'].create_detail_mnth_service_inv(self, 'receipt')
        #self.env['ticl.fright.service.line'].create_detail_mnth_fright_inv(self,'receipt')
        action =self.env.ref('ticl_receiving.ticl_action_receipt_log_summary').read()[0]
        action['views'] = [(self.env.ref('ticl_receiving.ticl_receipt_log_summary_form_view').id, 'form')]
        action['res_id'] = log_id.id
        return action

        # receipt_log_ids = self.env['ticl.receipt.log.summary'].search(
        #                 [('name', '=', self.name)], limit=1)
        # self.env['ticl.monthly.service.line'].create_detail_mnth_service_inv(receipt_log_ids, 'receipt')
        
        # # self.env['ticl.fright.service.line'].create_detail_mnth_fright_inv(self,'receipt')
        # action =self.env.ref('ticl_receiving.ticl_action_receipt_log_summary').read()[0]
        # action['views'] = [(self.env.ref('ticl_receiving.ticl_receipt_log_summary_form_view').id, 'form')]
        # action['res_id'] = receipt_log_ids.id
        # return action

    #VIew Receipt Log Use Of Button Click
#     @api.multi
    def view_receipt_log(self):
        receipt_log_ids = self.env['ticl.receipt.log.summary'].search(
            [('name', '=', self.name)], limit=1)
        action =self.env.ref('ticl_receiving.ticl_action_receipt_log_summary').read()[0]
        action['views'] = [(self.env.ref('ticl_receiving.ticl_receipt_log_summary_form_view').id, 'form')]
        action['res_id'] = receipt_log_ids.id
        return action

    def help_message(self):
        return False


class ticl_receipt_line(models.Model):
    _name = 'ticl.receipt.line'
    _inherit = ['mail.thread']
    _description = "Receiving Line"

     #delivery date plus 5 days        
    # def _get_delivery_date(self):
    #     today = datetime.today()
    #     wk = today.weekday()
    #     days = 0
    #     if wk in (0,1,2,3,4,6):
    #         days = 7
    #     elif wk == 5:
    #         days = 6
    #     else:
    #         days = 5
    #     deliveryDate = today + timedelta(days=days)
    #     return deliveryDate

    #delivery date       
    # def _get_delivery_date(self):
    #     today_date = datetime.today()
    #     return today_date


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
            self.check_serial_number()
    def check_serial_number(self):
        if self.ticl_receipt_id.receipt_type != 'warehouse_transfer':
            if self.serial_number:
                status = []
                receipt_status = []
                receipt_record = self.search([('serial_number', '=', self.serial_number)])
                if receipt_record:
                    for rec in receipt_record:
                        receipt_status.append(rec.ticl_receipt_id.state)

                if 'draft' in receipt_status:
                    raise UserError('Serial Number already exists in Draft !')
                elif 'pending' in receipt_status:
                    raise UserError('Serial Number already exists in Pending !')
                elif 'inprogress' in receipt_status:
                    raise UserError('Serial Number already exists in In-Progress !')

                move_id = self.env['stock.move'].search([('serial_number', '=', self.serial_number)])
                if move_id :
                    for ids in move_id:
                        status.append(ids.status)
                if 'inventory' in status:
                    raise UserError('Serial Number already exists in Inventory !')
                elif 'assigned' in status:
                    raise UserError('Serial Number already exists in Assigned !')
                elif 'picked' in status:
                    raise UserError('Serial Number already exists in Picked !')
                elif 'packed' in status:
                    raise UserError('Serial Number already exists in Packed !')

# XL FUnction for Validation
    @api.onchange('tel_type')
    def onchange_tel_type(self):
        for line in self:
            if line.tel_type.name != 'ATM':
                self.xl_items = 'y'
            else:
                self.xl_items = 'n'

    # Filter Product Basis of Product TYpe
    # @api.onchange('tel_type', 'condition_id', 'manufacturer_id')
    # def onchange_product_type(self):
    #     res = {}
    #    #######ATM####### 
    #     if self.tel_type.name == 'ATM' and self.manufacturer_id.name =='Nautilus Hyosung' or self.manufacturer_id.name =='NCR' or \
    #     self.manufacturer_id.name =='Generic Signage/Acessories OEM' or self.manufacturer_id.name =='Office Circiut' or \
    #     self.manufacturer_id.name =='Generic' or self.manufacturer_id.name =='Diebold' or self.manufacturer_id.name =='Supra Corporation' or self.manufacturer_id.name =='Wincor':
    #         res['domain']={'product_id':[('categ_id', '=', self.tel_type.id),('manufacturer_id', '=', self.manufacturer_id.id)]}
    # 
    #     #Accessory
    #     elif self.tel_type.name == 'Accessory' and self.manufacturer_id.name =='Nautilus Hyosung' or self.manufacturer_id.name =='NCR' or \
    #     self.manufacturer_id.name =='Generic Signage/Acessories OEM' or self.manufacturer_id.name =='Office Circiut' or \
    #     self.manufacturer_id.name =='Generic' or self.manufacturer_id.name =='Diebold' or self.manufacturer_id.name =='Supra Corporation' or self.manufacturer_id.name =='Wincor':
    #         res['domain']={'product_id':[('categ_id', '=', self.tel_type.id),('manufacturer_id', '=', self.manufacturer_id.id)]}
    # 
    #     #Accessory
    #     elif self.tel_type.name == 'Signage' and self.manufacturer_id.name =='Nautilus Hyosung' or self.manufacturer_id.name =='NCR' or \
    #     self.manufacturer_id.name =='Generic Signage/Acessories OEM' or self.manufacturer_id.name =='Office Circiut' or \
    #     self.manufacturer_id.name =='Generic' or self.manufacturer_id.name =='Diebold' or self.manufacturer_id.name =='Supra Corporation' or self.manufacturer_id.name =='Wincor':
    #         res['domain']={'product_id':[('categ_id', '=', self.tel_type.id),('manufacturer_id', '=', self.manufacturer_id.id)]}
    # 
    #     #Lockbox
    #     elif self.tel_type.name == 'Lockbox' and self.manufacturer_id.name =='Nautilus Hyosung' or self.manufacturer_id.name =='NCR' or \
    #     self.manufacturer_id.name =='Generic Signage/Acessories OEM' or self.manufacturer_id.name =='Office Circiut' or \
    #     self.manufacturer_id.name =='Generic' or self.manufacturer_id.name =='Diebold' or self.manufacturer_id.name =='Supra Corporation' or self.manufacturer_id.name =='Wincor':
    #         res['domain']={'product_id':[('categ_id', '=', self.tel_type.id),('manufacturer_id', '=', self.manufacturer_id.id)]}
    # 
    #     #XL Items
    #     elif self.tel_type.name == 'XL' and self.manufacturer_id.name =='Nautilus Hyosung' or self.manufacturer_id.name =='NCR' or \
    #     self.manufacturer_id.name =='Generic Signage/Acessories OEM' or self.manufacturer_id.name =='Office Circiut' or \
    #     self.manufacturer_id.name =='Generic' or self.manufacturer_id.name =='Diebold' or self.manufacturer_id.name =='Supra Corporation' or self.manufacturer_id.name =='Wincor':
    #         res['domain']={'product_id':[('categ_id', '=', self.tel_type.id),('manufacturer_id', '=', self.manufacturer_id.id)]}
    # 
    #     else:
    #         res['domain']={'product_id':[('categ_id', '=', self.tel_type.id),('manufacturer_id', '=', self.manufacturer_id.id)]}
    #         
    #     if self.manufacturer_id:
    #         if self.product_id.manufacturer_id.id != self.manufacturer_id.id:
    #             self.product_id = False
    # 
    #     if self.tel_type.name == 'ATM' and (self.condition_id.name in ('Refurb Required - L1','Refurb Required - L2','Significant Damage') or self.condition_id.name == 'To Recommend'  or self.condition_id.name == 'Quarantine'):
    #         self.hide_cod = False
    #         if self.ticl_receipt_id.receipt_type != 'warehouse_transfer':
    #             self.tel_cod = 'Y'
    #         else:
    #             self.tel_cod = 'N'
    # 
    #     else:
    #         self.hide_cod = True
    #         self.tel_cod = ''
    #     return res

    #Check for Used Condition ATM
    @api.onchange('condition_id','product_id','tel_type')
    def onchange_move_inventory(self):
        if self.tel_type.name == 'ATM' and (self.condition_id.name in ('Refurb Required - L1','Refurb Required - L2','Significant Damage') or self.condition_id.name == 'To Recommend'  or self.condition_id.name == 'Quarantine'):
            self.hide_cod = False
            if self.ticl_receipt_id.receipt_type != 'warehouse_transfer':
                self.tel_cod = 'Y'
            else:
                self.tel_cod = 'N'
        else:
            self.hide_cod = True
            self.tel_cod = ''
        if self.ticl_receipt_id.receipt_type != 'warehouse_transfer':
            if self.tel_type.name == 'ATM' and self.condition_id.name in ('Refurb Required - L1','Refurb Required - L2','Significant Damage'):
                self.tel_cod = 'Y'
        else:
            self.tel_cod = 'N'
        if self.tel_type.name == 'ATM' and self.condition_id.name not in ('Refurb Required - L1','Refurb Required - L2','Significant Damage') or self.condition_id.name != 'To Recommend':
            self.check_move_inventory = True
        else:
            self.check_move_inventory = False


    #Misc Charges Function for TICL
    @api.onchange('misc_log_time','misc_charges')
    def _total_misc_charges(self):
        for line in self:
            rec_misc = self.env['ticl.service.charge'].search([('name', '=', 'Misc Charges'),('monthly_service_charge', '=', False)])
            if int(line.misc_log_time) >= 1:
                line.misc_charges = int(line.misc_log_time) * int(45)
            else:
               line. misc_charges = 0.00

    #Onchange for Repalletize Charge
    @api.onchange('repalletize', 'repalletize_charge')
    def _onchange_repalletize_charge(self):
        for line in self:
            if line.repalletize == 'y':
                repalletize = self.env['ticl.service.charge'].search([('name', '=', 'Palletization per Pallet')])
                line.repalletize_charge = repalletize.service_price
            else:
                line.repalletize_charge = 0.00

    # #TICL Service Charges Function
    # @api.depends('tel_type','xl_items')
    def _ticl_service_price(self):
        for line in self:
            if line.tel_type.name == "ATM":
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Signage" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Accessory" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Signage" and line.xl_items == 'n':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Accessory" and line.xl_items =='n':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Lockbox" and line.xl_items =='n':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "Lockbox" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price
    
            if line.tel_type.name == "XL" and line.xl_items =='y':
                rec_log = self.env['ticl.service.charge'].search([('name', '=', 'Receiving per Pallet')])
                if line.ticl_receipt_id.receipt_type != "warehouse_transfer":
                    line.inbound_charges = rec_log.service_price

    #Total Line Weight
    @api.depends('line_item_weight','count_number','product_weight','tel_type')
    def count_total_line_weight(self):
        for line in self:
            if str(line.count_number) != '' and line.tel_type.name != 'ATM':
                weight = line.product_weight
                count = line.count_number
                line.line_item_weight = int(weight) * int(count)
            else:
                line.line_item_weight = line.product_weight
                

    name = fields.Text(string='Description')
    tel_unique_no = fields.Char(string="Unique Id")
    received_date = fields.Date(string='Received Date', related='ticl_receipt_id.delivery_date', store=True)
    check_asn = fields.Boolean(string="Check ASN")
    ticl_receipt_id = fields.Many2one('ticl.receipt', invisible=1)
    product_id = fields.Many2one('product.product', string='Model Name',track_visibility='onchange')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer",track_visibility='onchange')
    manufacturer_id_dup = fields.Many2one('manufacturer.order', string="Manufacturer Duplicate")
    serial_number = fields.Char(string='Serial #',track_visibility='onchange')
    count_number = fields.Char(string='Count')
    condition_id = fields.Many2one('ticl.condition', string="Condition",track_visibility='onchange')
    tel_type = fields.Many2one('product.category', string="Type",track_visibility='onchange')
    type_dup = fields.Many2one('product.category', string="Type Duplicate")
    funding_doc_type = fields.Char(string = "Funding Doc Type")
    funding_doc_number = fields.Char(string = "Funding Doc No.")
    ticl_project_id = fields.Char(string = "Project Id")
    ticl_checked = fields.Boolean(string="Check")
    tel_note = fields.Char(string='Comment/Note')
    tel_cod = fields.Selection([('Y', 'Y'),('N','N')], string='COD')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')], default='y')
    hide_cod = fields.Boolean(string="Hide COD")
    status_inv = fields.Selection(string="Moved to Inventory", selection=[('y', 'Y'), ('n', 'N')])

    inbound_charges = fields.Float(string='Inbound Charges',store=True, compute=_ticl_service_price)
    misc_log_time = fields.Char(string='Misc Log Time', default=0)
    misc_charges = fields.Float(string='Misc Charges', compute=_total_misc_charges)
    associated_fees = fields.Float(string='Associated Fees') 
    repalletize_charge = fields.Float(string="Repalletize Charge")
    service_price = fields.Float(string='Price')

    check_move_inventory = fields.Boolean(string="Move Inventory")
    hide_xl_items = fields.Boolean(string="Hide XL")
    repalletize = fields.Selection(string="Repalletize", selection=[('y', 'Y'), ('n', 'N')], default='n')
    not_quarantine = fields.Selection(string="not quarantine", selection=[('NA', 'NA'),('t', 'True'), ('f', 'False')], default ='NA')
    quarantine_count = fields.Integer('Quarantine Count')
    product_weight = fields.Char(string="Product Weight")
    line_item_weight = fields.Char(string="Line Items Weight", compute=count_total_line_weight)
    monitory_value = fields.Char(string="Monitory Value")


    @api.onchange('tel_type', 'ticl_checked')
    def _all_checked(self):
        self.type_dup = self.product_id.categ_id.id
        self.manufacturer_id_dup = self.product_id.manufacturer_id.id
        for line in self:
            if line.tel_type.name == 'ATM':
                self.ticl_checked = True
                self.count_number = 1

            else:
                self.ticl_checked = False
                self.count_number = ''
    

    #Onchange for Quarantine Count
    @api.onchange('quarantine_count')
    def on_change_q_count(self):
        if self.count_number:
            if self.quarantine_count > int(self.count_number):
                self.quarantine_count = 0
                return {
                    'warning': {
                        'title': "Warning",
                        'message': "Quarantine Count Should be less than or equal to Count !",
                    }

                }


    #onchange Product Name
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.tel_type = self.product_id.categ_id.id
            self.manufacturer_id = self.product_id.manufacturer_id.id
            self.type_dup = self.product_id.categ_id.id
            self.manufacturer_id_dup = self.product_id.manufacturer_id.id
            self.product_weight = self.product_id.product_weight or False
            self.monitory_value = self.product_id.monitory_value or False
            self.xl_items = self.product_id.xl_items




#Ticl Receipts Payments 
class ticl_receipt_payment(models.Model):
    _name = 'ticl.receipt.payment'
    _description = "Ticl Receipts Payment"

    name = fields.Text(string='Description')
    ticl_receipt_payment_id = fields.Many2one('ticl.receipt', string='Receipts Payment ID', invisible=1)
    payment_amount = fields.Char(string='Amount')
    payment_rate = fields.Char(string='Rate')
    ticl_units = fields.Char(string='Units')

                
