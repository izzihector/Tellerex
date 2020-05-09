# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
import calendar


class Picking(models.Model):
    _inherit = "stock.picking"
    _order = 'origin desc'

    tel_receive_id = fields.Many2one("tel.receiving", string="TEL Received ID")
    tel_receipt_id = fields.Many2one("ticl.receipt", string="TEL Receipt ID")
    tel_receipt_summary_id = fields.Many2one('ticl.receipt.log.summary', string="TEL Receipt Summary ID")
    tel_note = fields.Char(string='Comment/Note')
    tel_cod = fields.Selection([('Y', 'Y'),('N','N')], string='COD')
    shipping_status = fields.Selection(string=" Shipping Status", selection=[('NA', 'NA'), ('picked', 'Picked'), ('packed', 'Packed'),
                                                          ('shipped', 'Shipped')], default='NA')
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')], default='y')


    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier')
    pick_up_date = fields.Date(string='Pick up Date')
    accepted_date =  fields.Date(string='Accepted Date')
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee')

    inbound_charges = fields.Float(string='Inbound Charges')
    misc_log_time = fields.Char(string='Misc Log Time', default=0)
    misc_charges = fields.Float(string='Misc Charges')
    outbound_associated_fees = fields.Float(string='Outbound Associated Fees')
    associated_fees = fields.Float(string='Associated Fees')
    cod_charges = fields.Float(string='COD Charges')
    repalletize_charge = fields.Float(string="Repalletize Charge")

    service_price = fields.Float(string='Price')

global_cod_value_ids = []
# Stock Move Object For Inventory
class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'mail.thread', 'mail.activity.mixin']
    _order = 'origin desc'

    #override Function for move
    def _action_confirm(self, merge=True, merge_into=False):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        :param: merge: According to this boolean, a newly confirmed move will be merged
        in another move of the same picking sharing its characteristics.
        """
        move_create_proc = self.env['stock.move']
        move_to_confirm = self.env['stock.move']
        move_waiting = self.env['stock.move']

        to_assign = {}
        for move in self:
            # if the move is preceeded, then it's waiting (if preceeding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting |= move
            else:
                if move.procure_method == 'make_to_order':
                    move_create_proc |= move
                else:
                    move_to_confirm |= move
            if move._should_be_assigned():
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                if key not in to_assign:
                    to_assign[key] = self.env['stock.move']
                to_assign[key] |= move

        # create procurements for make to order moves
        for move in move_create_proc:
            values = move._prepare_procurement_values()
            origin = (move.group_id and move.group_id.name or (move.origin or move.picking_id.name or "/"))
            self.env['procurement.group'].run(move.product_id, move.product_uom_qty, move.product_uom, move.location_id, move.rule_id and move.rule_id.name or "/", origin,
                                              values)

        move_to_confirm.write({'state': 'confirmed'})
        (move_waiting | move_create_proc).write({'state': 'waiting'})

        # assign picking in batch for all confirmed move that share the same details
        for moves in to_assign.values():
            moves._assign_picking()
        self._push_apply()
        if merge and self._context.get('merge'):
            return self._merge_moves(merge_into=merge_into)
        return self


#     @api.multi
    def hide_filter_fields(self):
        return ['shipping_status', 'accepted_date', 'message_needaction',
               'activity_ids', 'returned_move_ids', 'backorder_id', 'bill_of_lading_number',
               'cod_employee_id', 'company_id', 'count_number', 'create_uid', 'create_date',
               'date', 'processed_date', 'name', 'partner_id', 'location_dest_id',
               'move_dest_ids', 'route_ids', 'hr_employee_id', 'date_expected',
               'message_follower_ids', 'message_channel_ids', 'message_partner_ids',
               'product_function', 'product_height', 'tel_receipt_summary_id', 'product_uom_qty',
               'message_is_follower', 'write_uid', 'write_date', 'product_lenght', 'message_main_attachment_id',
               'message_has_error', 'message_ids', 'monthly_service_charge', 'monthly_service_charge_total',
               'activity_date_deadline', 'activity_summary', 'activity_type_id',
               'note', 'notified', 'oem_pn', 'old_name', 'picking_type_id', 'order_from_receipt',
                'origin_returned_move_id', 'move_orig_ids', 'owner_id', 'package_level_id',
                'add_pallet', 'pick_up_date', 'product_packaging','service_price', 'priority', 'group_id',
                'product_tmpl_id', 'product_id', 'propagate', 'product_qty', 'has_tracking', 'ticl_project_id',
                'receive_date', 'recycled_date', 'reference', 'repalletize', 'user_id', 'activity_user_id',
                'scrapped', 'sequence', 'shippable', 'shipped_date', 'shipping_carrier_id',
                'origin', 'location_id', 'product_squre_feet', 'rule_id', 'procure_method',
                'picking_partner_id', 'picking_id', 'price_unit', 'product_uom',
                'attachment_ids', 'tel_user_ids', 'part_name', 'weight', 'additional', 'product_width',
                'xl_items', 'total_service_charge', 'tel_receipt_id', 'tel_receive_id', 'tel_receipt_summary_id',
                'fund_doc_type', 'fund_doc_number', 'states', 'state', 'refurbishment_charges', 'restrict_partner_id',
                'inventory_id', 'scrap_ids', 'picking_type_entire_packs', 'move_line_ids', 'move_line_nosuggest_ids',
                'show_operations', 'picking_code', 'product_type'
            ]


    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(StockMove, self).fields_get(allfields, attributes=attributes)
        for field in self.hide_filter_fields():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res


#     @api.multi
    def get_cod_values(self):
        res =[]
        stock_move = self.env['stock.move'].search([('id', '=', global_cod_value_ids)])
        for ids in stock_move:
            res.append({'serial_number':ids.serial_number,
                        'tel_unique_no': ids.tel_unique_no,
                        'origin': ids.origin,
                        'received_date': ids.received_date,
                        'processed_date': ids.processed_date,
                        'manufacturer_id': ids.manufacturer_id.name,
                        'product_id': ids.product_id.name,

                        })
            global_cod_value_ids.remove(ids.id)
        return res

#     @api.multi
    def print_report(self):
        stock_ids = []
        res = {}
        for ids in self.ids:
            stock_move = self.env['stock.move'].search([('id', '=', ids)])
            if stock_move.condition_id.name == 'Factory Sealed' or stock_move.condition_id.name == 'Refurb Complete' or stock_move.condition_id.name == 'New':
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view or False
                context = dict(self._context or {})
                context['message'] = 'COD is not available!'
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
            else:
                stock_move_id = self.env['stock.move'].search([('id', '=', ids)])
                ticl_receipt_summary_id = self.env['ticl.receipt.log.summary.line'].search(
                    [('ticl_receipt_summary_id', '=', stock_move_id.origin), ('serial_number', '=', stock_move_id.serial_number)], limit=1)

                if len(ticl_receipt_summary_id.attachment_ids_hdd) < 2 or len(
                        ticl_receipt_summary_id.attachment_ids_epp) < 2 or len(
                        ticl_receipt_summary_id.attachment_ids) < 5:
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view or False
                    context = dict(self._context or {})
                    context['message'] = 'COD is not available!'
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
                stock_ids.append(ids)
                global_cod_value_ids.append(ids)
        datas = {
            'doc_ids': self.ids,
            'doc_model': 'stock.move',
            'docs': self,
        }
        return {
            'type': 'ir.actions.report',
            'report_name': 'ticl_receiving.data_destruction_report_pdf',
            'report_type': 'qweb-pdf',
            'report_file': 'ticl_receiving.data_destruction_report_pdf',
            'name': 'stock.move',
            'data': datas,
            'docs' : datas,
            'doc_ids': self.ids,
        }

#     @api.multi
    def get_report_images(self, inv):
        origin_id = self.env['ticl.receipt.log.summary'].search([('name','=',inv['origin'])])
        ticl_receipt_summary_id = self.env['ticl.receipt.log.summary.line'].search([('ticl_receipt_summary_id','=',origin_id.id),('serial_number','=',inv['serial_number'])])
        return ticl_receipt_summary_id

#     @api.multi
    def get_report_rec(self, inv):
        return self.env['ticl.receipt.log.summary.line'].search(
                [('ticl_receipt_summary_id', '=', inv['origin']),('serial_number','=',inv['serial_number'])])


 #    #Misc Charges Function for TICL
 #    @api.onchange('misc_log_time','misc_charges')
 #    def _total_misc_charges(self):
 #        for line in self:
 #            rec_misc = self.env['ticl.service.charge'].search([('name', '=', 'Misc Charges'),('monthly_service_charge', '=', False)])
 #           # misc_charges = 0.00
 #            if int(line.misc_log_time) >= 1:
 #                line.misc_charges = int(line.misc_log_time) * int(rec_misc.service_price)
 #                print("==misc999999999999999c====",line.misc_charges)
 #            else:
 #               line. misc_charges = 0.00

 #    #Onchange for Repalletize Charge
    # @api.onchange('repalletize', 'repalletize_charge')
 #    def _onchange_repalletize_charge(self):
 #        for line in self:
 #            if line.repalletize == 'y':
 #                repalletize = self.env['ticl.service.charge'].search([('name', '=', 'Repalletize'),('monthly_service_charge', '=', False)])
 #                line.repalletize_charge = repalletize.service_price
 #            else:
 #                line.repalletize_charge = 0.00

 #    #TICL Service Charges Function 
 #    @api.depends('tel_type', 'misc_log_time', 'xl_items', 'service_price','associated_fees','repalletize')
 #    def _total_service_price(self):
 #        for line in self:
 #            rec_log = self.env['ticl.service.charge'].search([('name', '=', 'ATM'),('monthly_service_charge', '=', False)])
 #            if line.tel_type.name == "ATM":             
 #                line.service_price = rec_log.service_price + line.associated_fees + line.misc_charges 
 #                if line.repalletize == "y":
 #                    line.service_price = rec_log.service_price + line.associated_fees + line.repalletize_charge
           
 #            rec_signage = self.env['ticl.service.charge'].search([('name', '=', 'Signage'),('xl_items', '=', 'y'),('monthly_service_charge', '=', False)])
 #            if line.tel_type.name == "Signage":             
 #                line.service_price = rec_log.service_price + line.associated_fees + line.misc_charges
 #                if line.repalletize == "y":
 #                    line.service_price = rec_log.service_price + line.associated_fees + line.repalletize_charge

 #            rec_accessory = self.env['ticl.service.charge'].search([('name', '=', 'Accessory'),('xl_items', '=', 'y'),('monthly_service_charge', '=', False)])
 #            if line.tel_type.name == "Accessory":              
 #                line.service_price = rec_log.service_price + line.associated_fees
 #                if line.repalletize == "y":
 #                    line.service_price = rec_log.service_price +  line.associated_fees + line.repalletize_charge

    move_to_inv = fields.Selection([('y', 'Y'), ('n', 'N')], string="Moved to Inventory")
    tel_receive_id = fields.Many2one("tel.receiving", string="TEL Received ID")
    tel_receipt_id = fields.Many2one("ticl.receipt", string="TEL Receipt ID")
    tel_receipt_summary_id = fields.Many2one('ticl.receipt.log.summary', string="TEL Receipt Summary ID")
    tel_unique_no = fields.Char(string="Unique Id")
    tel_note = fields.Char(string='Comment/Note')
    tel_cod = fields.Selection([('Y', 'Y'),('N','N')], string='COD')
    shipping_status = fields.Selection(string=" Shipping Status", selection=[('NA', 'NA'), ('picked', 'Picked'), ('packed', 'Packed'),
                                                          ('shipped', 'Shipped')], default='NA')
    attachment_ids = fields.Many2many('ir.attachment', string='Upload BOL #')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')])

    shipping_carrier_id = fields.Many2one('shipping.carrier', string='Shipping Carrier')
    pick_up_date = fields.Date(string='Pick up Date')
    accepted_date =  fields.Date(string='Accepted Date')
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee')
    future_ship_date = fields.Date(string="Future Ship Date",track_visibility='onchange')
    future_ship_location =  fields.Many2one('stock.location', string="Future Ship Location",track_visibility='onchange')
    received_date = fields.Date(string='Received Date')
    notified = fields.Boolean(string='Notification', default=False)
    repalletize = fields.Selection(string="Repalletize", selection=[('y', 'Y'), ('n', 'N')])
    status = fields.Selection([('inventory', 'Inventory'),('assigned', 'Assigned'),('picked', 'Picked'),('packed', 'Packed'),('shipped', 'Shipped'),
        ('sold', 'Sold'),('cancel', 'Cancelled'),('recycled', 'Recycled')], string='Status', default='inventory',track_visibility='onchange')
    processed_date = fields.Date(string='Date Processed')

    monthly_service_charge = fields.Float('Monthly Service Charges',store=True)
    monthly_service_charge_total = fields.Char('Monthly Service Charges')
    total_service_charge = fields.Char(string="total_service_charge")

    inbound_charges = fields.Float(string='Inbound Charges')
    misc_log_time = fields.Char(string='Misc Log Time', default=0)
    misc_charges = fields.Float(string='Misc Charges')
    associated_fees = fields.Float(string='Inbound Associated Fees')
    cod_charges = fields.Float(string='COD Charges')
    repalletize_charge = fields.Float(string="Repalletize Charge")
    service_price = fields.Float(string='Price')


    outbound_charges = fields.Float(string='Outbound Charges')
    outbound_associated_fees = fields.Float(string='Outbound Associated Fees')
    #associated_fees = fields.Float(string='Outbound Associated Fees')
    shipment_date = fields.Date(string='Shipped Date')


    cod_employee_id = fields.Many2one('hr.employee', string='COD Employee')
    refurbishment_charges = fields.Float('Refurbishment Charges',store = True)
    old_name = fields.Char(string='Old Receipt Id', index=True)
    shipment_id = fields.Char("Shipment Id")

    # receiving_time_log = fields.One2many("common.misc.line", "receiving_move_ids",
    #                                      string="Misc Log Time")
    scrap_tel_note = fields.Char(string='Scrap Comments')
    sending_location_id = fields.Many2one('res.partner', string='Origin Location')

    @api.onchange('misc_log_time', 'misc_charges')
    def _total_misc_charges(self):
        count = []
        for ids in self.ids:
            # receipt_misc = self.env['common.misc.line'].search([('receiving_move_ids', '=', ids)])
            # for x in receipt_misc:
            #     count.append(x.work_time)
            # self.misc_log_time = sum(count)
            self.misc_log_time = 0

#     @api.multi
    # def ticl_action_show_details_moves_receiving(self):
    #     self.ensure_one()
    #     view = self.env.ref('ticl_receiving.receiving_view_misc_details')
    #     warehouse = self.env['stock.warehouse'].search([('name','=',self.location_dest_id.name)])

    #     return {
    #         'name': _('Misc Details'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'stock.move',
    #         'views': [(view.id, 'form')],
    #         'view_id': view.id,
    #         'target': 'new',
    #         'res_id': self.id,
    #         'context': {'default_model_name': self.product_id.id,
    #                     'default_serial_number': self.serial_number,
    #                     'default_warehouse_id': warehouse.id,},

    #     }

    #Refurbishment Amount add in Stock
    @api.onchange('condition_id')
    def onchange_refurbishment_amount(self):
        if self.condition_id.name == 'Refurb Complete':
            x =self.env['ticl.refurbishment.charge'].search([('name', '=', self.condition_id.name)])
            self.refurbishment_charges = x.service_price
        else:
            self.refurbishment_charges = 0


    @api.onchange('future_ship_date','monthly_service_charge_total')
    def monthly_charges(self):
        monthly_charge = self.monthly_service_charge
        received_date = str(self.received_date).split(" ")
        future_ship_date = str(self.future_ship_date).split(" ")
        date1 = datetime.strptime(received_date[0], "%Y-%m-%d")
        date2 = datetime.strptime(future_ship_date[0], "%Y-%m-%d")
        months_str = calendar.month_name
        months = []
        while date1 <= date2:
            month = date1.month
            year = date1.year
            month_str = months_str[month][0:3]
            months.append("{0}-{1}".format(month_str, str(year)[-2:]))
            next_month = month + 1 if month != 12 else 1
            next_year = year + 1 if next_month == 1 else year
            y =  str(date1.replace(month=next_month, year=next_year)).split(" ")
            x = y[0]
            rd_1 = x.split('-')
            date1 = datetime.strptime("{0}-{1}-{2} 00:00:00".format(rd_1[0],rd_1[1],1), '%Y-%m-%d %H:%M:%S')
        if len(months) == 1:
            charges = monthly_charge
        else:
            charges = monthly_charge * len(months)
        self.monthly_service_charge_total = charges

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        # self.env['ticl.monthly.service.line'].create_detail_mnth_service_inv(res, 'inventory')
        return res


#     @api.multi
    def write(self,values):
        for i in self:
            monthly_charge = i.monthly_service_charge
            received_date = str(i.received_date).split(" ")
            months = []
            if values.get('future_ship_date'):
                future_ship_date = str(values['future_ship_date']).split(" ")
                date1 = datetime.strptime(received_date[0], "%Y-%m-%d")
                date2 = datetime.strptime(future_ship_date[0], "%Y-%m-%d")
                months_str = calendar.month_name
                while date1 <= date2:
                    month = date1.month
                    year = date1.year
                    month_str = months_str[month][0:3]
                    months.append("{0}-{1}".format(month_str, str(year)[-2:]))
                    next_month = month + 1 if month != 12 else 1
                    next_year = year + 1 if next_month == 1 else year
                    y = str(date1.replace(month=next_month, year=next_year)).split(" ")
                    x = y[0]
                    rd_1 = x.split('-')
                    date1 = datetime.strptime("{0}-{1}-{2} 00:00:00".format(rd_1[0], rd_1[1], 1), '%Y-%m-%d %H:%M:%S')
            if len(months) == 1:
                charges = monthly_charge
            else:
                charges = monthly_charge * len(months)
            values['monthly_service_charge_total'] = charges
            if 'condition_id' in values.keys():
                if values['condition_id'] == 5:
                    x = self.env['ticl.refurbishment.charge'].search([('name', '=', 'Refurb Complete')])
                    values['refurbishment_charges'] = x.service_price
                elif values['condition_id'] != 5:
                    values['refurbishment_charges'] = 0

            return super(StockMove, self).write(values)

            # tel_receipt_summary_line = self.env['ticl.receipt.log.summary.line'].search([('tel_unique_no', '=', i.tel_unique_no)])
            # print("Line number 430+++++++", tel_receipt_summary_line)
            # if 'status' in values.keys():
            #     print("Inside if line no 432")
            #     tel_receipt_summary_line.write({'receipt_status': values['status']})
            # return super(StockMove, self).write(values)


#This method is called from a cron job. to send notifications
    #@api.model
    def _run_future_notifications(self):
        self.env.cr.execute("""select id,future_ship_date,warehouse_id from stock_move 
                                where future_ship_date::date = now()::date and
                                notified = false""")
        moves = self.env.cr.fetchall()
        self.env.cr.execute("select id from ir_model where model='stock.move'")
        model = self.env.cr.fetchall()
        for move in moves:
            users = self.env['res.users'].search([('warehouse_id','=',int(move[2]))])
            if users:
                for user in users:
                    self.env['mail.activity'].create({
                        'activity_type_id': 4,
                        'note': 'Future Notification',
                        'res_id': move[0],
                        'res_model_id': model[0],
                        'user_id':user.id,
                        'create_user_id':user.id,
                        'summary':'Stock Move Future Notification',
                        'res_name':'Future Notification'
                        })
                self.env.cr.execute("""update stock_move set notified = true where id = %s""", [move[0]])



# Stock picked Pop Message
#     @api.multi
    def picked_button(self):
        for r in self:
            if r.shipping_status == "picked":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="Selected item(s) already in Picked status!"
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
            elif r.shipping_status in ["packed", "shipped"]:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="You can not move item(s) to previous status!"
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
            else:
                r.shipping_status = "picked"

# Stock picked First Pop Message and Packed
    # @api.multi
    def packed_button(self):
        for r in self:
            if r.shipping_status ==  "NA":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="Please move item(s) to Picked status first!"
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
            elif r.shipping_status == "packed":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="Selected item(s) already in Packed status!"
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
            elif r.shipping_status == "shipped":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="You can not move item(s) to previous status!"
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
            else:
                r.shipping_status = "packed"

# Stock shipped Pop Message
    # @api.multi
    def shipped_button(self):
        for r in self:
            if r.shipping_status ==  "NA":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="Please move item(s) to Picked status first!"
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
            elif r.shipping_status  == "picked":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="Please move item(s) to Packed status first!"
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
            elif r.shipping_status == "shipped":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view  or False
                context = dict(self._context or {})
                context['message']="Selected item(s) already in Shipped status!"
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
            else:
                r.shipping_status = 'shipped'


    def move_to_refurbishment(self):
        for ids in self:
            ids.condition_id = 6


#Serial Number History code started
    # @api.multi
    def exception_wizard(self, message):
        #raise all exceptions
        context = dict(self._context or {})
        context['message'] = message
        return {
            'name': 'Serial Number History',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'serial.number.history',
            'view': [('view', 'form')],
            'target': 'new',
            'context': context,
        }

    # @api.multi
    def mail_message(self, domain, order=None, limit=None):
        mail_messages = self.env['mail.message'].search(domain, order=order, limit=limit)
        return mail_messages

    # @api.multi
    def mail_tracking_value(self, domain):
        tracks = self.env['mail.tracking.value'].search(domain)
        return tracks

    # @api.multi
    def get_raw_html(self,a,b,c,d,e,f,g,h,i,j):
        create_raw_html = """
            <span>
            <div class="o_thread_message  o_mail_not_discussion" data-message-id="6028" style="width: 50%;float: left;">
                            <h5 style="text-align: -webkit-center;">Receipt</h5>
                            <div class="o_thread_message_core" >
                                {0}
                                <div class="o_thread_message_content">
                            <ul class="o_mail_thread_message_tracking">
                               {1}

                               {2}

                                </ul>
                                </div>
                                </div>
                            </div>
                            {3}
                            {4}
                            {5}
                             <div class="o_thread_message  o_mail_not_discussion" data-message-id="6029" style="top: 8%;position: absolute;right: 100px;">
                            <h5 style="text-align: -webkit-center;">Shipment</h5>
                            <div class="o_thread_message_core" >
                                {6}
                              
                                </div>
                            </div>
                          
                  </span>          
                            
            """.format(a, "".join(b), "".join(c),"".join(d),"".join(e),f +"".join(g),h + "".join(i) + "".join(j) + """</div></div>""")

        return create_raw_html

    #Serial Number History code
    # @api.multi
    def serial_num_history(self):
        field_value = False
        vals = ''

        if len(self.ids) > 1:
            return self.exception_wizard("<h6>Please do not Select Multiple Records !</h6>")
        context = dict(self._context or {})

        if self.categ_id.name != 'ATM':
            return self.exception_wizard("<h6>History not found for the Selected Item !</h6>")
        else:
            receipt_id = self.env['ticl.receipt'].search([('name', '=', self.origin)])
            domain = [('res_id', '=', receipt_id.id),('model', '=', 'ticl.receipt'),('body', '!=', '')]
            mail_message_create = self.mail_message(domain)

            if not mail_message_create:
                return self.exception_wizard("<h6>History not found for the Selected ATM !</h6>")

            #Created By Information

            create_time_data = []
            user_date = """<p class="o_mail_info text-muted">
                                    <strong data-oe-model="res.partner" data-oe-id="" class="o_thread_author ">
                                      Created By --> {0}
                                    </strong>
                                    - <small style="color:#5ec269;font-size:12px;" >{1}</small>
                                </p>""".format(mail_message_create.reply_to, mail_message_create.create_date)

            track_domain = [('mail_message_id', '=', mail_message_create.id + 1)]
            mail_tracking_create = self.mail_tracking_value(track_domain)

            for data in mail_tracking_create:
                if data.field_desc == "Delivery Date":
                    field_value = data.new_value_datetime
                else:
                    field_value = data.new_value_char
                create_time_data.append(""" <li>
                                    {0}:
                                    <span>
                                        {1}
                                    </span>
                                </li>""".format(data.field_desc, field_value))


            #### End Created by ###

            ticl_line_id = self.env['ticl.receipt.line'].search([
                ('ticl_receipt_id', '=', receipt_id.id),
                ('serial_number', '=', self.serial_number)],
                limit=1 )

            line_domain = [('res_id', '=', ticl_line_id.id),('model', '=', 'ticl.receipt.line'),('body', '=', '')]
            order="id asc"
            mail_message_line_create = self.mail_message(line_domain,order)

            create_line_time_data = []

            mail_line_tracking_create = self.env['mail.tracking.value'].search([('mail_message_id', 'in', mail_message_line_create.ids)])
            for data in mail_line_tracking_create:

                if not data.old_value_char:
                    if data.field_desc == "Received Date":
                        field_value = data.new_value_datetime
                    else:
                        field_value = data.new_value_char
                    create_line_time_data.append(""" <li>
                                        {0}:
                                        <span>
                                            {1}
                                        </span>
                                    </li>""".format(data.field_desc, field_value))

                if data.old_value_char:
                    create_line_time_data.append(""" 
                        <div class="o_thread_message  o_mail_not_discussion"  style="width: 50%;">
                        <div class="o_thread_message_core" >
                                                    <p class="o_mail_info text-muted">
                                <strong data-oe-model="res.partner" data-oe-id="" class="o_thread_author ">
                                  Updated By --> {0} 
                                </strong>
                                - <small style="color:#5ec269;font-size:12px;" >{1}</small>
                            </p>
                              <div class="o_thread_message_content">
                        <ul class="o_mail_thread_message_tracking">
                                                    <li>
                                                     {2} : {3} <span aria-label="Changed" class="fa fa-long-arrow-right" role="img" title="Changed"></span> {4}  </br>

                                                     </li></ul></div></div></div>""".format(data.mail_message_id.reply_to,
                                                                                            data.mail_message_id.create_date,
                                                                                            data.field_desc,
                                                                                            data.old_value_char,
                                                                                            data.new_value_char,
                                                                                            field_value))






            domain_2 = [
                ('res_id', '=', receipt_id.id),
                ('model', '=', 'ticl.receipt'),
                ('body', '=', ''),
                ('id', 'not in', [mail_message_create.id, mail_message_create.id + 1])]
            order_2="id desc"
            mail_message_create_check = self.mail_message(domain_2,order_2)

            receipt_log_id = self.env['ticl.receipt.log.summary'].search([('name', '=', self.origin)], limit=1)
            domain_3 = [('res_id', '=', receipt_log_id.id), ('model', '=', 'ticl.receipt.log.summary'),('body', '=', '')]

            ml_msg_smr = self.mail_message(domain_3,order_2)

            receipt_log_update_id = self.env['ticl.receipt.log.summary'].search([('name', '=', self.origin)])
            receipt_log_update_line_id = self.env['ticl.receipt.log.summary.line'].search(
                [('ticl_receipt_summary_id', '=', receipt_log_update_id.id),('serial_number', '=', self.serial_number)], limit=1)

            domain_4 = [('res_id', '=', receipt_log_update_line_id.id),('model', '=', 'ticl.receipt.log.summary.line'),('body', '=', '')]

            ml_msg_smr_ln = self.mail_message(domain_4,order_2)

            msgIds = ml_msg_smr_ln.ids + ml_msg_smr.ids + mail_message_create_check.ids

            self._cr.execute(""" SELECT array_agg(id) as ids from mail_tracking_value
                where mail_message_id in %s
                GROUP BY create_date,create_uid
                ORDER BY create_date desc
            """, (tuple(msgIds),))
            trackQryDatas = self._cr.dictfetchall()


            create_line_time_data_check = []

            for trackQryData in reversed(trackQryDatas):
                trackIds = trackQryData.get('ids')
                #tracks = self.env['mail.tracking.value'].browse(trackIds)
                tracks_1 = self.env['mail.tracking.value']
                tracks = tracks_1.browse(trackIds)

                trackMsg = """ 
                    <div class="o_thread_message  o_mail_not_discussion"  style="width: 50%;">
                        <div class="o_thread_message_core" >
                            <p class="o_mail_info text-muted">
                                <strong data-oe-model="res.partner" data-oe-id="" class="o_thread_author ">
                                  Updated By --> {0} 
                                </strong>
                                - <small style="color:#5ec269;font-size:12px;" >{1}</small>
                            </p> """.format(tracks[0].mail_message_id.reply_to,tracks[0].create_date)
                innMsg = ''
                dupliLst = []
                for track in tracks_1.search([('id','in',tracks.ids)],order="id asc"):
                    if track.field_desc not in ['Warehouse Location','Sending Location','Receiving Location']:
                        if track.field_desc not in dupliLst:
                            if track.field_type == 'datetime' and track.new_value_datetime:
                                x,y,z = track.field_desc,track.old_value_datetime if track.old_value_datetime else '',track.new_value_datetime
                            elif track.field_type == 'boolean' and track.new_value_integer:
                                x,y,z = track.field_desc,'','Done'
                            else:
                                if track.field_desc == 'Status' and not track.old_value_char:
                                    continue
                                x,y,z = track.field_desc,track.old_value_char if track.old_value_char else '',track.new_value_char
                            if str(x) != "BOL #":
                                innMsg += """<div class="o_thread_message_content">
                                                <ul class="o_mail_thread_message_tracking">
                                                    <li>
                                                        {0} : {1} <span aria-label="Changed" class="fa fa-long-arrow-right" role="img" title="Changed"></span> {2}  </br>
                
                                                    </li>
                                                </ul>
                                            </div>""".format(x,y,z)
                            dupliLst.append(track.field_desc)
                create_line_time_data_check.append(trackMsg + innMsg + '</div></div>')
            ################Shipment #################
            shipment_create_vals = []
            shipment_create_line_vals = []
            vals_shipment = ''
            # ticl_shipment_line_id = self.env['ticl.shipment.log.line'].search([('serial_number','=',self.serial_number)])
            ticl_shipment_line_id = self.env['ticl.shipment.log.line'].search([('serial_number','=',self.serial_number)], limit=1)
            if ticl_shipment_line_id.id != False:
                ticl_shipment_id	= self.env['ticl.shipment.log'].search([('id','=',ticl_shipment_line_id.ticl_ship_id.id)], limit=1)
                mail_message_log_update = self.env['mail.message'].search(
                    [('res_id', '=', ticl_shipment_id.id),
                     ('model', '=', 'ticl.shipment.log'),
                     ('body', '=', '')],
                    order="id asc")
                vals_shipment = """<div class="o_thread_message  o_mail_not_discussion"  >
                                                                    <div class="o_thread_message_core" >
                                                                    <p class="o_mail_info text-muted">
                                        <strong data-oe-model="res.partner" data-oe-id="" class="o_thread_author ">
                                          Created By --> {0} 
                                        </strong>
                                        - <small style="color:#5ec269;font-size:12px;" >{1}</small>
                                            </p>
                                                  <div class="o_thread_message_content">
                                                                    <ul class="o_mail_thread_message_tracking">
                                                """.format(mail_message_log_update[0].reply_to,mail_message_log_update[0].create_date)

                for ids in mail_message_log_update:
                    mail_log_line_tracking_create = self.env['mail.tracking.value'].search(
                        [('mail_message_id', '=', ids.id), ('old_value_char', '=', '')])
                    for data in mail_log_line_tracking_create:
                        print('\n\n\n\n RRRRRRRRRRRRRR',data.field_desc,data.new_value_char , data.new_value_datetime)
                        if data.field_desc == "Pickup Date Date":
                            data.new_value_char = data.new_value_datetime
                        shipment_create_vals.append("""
                            <li>
                             {0} : {1}   </br>
                             </li>""".format(
                            data.field_desc,
                            data.new_value_char
                        ))
                mail_message_log_line_update = self.env['mail.message'].search(
                    [('res_id', '=', ticl_shipment_line_id.id),
                     ('model', '=', 'ticl.shipment.log.line'),
                     ('body', '=', '')],
                    order="id asc")
                for ids in mail_message_log_line_update:
                    mail_log_line_tracking_create = self.env['mail.tracking.value'].search(
                        [('mail_message_id', '=', ids.id), ('old_value_char', '=', '')])
                    for data in mail_log_line_tracking_create:
                        shipment_create_line_vals.append("""
                            <li>
                             {0} : {1}   </br>
                             </li>""".format(
                            data.field_desc,
                            data.new_value_char
                        ))
                vals_shipment = vals_shipment + "".join(shipment_create_vals) + "".join(shipment_create_line_vals) + """</ul></div>"""

            #############
            shipment_update_vals = []
            ticl_shipment_line_id = self.env['ticl.shipment.log.line'].search(
                [('serial_number', '=', self.serial_number)], limit=1)
            if ticl_shipment_line_id.id != False:
                ticl_shipment_id = self.env['ticl.shipment.log'].search(
                    [('id', '=', ticl_shipment_line_id.ticl_ship_id.id)])
                mail_message_log_update = self.env['mail.message'].search(
                    [('res_id', '=', ticl_shipment_id.id),
                     ('model', '=', 'ticl.shipment.log'),
                     ('body', '=', '')],
                    order="id asc")
                for ids in mail_message_log_update:
                    mail_log_line_tracking_create = self.env['mail.tracking.value'].search(
                        [('mail_message_id', '=', ids.id), ('old_value_char', '!=', '')])
                    for data in mail_log_line_tracking_create:
                        if data.field_desc == "Pickup Date Date":
                            data.old_value_char = data.old_value_datetime
                            data.new_value_char = data.new_value_datetime
                        shipment_update_vals.append(""" 
                                <div class="o_thread_message  o_mail_not_discussion" >
                                <div class="o_thread_message_core" >
                                                            <p class="o_mail_info text-muted">
                                        <strong data-oe-model="res.partner" data-oe-id="" class="o_thread_author ">
                                          Updated By --> {0} 
                                        </strong>
                                        - <small style="color:#5ec269;font-size:12px;" >{1}</small>
                                    </p>
                                      <div class="o_thread_message_content">
                                <ul class="o_mail_thread_message_tracking">
                                                            <li>
                                                             {2} : {3} <span aria-label="Changed" class="fa fa-long-arrow-right" role="img" title="Changed"></span> {4}  </br>
            
                                                             </li></ul></div></div></div>""".format(
                            ids.reply_to,
                            ids.create_date,
                            data.field_desc,
                            data.old_value_char,
                            data.new_value_char
                        ))

            shipment_update = []
            ticl_shipment_line_id = self.env['ticl.shipment.log.line'].search(
                [('serial_number', '=', self.serial_number)], limit=1)
            if ticl_shipment_line_id.id != False:
                ticl_shipment_id = self.env['ticl.shipment.log'].search(
                    [('id', '=', ticl_shipment_line_id.ticl_ship_id.id)])
                mail_message_log_update = self.env['mail.message'].search(
                    [('res_id', '=', ticl_shipment_line_id.id),
                     ('model', '=', 'ticl.shipment.log.line'),
                     ('body', '=', '')],
                    order="id asc")
                for ids in mail_message_log_update:
                    mail_log_line_tracking_create = self.env['mail.tracking.value'].search(
                        [('mail_message_id', '=', ids.id), ('old_value_char', '!=', '')])
                    for data in mail_log_line_tracking_create:
                        shipment_update.append(""" 
                                    <div class="o_thread_message  o_mail_not_discussion" >
                                    <div class="o_thread_message_core" >
                                                                <p class="o_mail_info text-muted">
                                            <strong data-oe-model="res.partner" data-oe-id="" class="o_thread_author ">
                                              Updated By --> {0} 
                                            </strong>
                                            - <small style="color:#5ec269;font-size:12px;" >{1}</small>
                                        </p>
                                          <div class="o_thread_message_content">
                                    <ul class="o_mail_thread_message_tracking">
                                                                <li>
                                                                 {2} : {3} <span aria-label="Changed" class="fa fa-long-arrow-right" role="img" title="Changed"></span> {4}  </br>

                                                                 </li></ul></div></div></div>""".format(
                            ids.reply_to,
                            ids.create_date,
                            data.field_desc,
                            data.old_value_char,
                            data.new_value_char
                        ))

            create_log_update_data_check , create_log_line_update_data_check = [] , []
            create_raw_html = self.get_raw_html(
                user_date,
                create_time_data,
                create_line_time_data,
                create_log_update_data_check,
                create_log_line_update_data_check,
                vals,
                create_line_time_data_check,
                vals_shipment,
                shipment_update_vals,
                shipment_update
                )


            context['message'] = create_raw_html
            return {
                'name': 'Serial Number History ({0})'.format(self.serial_number),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'serial.number.history',
                'view': [('view', 'form')],
                'target': 'new',
                'context': context,
            }
