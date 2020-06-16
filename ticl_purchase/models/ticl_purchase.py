from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from werkzeug.urls import url_encode


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	
		
	receiving_status = fields.Selection([
		('draft', 'Nothing to Receive'),
		('receiving', 'Waiting Receive'),
		('done', 'Received'),
		], string='Delivery Status', store=True, readonly=True, copy=False, default='draft')
	is_service = fields.Boolean(string='Is Service')
	sales_num = fields.Char(string='Sales Order Number' )
	check_number = fields.Char("Check Number", copy=False)
	invoice_status = fields.Selection([   ('no', 'Nothing to Bill'),
										  ('to invoice', 'Waiting Bills'),
										  ('invoiced', 'Bill to be Paid'),
										  ('paid', 'Bill Completed'),
							], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

	

	#Write Method
	#@api.multi
	def write(self, values):
		if 'check_number' in values.keys():
			if self.partner_ref:
				so_id = self.env['sale.order'].search([('name','=',self.partner_ref)])
				so_id.write({'check_number':values['check_number']})
		return super(PurchaseOrder, self).write(values)

	# #@api.multi
	# def action_view_invoice(self):
	# 	'''
 #        This function returns an action that display existing vendor bills of given purchase order ids.
 #        When only one found, show the vendor bill immediately.
 #        '''
	# 	action = self.env.ref('account.action_vendor_bill_template')
	# 	result = action.read()[0]
	# 	create_bill = self.env.context.get('create_bill', False)
	# 	# override the context to get rid of the default filtering
	# 	result['context'] = {
	# 		'type': 'in_invoice',
	# 		'default_purchase_id': self.id,
	# 		'default_currency_id': self.currency_id.id,
	# 		'default_company_id': self.company_id.id,
	# 		'company_id': self.company_id.id
	# 	}
	# 	# choose the view_mode accordingly
	# 	if len(self.invoice_ids) > 1 and not create_bill:
	# 		result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
	# 	else:
	# 		res = self.env.ref('account.invoice_supplier_form', False)
	# 		result['views'] = [(res and res.id or False, 'form')]
	# 		# Do not set an invoice_id if we want to create a new bill.
	# 		if not create_bill:
	# 			result['res_id'] = self.invoice_ids.id or False
	# 	result['context']['default_origin'] = self.name
	# 	result['context']['default_reference'] = self.partner_ref
	# 	result['context']['default_comment'] = self.notes
	# 	self.invoice_status = 'invoiced'
	# 	return result

	#Stock picking and move create
	#@api.multi
	# def button_confirm(self):
	# 	res = super(PurchaseOrder, self).button_confirm()
	# 	moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
		
	# 	for line in  self.order_line:
	# 		move = self.env['stock.move'].search([
	# 			('id','in',moves.ids),
	# 			('product_id','=',line.product_id.id)
	# 		])
	# 		move.write({
	# 			'condition_id':line.condition_id.id,
	# 			'categ_id': line.type_id.id,
	# 			'manufacturer_id':line.product_id.manufacturer_id.id,
	# 			'status':'inventory',
	# 			'order_from_receipt':False})
	# 		moveLine = self.env['stock.move.line'].search([('move_id','in',move.ids)])
	# 		for moveLinemove in moveLine:
	# 			if moveLinemove: moveLinemove.condition_id = line.condition_id.id
	# 		self.invoice_status = 'to invoice'
	# 	return res			
	
	# @api.multi
	# def button_confirm(self):
	# 	res = super(PurchaseOrder, self).button_confirm()
	# 	self.receiving_status = 'receiving'
	# 	moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
		
	# 	for line in  self.order_line:
	# 		move = self.env['stock.move'].search([
	# 			('id','in',moves.ids),
	# 			('product_id','=',line.product_id.id)
	# 		])
	# 		move.write({
	# 			'condition_id':line.condition_id.id,
	# 			'categ_id': line.type_id.id,
	# 			'manufacturer_id':line.product_id.manufacturer_id.id,
	# 			'status':'inventory',
	# 			})
	# 	return res
	

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	# Filter Product Basis of Product TYpe	
	@api.onchange('type_id')
	def onchange_product_type(self):
		res = {}
		if self.type_id.name == 'ATM':
			res['domain']={'product_id':[('categ_id', '=', self.type_id.id),('purchase_ok', '=', True)]}
		elif self.type_id.name == 'Accessory':
			res['domain']={'product_id':[('categ_id', '=', self.type_id.id),('purchase_ok', '=', True)]}
		elif self.type_id.name == 'Signage':
			res['domain']={'product_id':[('categ_id', '=', self.type_id.id),('purchase_ok', '=', True)]}	
		elif self.type_id.name == 'Lockbox':
			res['domain']={'product_id':[('categ_id', '=', self.type_id.id),('purchase_ok', '=', True)]}
		else:
			res['domain']={'product_id':[('categ_id', '=', self.type_id.id),('purchase_ok', '=', True)]}          
		return res


	type_id = fields.Many2one('product.category', string="Type")
	serial_number = fields.Char(string='Serial #')
	condition_id = fields.Many2one('ticl.condition', string="Condition")
	tab_hide = fields.Boolean(string='Hide Tab',default=False)



class Picking(models.Model):
	_inherit = "stock.picking"

	condition_id = fields.Many2one('ticl.condition', string="Condition")

	#@api.multi
	def button_validate(self):
	    res = super(Picking, self).button_validate()
	    # sale_id = self.env['sale.order'].search([('name','=',self.origin)])
	    # if sale_id:
	    # 	sale_id.receiving_status = 'done'
	    # 	for line in  self.move_ids_without_package:
	    # 		move_line_id = self.env['stock.move.line'].search([('move_id', '=', line.id)])
	    # 		for lines in move_line_id:
	    # 			self.env['stock.move'].search([('serial_number', '=', lines.lot_id.name),('status','=','inventory')]).write({
	    # 				 'status': 'sold'})
	    # moves = self.env['purchase.order'].search([('name','=',self.origin)])
	    # if moves:
	    #     moves.receiving_status = 'done'
	    #     for line in  self.move_ids_without_package:
	    #         line.write({
	    #         'order_from_receipt':True})
	    return res


class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	#onchange for serail Number
	@api.onchange('location_dest_id')
	def onchange_filter(self):
		lots = []
		warehouse = self.env['stock.location'].search([('name', '=', self.move_id.picking_id.picking_type_id.warehouse_id.name)])
		move_id = self.env['stock.move'].search([('product_id','=',self.move_id.product_id.id),('status','=','inventory'),
												 ('location_dest_id','=',warehouse.id)])
		for ids in move_id:
			lot_ids =  self.env['stock.production.lot'].search([('name','=',ids.serial_number)])
			for ids in lot_ids:
				lots.append(ids.id)
		return {'domain': {'lot_id': [('id', 'in',lots)]}}

	condition_id = fields.Many2one('ticl.condition', string="Condition")
	manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")

	#@api.multi
	@api.onchange('lot_name')
	def on_change_lot_name(self):
		product = self.product_id
		if self.lot_name and product.manufacturer_id.name:
			if len(self.lot_name) != 8 and product.manufacturer_id.name == "NCR":
				self.serial_number = ''
				raise UserError(
					_("Serial number should be 8 Digit for NCR ATM's product %s.") % product.display_name)

			if len(self.lot_name) != 10 and product.manufacturer_id.name in ["Nautilus Hyosung",
																			 "Wincor"]:
				self.lot_name = ''
				raise UserError(
					_("Serial number should be 10 Digit for " + product.manufacturer_id.name + " ATM's !"))

			if len(self.lot_name) != 12 and product.manufacturer_id.name == "Diebold":
				self.lot_name = ''
				raise UserError(
					_("Serial number should be 12 Digit for Diebold ATM's product %s.") % product.display_name)

		if not self.lot_name and not self.lot_id and self.product_id.tracking not in ('serial','lot'):
			raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

class account_invoice_supplier(models.Model):
	_inherit = 'account.move.line'

	condition_id = fields.Many2one('ticl.condition', string="Condition")




class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_invoice_register_payment(self):
		res = super(AccountMove, self).action_invoice_register_payment()
		if self.type == 'out_invoice':
			if 'SO' == self.communication[:2]:
				inv_id = self.env['account.move'].search([('reference', '=', self.communication)],limit=1)
				origin = inv_id.origin
				if 'PO' == origin[:2]:
					self.env['purchase.order'].search([('name', '=', inv_id.origin)]).write({'invoice_status': 'paid'})
			else:
				inv_id = self.env['account.move'].search([('number','=',self.communication)],limit=1)
				origin = inv_id.origin
				if 'PO' == origin[:2]:
					self.env['purchase.order'].search([('name','=',inv_id.origin)]).write({'invoice_status':'paid'})
		sale_ref = self.env['sale.order'].search([('name','=', self.ref)])
		if sale_ref:
			print("=====action_invoice_register_payment11111111=")
			sale_ref.write({'chase_inv_status': 'fully_paid'})

		return res


# class AccountPayment(models.Model):
# 	_inherit = 'account.payment'

# 	def action_validate_invoice_payment(self):
# 		res = super(AccountPayment, self).action_validate_invoice_payment()
# 		self.mapped('payment_transaction_id').filtered(
# 			lambda x: x.state == 'done' and not x.is_processed)._post_process_after_done()
# 		if self.payment_type == 'outbound':
# 			if 'SO' == self.communication[:2]:
# 				inv_id = self.env['account.move'].search([('reference', '=', self.communication)],limit=1)
# 				origin = inv_id.origin
# 				if 'PO' == origin[:2]:
# 					self.env['purchase.order'].search([('name', '=', inv_id.origin)]).write({'invoice_status': 'paid'})
# 			else:
# 				inv_id = self.env['account.move'].search([('number','=',self.communication)],limit=1)
# 				origin = inv_id.origin
# 				if 'PO' == origin[:2]:
# 					self.env['purchase.order'].search([('name','=',inv_id.origin)]).write({'invoice_status':'paid'})
# 		return res
