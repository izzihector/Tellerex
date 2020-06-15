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
import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC
import calendar

class StockQuant(models.Model):
	_inherit='stock.quant'
	
	#override
	# @api.model
	def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
		self = self.sudo()
		rounding = product_id.uom_id.rounding
		quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
		reserved_quants = []
		if self._context.get('order_type', False):
			if self._context.get('order_type') == 'sale':
				moves = self.env['stock.move'].sudo().search([('status','=','inventory'),('product_id','=',product_id.id)])
				serial_number = moves.mapped('serial_number')
				condition_id = self.env['ticl.condition'].sudo().search([('name','=','To Recommend')]).id
				lots = self.env['stock.production.lot'].sudo().search([
					('condition_id','=',condition_id),
					('product_id','=',product_id.id),
					('name','in',serial_number)
					])
				quants = moves = self.env['stock.quant'].sudo().search([
				    ('id','in',quants.ids),
				    ('lot_id','in',lots.ids)])
				
		if float_compare(quantity, 0, precision_rounding=rounding) > 0:
			# if we want to reserve
			available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
			if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
				raise UserError(_('It is not possible to reserve more products of %s than you have in stock.') % product_id.display_name)
		elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
			# if we want to unreserve
			available_quantity = sum(quants.mapped('reserved_quantity'))
			if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
				raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.') % product_id.display_name)
		else:
			return reserved_quants

		for quant in quants:
			if float_compare(quantity, 0, precision_rounding=rounding) > 0:
				max_quantity_on_quant = quant.quantity - quant.reserved_quantity
				if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
					continue
				max_quantity_on_quant = min(max_quantity_on_quant, quantity)
				quant.reserved_quantity += max_quantity_on_quant
				reserved_quants.append((quant, max_quantity_on_quant))
				quantity -= max_quantity_on_quant
				available_quantity -= max_quantity_on_quant
			else:
				max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
				quant.reserved_quantity -= max_quantity_on_quant
				reserved_quants.append((quant, -max_quantity_on_quant))
				quantity += max_quantity_on_quant
				available_quantity += max_quantity_on_quant

			if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
				break
		return reserved_quants
	



class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.model
	def create(self, vals_list):
		if 'order_line' in vals_list.keys():
			for i in range(0, len(vals_list['order_line'])):
				vals_list['order_line'][i][2]['disassembly_unit'] = vals_list['sale_unit']
				# vals['order_line'][i][2]['unit_type'] = vals['unit_type']
		return super(SaleOrder, self).create(vals_list)

	#@api.model
	def write(self, vals_list):
		if 'order_line' in vals_list.keys():
			for i in range(len(self.order_line), len(vals['order_line'])):
				if vals_list['order_line'][i][2] != False:
					vals_list['order_line'][i][2]['disassembly_unit'] = self.sale_unit
					# vals['order_line'][i][2]['unit_type'] = self.unit_type
		if 'check_number' in vals_list.keys():
			if self.po_ids:
				po_id = self.env['purchase.order'].search([('name','=',self.po_ids.name)])
				po_id.write({'check_number':vals_list['check_number']})
		return super(SaleOrder, self).write(vals_list)

	@api.onchange('sale_unit','unit_type','sale_type')
	def on_change_sale_unit(self):
		if self.sale_type == 're-marketing':
			self.unit_type = False
			self.sale_unit = 'no'
		if self.sale_type == 'refurb':
			self.sale_unit = 'no'
			if self.unit_type == False:
				self.unit_type = 'fully_functional'
		if self.sale_type == 'disassembly_unit':
			self.unit_type = False
			self.sale_unit = 'yes'
		self.order_line = self.env['sale.order.line']

	# @api.model
	def get_comission_product(self, order_date):
		contract = self.env['ticl.sale.contract'].search([('active','=',True)])
		for comission in contract.contract_line:
			if comission.start_date <= order_date <= comission.end_date:
				tel_charge = comission.commission
				banks_charge = 1 - comission.commission
				for line in  self.order_line:
					if line.disassembly_unit == 'no' and line.unit_type == False:
						line.tellerex_charges = (line.product_uom_qty) * (line.price_unit * tel_charge)	
						line.bank_chanrges = (line.product_uom_qty) * (line.price_unit * banks_charge)
					elif line.disassembly_unit == 'yes' and line.unit_type == False:
						line.tellerex_charges = ''
						line.bank_chanrges = 250 * line.product_uom_qty
						line.price_unit = 250 
						line.purchase_price = 0.00
				break
			else:
				for line in  self.order_line:
					if line.disassembly_unit == 'yes' and line.unit_type == False:
						line.tellerex_charges = ''
						line.bank_chanrges = 250 * line.product_uom_qty
						line.price_unit = 250 
						line.purchase_price = 0.00
	# @api.model
	def create_purchase_order(self):
		vendorName = self.warehouse_id.name
		vender = self.env['res.partner'].search([('name','=','JP Morgan Chase Bank')])
		product_id = self.env['product.product'].search([('name','=','Tellerex RM Services')])
		condition_env = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
		picking_id = self.env['stock.picking'].search([('origin','=',self.name),('state','=','done')])
		move_id = self.env['stock.move'].search([('picking_id', '=', picking_id.id)])
		data = ""
		for ids in move_id:
			move_line_id = self.env['stock.move.line'].search([('move_id','=',ids.id)])
			for ids in move_line_id:
				if ids.lot_id.name != False:
					name = ids.lot_id.name
				if ids.lot_id.name == False:
					name = ''
				data = data + str(ids.product_id.name) + '  ➜  ' + str(name) + '\n'
		po = self.env['purchase.order'].create({'partner_id':vender.id,'partner_ref':self.name,'notes': data})
		
		sum_amount = []
		quantity = []
		for line in self.order_line:
			sum_amount.append(line.bank_chanrges)
			quantity.append(line.product_uom_qty)
		for line in  self.order_line:
			print("==pooooooooooooooooooooooooooo====",condition_env.id)
			po_line = self.env['purchase.order.line'].create({
				'type_id': line.tel_type.id, 
				'product_qty': 1,
				'product_id': product_id.id,
				'name': product_id.name,
				'price_unit': sum(sum_amount),
				'order_id':po.id,
				'date_planned': self.date_order,
				'product_uom':line.product_uom.id,
				'condition_id': condition_env.id,
				'tab_hide' : True,

			})
			
			po_line.price_subtotal = sum(sum_amount)
			po_line.price_total = sum(sum_amount)
			break;
		self.write({'po_ids': po.id,'chase_inv_status':'not_paid'})
		return po

	#Override Action Function from Inventory
	#@api.model
	def action_confirm(self):
		sup = super(SaleOrder,self.with_context(order_type='sale'))
		print("====sup==",sup)
		res = sup.action_confirm()
		moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
		#Contract comission calculation
		self.get_comission_product(self.date_order)
		for pick in self.picking_ids:
			pick.write({'user_id':self.user_id.id})		
		#Move record from sale order line to picking from line
# 		user_mvs = []
		for line in  self.order_line:
			move = self.env['stock.move'].search([
				('id','in',moves.ids),
				('product_id','=',line.product_id.id)
			])
			move.write({
				'condition_id':line.condition_id.id,
				'categ_id': line.tel_type.id,
				'manufacturer_id':line.product_id.manufacturer_id.id,
				#'status':'inventory',
				})
		return res

	sale_unit = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Disassembly Unit', default='no')
	is_service = fields.Boolean(string='Is Service',default= True)
	additional_note = fields.Char(string='Additional Note')
	validity_date = fields.Datetime(string="Validity", default=datetime.datetime.today())
	po_count = fields.Integer(string='Purchase Order Count', readonly=True,copy=False)
	po_ids = fields.Many2one("purchase.order", string='Purchase Order', readonly=True,
								   copy=False)
	check_number = fields.Char("Check Number",copy=False)
	chase_inv_status = fields.Selection([('fully_paid','Fully Paid'),('not_paid','Not Paid')],"Chase Invoice Status",copy=False)
	sale_type = fields.Selection([('re-marketing','Re-Marketing'),('refurb','Refurb'),('disassembly_unit','Disassembly Unit')],string="Sale Type",copy=False)
	unit_type = fields.Selection([('fully_functional','Fully Functional'),('cash_dispenser','Cash Dispenser')],string="Unit Type",copy=False)

	#@api.model
	def action_view_purchase(self):
		action = self.env.ref('purchase.purchase_rfq').read()[0]
		action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
		action['res_id'] = self.po_ids.id
		return action
	



class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'


	# @api.onchange('condition_id')
	# def onchange_product_type(self):
	# 	for line in self:
	# 		if line.condition_id.name == 'To Recommend':
	# 			self.to_recommend = '250'

	def _default_to_recommend(self):
		return self.env['ticl.condition'].search([('name', '=', 'To Recommend')], limit=1).id

	@api.onchange('disassembly_unit','unit_type','chase_contract_date','price_unit','product_uom_qty','purchase_price')
	def onchange_disassembly_unit(self):
		for line in self:		
			if line.unit_type == "fully_functional":
				line.price_unit =2500
				line.tellerex_charges = ''
				line.bank_chanrges = 2500
				line.purchase_price = 0.00
			elif line.unit_type == "cash_dispenser":
				line.price_unit =1250
				line.tellerex_charges = ''
				line.bank_chanrges = 1250
				line.purchase_price = 0.00
			if line.disassembly_unit == 'no' and line.unit_type == False:
				#line.price_unit = line.product_id.lst_price
				if line.chase_contract_date:
					#line.price_unit = line.product_id.lst_price
					d = datetime.datetime.now()
					contract_date = fields.Datetime.from_string(line.chase_contract_date)
					for attr in [ 'year']:
						now_year = getattr(d, attr)
						contract_date = getattr(contract_date, attr)
						diff_year = now_year - contract_date
						if diff_year == 0:
							tel_charge = (line.price_unit*20)/100
							line.tellerex_charges = (line.product_uom_qty)*tel_charge		
							banks_charge = (line.price_unit*80)/100
							line.bank_chanrges = (line.product_uom_qty)*banks_charge

						elif diff_year == 1:
							tel_charge = (line.price_unit*25)/100
							line.tellerex_charges = (line.product_uom_qty)*tel_charge
							banks_charge = (line.price_unit*75)/100
							line.bank_chanrges = (line.product_uom_qty)*banks_charge

						elif diff_year == 2:
							tel_charge = (line.price_unit*30)/100
							line.tellerex_charges = (line.product_uom_qty)*tel_charge
							banks_charge = (line.price_unit*70)/100
							line.bank_chanrges = (line.product_uom_qty)*banks_charge
						else:
							raise Warning(_('Please check More than 3years, required for Disassembly Unit!'))
				else:
					line.tellerex_charges = ''
					line.bank_chanrges = ''
							
			elif line.disassembly_unit == 'yes' and line.unit_type == False:
				line.tellerex_charges = ''
				line.bank_chanrges = 250 * line.product_uom_qty
				line.price_unit = 250
				line.purchase_price = 0.00

			else:
				return False


		    	

	@api.model
	def _compute_amount(self):
		res = super(SaleOrderLine, self)._compute_amount()
		for line in self:
			if line.disassembly_unit == 'yes':
				price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
				taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
				line.update({
					'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
					'price_total': taxes['total_included'],
					'price_subtotal': taxes['total_excluded'],
					})


		#return res

	#Prepare Invoice from sale Order
	#@api.model
	def _prepare_invoice_line(self):
		res = super(SaleOrderLine, self)._prepare_invoice_line()
		res.update({'tel_type': self.tel_type.id,'chase_contract_date': self.chase_contract_date,'disassembly_unit': self.disassembly_unit\
			,'tellerex_charges': self.tellerex_charges,'bank_chanrges': self.bank_chanrges,'price_unit': self.price_unit})
		return res

	#Onchange Domain Function
	@api.onchange( 'product_id', 'tel_type','manufacturer_id')
	def onchange_product_type(self):
		return {'domain':{'product_id':[('categ_id','=',self.tel_type.id),('manufacturer_id','=',self.manufacturer_id.id)]}}



	#Product Onchange Method
	#@api.model
	@api.onchange('product_id','product_uom_qty')
	def product_id_change(self):
		res = super(SaleOrderLine, self).product_id_change()
		for line in self:
			if line.unit_type == "fully_functional":
				line.price_unit =2500
			elif line.unit_type == "cash_dispenser":
				line.price_unit =1250
			if line.disassembly_unit == "yes" and line.unit_type == False:
				line.price_unit =250
			if not self.product_id or not self.product_uom_qty or not self.product_uom:
				return {}
			else:
				condition_id = self.env['ticl.condition'].search([('name','=','To Recommend')]).id
				print("==condition_id===",condition_id)
				move = self.env['stock.move.line'].search([('product_id','=',line.product_id.id),('status','=','inventory'),
															 ('warehouse_id','=',line.order_id.warehouse_id.id),('condition_id','=',condition_id),('order_from_receipt','=',True)])

				print("==move_id===",move)
				total_prod = len(move)
				print("==total_prod===",total_prod)
				if int(total_prod) < int(line.product_uom_qty):
					raise UserError(_("Not enough inventory!"))
					# line.product_uom_qty = 0.00
					# raise UserError(_("Not enough inventory!"))

	@api.model
	def _product_filter(self):
		domain = [('sale_ok', '=', True)]
		condition_id = self.env['ticl.condition'].search([('name','=','To Recommend')]).id
		moves = self.env['stock.move'].search([('condition_id','=',condition_id),('status','=','inventory')])
		domain += [('id','in',moves.mapped('product_id').ids)]
		return domain

	product_id = fields.Many2one('product.product', string='Product', domain=_product_filter, change_default=True, ondelete='restrict')
	condition_id = fields.Many2one('ticl.condition', string="Condition",default=_default_to_recommend)
	to_recommend = fields.Char(string='To Recommend Charges')
	tellerex_charges = fields.Float(string='Tellerex Charges')
	bank_chanrges = fields.Float(string='Chase Charges', default=0.00)
	chase_contract_date = fields.Datetime(string='Contract Date')
	ticl_contract_id = fields.Many2one('ticl.sale.contract', string="Contract")
	charge_year_count = fields.Char(string="Calculate Contract Year")
	reassemble_unit = fields.Selection([('yes', 'Yes'), ('no', 'No')],string='Disassembly Unit')
	disassembly_unit = fields.Selection([('yes', 'Yes'), ('no', 'No')],string='Disassembly Unit')
	unit_type = fields.Selection([('fully_functional','Fully Functional'),('cash_dispenser','Cash Dispenser')],string="Unit Type")
	tel_type = fields.Many2one('product.category', string="Type",track_visibility='onchange')
	manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer",track_visibility='onchange')



# class SaleAdvancePaymentInv(models.TransientModel):
#     _inherit = "sale.advance.payment.inv"
#     _description = "Sales Advance Payment Invoice"




class StockProductionLot(models.Model):
	_inherit = 'stock.production.lot'
	_sql_constraints = [('name_ref_uniq', 'check(1=1)', 'No error'), ]
	
	condition_id = fields.Many2one('ticl.condition', string="Condition")
	receiving_location_id = fields.Many2one('stock.location', string='Destination Location')
	is_scraped = fields.Boolean(default=False)
	stock_move_id = fields.Many2one('stock.move', string='Stock Move ID')
	
	
	#@api.model_create_multi
	def create(self, vals_list):
		if vals_list.get('name', False):
			move = self.env['stock.move.line'].search([('serial_number','=',vals_list.get('name'))], order='id desc', limit=1)
			vals_list.update({'condition_id':move.condition_id.id,'receiving_location_id':move.ticl_warehouse_id.id})
		return super(StockProductionLot, self).create(vals_list)


class Picking(models.Model):
	_inherit = "stock.picking"

	#@api.model
	def button_validate(self):
		if 'active_model' in self._context.keys():
			if self._context['active_model'] == 'sale.order':
				move_id = self.env['stock.move.line'].search([('picking_id', '=', self.id)])	
				for ids in move_id:
					for x in ids:	      
						if not x.lot_id:
							stock_id = 0
							condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
							for i in range(int(x.product_uom_qty)):
								stock_move_id = self.env['stock.move.line'].search([('id', '!=', stock_id), ('product_id', '=', x.move_id.product_id.id), ('condition_id', '=', condition_id.id), ('status', '=', 'inventory')], limit=1)
								if stock_move_id.id != False:
									stock_id = stock_move_id.id
									move = self.env['stock.move.line'].search([('id', '=', stock_move_id.id)])
									move.write({'status':'sold', 'sale_stock_move_id':x.picking_id.origin})
									self.env['ticl.receipt.log.summary.line'].search(
									    [('tel_unique_no', '=', move.tel_unique_no)]).write(
									    {'check_sale': True})
								if stock_move_id.id == False:
									raise UserError('{0} — Item(s) are not available in Inventory !'.format(x.move_id.product_id.name))
						if x.lot_id:
							stock_move_id = self.env['stock.move.line'].search([('serial_number', '=', x.lot_id.name)], limit=1)
							if stock_move_id.condition_id.name == 'To Recommend':
								stock_move_id.write({'status':'sold', 'sale_stock_move_id':x.picking_id.origin})
								self.env['ticl.receipt.log.summary.line'].search(
								    [('tel_unique_no', '=', stock_move_id.tel_unique_no)]).write(
								    {'check_sale': True})
		res = super(Picking, self).button_validate()
		return res


class StockMoveSale(models.Model):
    _inherit="stock.move"

    sale_stock_move_id = fields.Char('Sale ID')
    sale_old_id = fields.Char('Sale Old ID')
    sale_import_data = fields.Boolean("Imported Data")
    sale_type = fields.Char('Sale Type')
    sale_date = fields.Char('Sold Date')
    sale_date_pick = fields.Date('Sold Date')
    sale_gross = fields.Char('Sale Gross')
    sale_net = fields.Char('Sale Net')
    sale_commission = fields.Char('Sale Commission')
    sale_check_number = fields.Char('Sale Check Number')

    # @api.one
    # def _get_sale_data(self):
    #     if self.sale_stock_move_id != False:
    #         picking_id = self.env['stock.picking'].search([('origin', '=', self.sale_stock_move_id)], limit=1)
    #         so_id = self.env['sale.order'].search([('name', '=', self.sale_stock_move_id)])
    #         so_line_ids = self.env['sale.order.line'].search(
    #             [('order_id', '=', so_id.id), ('product_id', '=', self.product_id.id)], limit=1)
    #         if so_line_ids.product_uom_qty > 1:
    #             price_subtotal = round(so_line_ids.price_subtotal / so_line_ids.product_uom_qty, 2)
    #             bank_chanrges = round(so_line_ids.bank_chanrges / so_line_ids.product_uom_qty, 2)
    #             tellerex_charges = round(so_line_ids.tellerex_charges / so_line_ids.product_uom_qty, 2)
    #         elif so_line_ids.product_uom_qty <= 1:
    #             price_subtotal = so_line_ids.price_subtotal
    #             bank_chanrges = so_line_ids.bank_chanrges
    #             tellerex_charges = so_line_ids.tellerex_charges
    #         if so_line_ids.disassembly_unit == 'yes':
    #             sale_type = 'Parts Unit'
    #         if so_line_ids.disassembly_unit == 'no':
    #             sale_type =  'External Sale'
    #         self.sale_type = sale_type
    #         self.sale_date = picking_id.create_date
    #         self.sale_check_number = so_id.check_number
    #         self.sale_gross = price_subtotal
    #         self.sale_net = bank_chanrges
    #         self.sale_commission = tellerex_charges



 #    #update Sale Check Box in Receipt
	# def update_check_sale(self):
	# 	move_id = self.env['stock.move'].search([('picking_id', '=', self.id)])
	# 	for x in move_id.move_line_ids:
	# 		move_line_id = self.env['stock.move.line'].search([('move_id', '=', x.id)])
	# 		stock_move_id = self.env['stock.move'].search([('serial_number', '=', x.lot_id.name)])
	# 		for i in stock_move_id:
	# 			if i.condition_id.name == 'To Recommend':
	# 				self.env['ticl.receipt.log.summary.line'].search(
	# 					[('tel_unique_no', '=', i.tel_unique_no)]).write(
	# 					{'check_sale': True})
