import time
from datetime import datetime,timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime as real_datetime
import logging
_logger = logging.getLogger(__name__)

class ticl_shipment_log_ext(models.Model):
    _name = 'ticl.shipment.log.ext'
    _description = "Shipment Log"
    _order = 'id desc'
    
    name = fields.Char(string='Shipment Number', index=True )
    tel_note = fields.Char(string='Comment/Note')
    delivery_date = fields.Datetime(string='Delivery Date')
    echo_tracking_id = fields.Char(string="Tracking #")
    delivery_date_new = fields.Date(string='Delivery Date')
    pick_up_date_new = fields.Date(string='Pick up Date')
    activity_date_new = fields.Date(string='Activity Date')

    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)')
    sending_location_id = fields.Many2one('res.partner', string='Receiving Location')
    warehouse_id = fields.Many2one('stock.warehouse', string='Receiving warehouse', default=lambda self: self.env.user.warehouse_id.id)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    asn_bol_type = fields.Selection([('asn', 'ASN'),('bol','BOL')], string='Type', default='bol')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('picked', 'Picked'),
        ('packed', 'Packed'),('shipped', 'Shipped'),('approved','Approved')],
        string='Status', default='draft')

    ticl_ship_lines = fields.One2many('ticl.shipment.log.line.ext', 'ticl_ship_id', ondelete='cascade')
    start_quarantine_date = fields.Date(string='Start Quarantine Date')
    end_quarantine_date = fields.Date(string='End Quarantine Date')
    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier')
    pick_up_date = fields.Datetime(string='Pick up Date')
    accepted_date =  fields.Datetime(string='Accepted Date')
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee')
    activity_date =  fields.Datetime(string='Activity Start Date')
    equipment_date =  fields.Datetime(string='Equipment Shipping Request Date')
    shipment_types = fields.Selection([('Regular', 'Regular'),('Inventory Transfer', 'Inventory Transfer'),
                                      ('Guaranteed', 'Guaranteed'),('Expedited', 'Expedited'),('Non Freight','Non Freight')], string='Shipment Type'
                                      ,default='Regular',track_visibility='onchange')
    receiving_location_id = fields.Many2one('stock.location', string='Destination Location',default='')

    @api.model
    def create(self, vals):
        sequence = '/'
        vals['name'] = sequence
        return super(ticl_shipment_log_ext, self).create(vals)
    
    # @api.multi
    def picked_shipment_log_ext(self):
       # location = self.env['stock.location'].sudo().search([('name','=',self.warehouse_id.name)], limit=1)
        today_day = datetime.strptime(str(real_datetime.datetime.today()),
                                      '%Y-%m-%d %H:%M:%S.%f').weekday() + 1 % 7
        if today_day in [0, 1, 2, 3]:
            pick_up_date_new = str(datetime.strptime(str(real_datetime.datetime.today()),
                                                        '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=2))
        elif today_day in [4, 5]:
            pick_up_date_new = str(datetime.strptime(str(real_datetime.datetime.today()),
                                                        '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=4))
        elif today_day in [6]:
            pick_up_date_new = str(datetime.strptime(str(real_datetime.datetime.today()),
                                                        '%Y-%m-%d %H:%M:%S.%f') + timedelta(days=3))
        emp = self.env['hr.employee'].search([('user_id','=',self.user_id.id)])
        
        # receiving_location_id = False
        # if not self.receiving_location_id.id:
        #     receiving_location_id = self.sending_location_id.id

        vals = {
            'delivery_date_new':self.delivery_date_new,
            'shipment_date': pick_up_date_new,
            'receiving_location_id':self.sending_location_id.id,
            'sending_location_id':self.receiving_location_id.id,
            'warehouse_id':self.warehouse_id.id,
            'equipment_date':self.equipment_date,
            'shipment_type':self.shipment_types,
#             'ship_stock_move_id':self.id,
            #'tender_stock_move_id':self.id,
            'appointment_date_new':self.pick_up_date_new,
            'activity_date_new': self.activity_date_new,
            'hr_employee_id': emp.id,
            }
        _logger.warning("=====vals==",vals)
        ticl_ship_lines = []
        pending = self.ticl_ship_lines.filtered(lambda x: x.tel_available == 'N')
        if pending:
            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            context['message'] = "Some Product's not available."
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
        
        for line in self.ticl_ship_lines:
            if not self.sending_location_id.id:
                print("-------rrrrrr")
                domain = [
                        ('product_id','=',line.product_id.id),
                        ('status','=','inventory')
                    ]
                    
                if line.serial_number:
                    domain += [('serial_number','=',line.serial_number)]
                moves = self.env['stock.move.line'].sudo().search(domain)
                receiving_location_id = moves[0].ticl_warehouse_id.id
                print("-------rrrrrr",receiving_location_id)
            if line.tel_type.name == "ATM":                   
                rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound per ATM / Pallet')])
                outbound_charges = rec_log.shipment_service_charges
            
            if line.tel_type.name == "Signage":            
                rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound Services per Signage Piece')])
                outbound_charges = rec_log.shipment_service_charges

            if line.tel_type.name == "XL":
                rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound Services for XL Items')])
                outbound_charges = rec_log.shipment_service_charges

            if line.tel_type.name == "Accessory":
                rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound per ATM / Pallet')])
                outbound_charges = rec_log.shipment_service_charges

            if line.tel_type.name == "Lockbox":
                rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'Outbound Small Item (non-freight)')])
                outbound_charges = rec_log.shipment_service_charges 
            lot = self.env['stock.production.lot'].search([('name', '=', line.serial_number)])
            lot_id = 0
            for l in lot:
                lot_id = l.id
                # if l.stock_move_id.status == 'inventory':
                #     lot_id = l.id

            ticl_ship_lines.append((0,0,{
                "tel_type":line.tel_type.id,
                "ticl_checked":line.ticl_checked,
                "product_id" :line.product_id.id,
                "lot_id":lot_id,
                "count_number" :1,
                "manufacturer_id":line.product_id.manufacturer_id.id,
                "hide_cod":line.hide_cod,
                "hide_xl_items":line.hide_xl_items,
                "xl_items":'n',
                "shipment_date":line.shipment_date,
                "tel_note":line.tel_note,
                "funding_doc_type":line.funding_doc_type,
                "funding_doc_number":line.funding_doc_number,
                "ticl_project_id":line.ticl_project_id,
#                 "tel_available":line.tel_available,
                "shipment_service_charges":line.shipment_service_charges,
                "product_weight":line.product_id.product_weight,
                "ship_stock_move_line_id":line.move_id.id,
                "common_name":line.common_name,
                "tid":line.tid,
                "outbound_charges": outbound_charges
            }))
        prod = self.ticl_ship_lines.filtered(lambda z: z.tel_type.name == 'ATM' and z.product_id.ticl_product_id.name != False)
        # if prod:
        #     stand_lines = self.env['ticl.shipment.log'].create_stand(self,prod)
        #     if stand_lines:
        #         ticl_ship_lines += stand_lines
        vals.update({'ticl_ship_lines':ticl_ship_lines,'sending_location_id':self.receiving_location_id.id})
        shp_log = self.env['ticl.shipment.log'].create(vals)
        print("==shp_log====",shp_log)
        self.name = shp_log.name
        self.state = 'approved'
        return True
    
    
class ticl_shipment_log_line_ext(models.Model):
    _name = 'ticl.shipment.log.line.ext'
    _description = "Shipping Log Line"


    @api.depends('ship_stock_move_id.status')
    @api.onchange('product_id')
    def onchange_model_name(self):
        tel_obj = self.env['stock.move']
        if self.product_id.id != None:
            tel_no = tel_obj.search([('status', '=', 'inventory'),('warehouse_id', '=', self.ticl_ship_id.warehouse_id.id),('product_id','=',self.product_id.id)],limit=1)
            print ("============ppppppppp========", tel_no)           
            for res in self:
                if res.product_id.id == tel_no.product_id.id:
                    for tel in tel_no:
                        vals = {
                        'product_id' : tel.product_id.id or False,
                        'manufacturer_id' : tel.product_id.manufacturer_id.id or False,
                        'condition_id' : tel.product_id.condition_id.id or False,
                        'tel_type' : tel.product_id.categ_id.id or False,
                        'ship_stock_move_id':tel.id
                        }
                        self.update(vals)

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

# TICL Service Charges Fnction 
    @api.depends('tel_type', 'xl_items', 'shipment_service_charges')
    def _get_shipment_service_charges(self):
        for line in self:
            rec_log = self.env['ticl.shipment.charge'].search([('name', '=', 'ATM')])
            if line.tel_type.name == "ATM":
                line.shipment_service_charges = rec_log.shipment_service_charges

            rec_signage = self.env['ticl.shipment.charge'].search([('name', '=', 'Signage'),('xl_items', '=', 'y')])
            if line.tel_type.name == "Signage" and line.xl_items == "y":
                line.shipment_service_charges = rec_signage.shipment_service_charges

            rec_signage = self.env['ticl.shipment.charge'].search([('name', '=', 'Signage'),('xl_items', '=', 'n')])
            if line.tel_type.name == "Signage" and line.xl_items == "n":
                line.shipment_service_charges = rec_signage.shipment_service_charges

            rec_accessory = self.env['ticl.shipment.charge'].search([('name', '=', 'Accessory'),('xl_items', '=', 'y')])
            if line.tel_type.name == 'Accessory' and line.xl_items == 'y':
                line.shipment_service_charges = rec_accessory.shipment_service_charges

            rec_accessory = self.env['ticl.shipment.charge'].search([('name', '=', 'Accessory'),('xl_items', '=', 'n')])
            if line.tel_type.name == 'Accessory' and line.xl_items == 'n':
                line.shipment_service_charges = rec_accessory.shipment_service_charges

    # @api.depends('tel_available')
    # def _check_availability(self):
    #     for line in self:
    #         if line.ticl_ship_id.state == 'draft':
    #             domain = [
    #                 ('product_id','=',line.product_id.id),
    #                 ('status','=','inventory')
    #             ]
    #
    #             if line.serial_number:
    #                 domain += [('serial_number','=',line.serial_number)]
    #             moves = self.env['stock.move'].sudo().search(domain)
    #             if moves:
    #                 line.update({'tel_available': 'Y'})
    #             else:
    #                 line.update({'tel_available': 'N'})
    #         else:
    #             line.update({'tel_available': 'Y'})
    
    name = fields.Text(string='Description')
    shipment_date = fields.Datetime(string='Shipment Date', default=datetime.today())
    ticl_ship_id = fields.Many2one('ticl.shipment.log.ext', string='Shipment ID', invisible=1)
    product_id = fields.Many2one('product.product', string='Model Name')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    serial_number = fields.Char(string='Serial #')
    count_number = fields.Char(string='Count')
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    tel_type = fields.Many2one('product.category', string="Type")
    funding_doc_type = fields.Char(string = "Funding Doc Type", default=lambda self: self.env.user.funding_doc_type)
    funding_doc_number = fields.Char(string = "Funding Doc No.", default=lambda self: self.env.user.funding_doc_number)
    ticl_project_id = fields.Char(string = "Project Id", default=lambda self: self.env.user.ticl_project_id)
    ticl_checked = fields.Boolean(string="Check")
    tel_note = fields.Char(string='Comment/Note')
    tel_cod = fields.Selection([('Y', 'Y'),('N','N')], string='COD')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')], default='y')
    hide_cod = fields.Boolean(string="Hide COD")

    shipment_service_charges = fields.Float(string='Charges', compute="_get_shipment_service_charges")

    hide_xl_items = fields.Boolean(string="Hide XL")
    tel_available = fields.Selection([('Y', 'Available'),('N','Pending')], string='Availablity')
    tid = fields.Char(string='TID')
    common_name = fields.Char(string='Common Name')
    move_id = fields.Many2one('stock.move.line', string='Move Id')
    outbound_charges = fields.Float(string='Outbound Charges')
    activity_date =  fields.Datetime(string='Activity Start Date')
    eqp_grp = fields.Char(string='eqp_grp')
