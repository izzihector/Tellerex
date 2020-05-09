# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Picking(models.Model):
	_inherit = "stock.picking"

	condition_id = fields.Many2one('ticl.condition', string="Condition")
	states = fields.Selection([('draft', 'Inventory'),('shipped', 'Shipped'),('recycled', 'Recycled'),
		('cancel', 'Cancelled')], string='States')
	receive_date = fields.Datetime(string="Receive Date")
	recycled_date = fields.Datetime(string="Recycled Date")
	part_name = fields.Char(string="Version Number")
	serial_number = fields.Char(string = "Serial Number")
	count_number = fields.Char(string = "Count")
	fund_doc_type = fields.Char(string = "Funding Doc Type")
	fund_doc_number = fields.Char(string = "Funding Doc Number")
	ticl_project_id = fields.Char(string = "Project Id")
	manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
	oem_pn = fields.Char(string = "OEM PN")
	product_function = fields.Char(string = "Function")
	product_lenght = fields.Float(string = "Lenght")
	product_width = fields.Float(string = "Width")
	product_height = fields.Float(string = "Height")
	weight = fields.Float(string = "Weight")
	product_squre_feet = fields.Float(string = "Square Feet")
	categ_id = fields.Many2one('product.category', string="Type")
	user_id = fields.Many2one('res.users', string='Responsible Persons', default=lambda self: self.env.user)

	# def confirm_shipped(self):
	# 	self.states = 'shipped'

	# @api.multi
	# def button_validate(self):
	# 	for line in self.move_line_ids:
	# 		product = line.product_id
	# 		if line.lot_name and product.manufacturer_id.name:
	# 			if len(line.lot_name) != 8 and product.manufacturer_id.name == "NCR":
	# 				line.serial_number = ''
	# 				raise UserError(
	# 					_("Serial number should be 8 Digit for NCR ATM's product %s.") % product.display_name)

	# 			if len(line.lot_name) != 10 and product.manufacturer_id.name in ["Nautilus Hyosung",
	# 																			 "Wincor"]:
	# 				line.lot_name = ''
	# 				raise UserError(
	# 					_("Serial number should be 10 Digit for " + product.manufacturer_id.name + " ATM's !"))

	# 			if len(line.lot_name) != 12 and product.manufacturer_id.name == "Diebold":
	# 				line.lot_name = ''
	# 				raise UserError(
	# 					_("Serial number should be 12 Digit for Diebold ATM's product %s.") % product.display_name)

	# 		if not line.lot_name and not line.lot_id:
	# 			raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)
	# 	super(Picking, self).button_validate()



class StockMove(models.Model):
	_inherit = 'stock.move'


	condition_id = fields.Many2one('ticl.condition', string="Condition")
	states = fields.Selection([('draft', 'Inventory'),('shipped', 'Shipped'),('recycled', 'Recycled'),
		('cancel', 'Cancelled')], string='States')
	receive_date = fields.Datetime(string="Receive Date")
	recycled_date = fields.Datetime(string="Recycled Date")
	part_name = fields.Char(string="Version Number")
	serial_number = fields.Char(string = "Serial Number")
	count_number = fields.Char(string = "Count")
	fund_doc_type = fields.Char(string = "Funding Doc Type")
	fund_doc_number = fields.Char(string = "Funding Doc Number")
	ticl_project_id = fields.Char(string = "Project Id")
	manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
	oem_pn = fields.Char(string = "OEM PN")
	product_function = fields.Char(string = "Function")
	product_lenght = fields.Float(string = "Lenght")
	product_width = fields.Float(string = "Width")
	product_height = fields.Float(string = "Height")
	weight = fields.Float(string = "Weight")
	product_squre_feet = fields.Float(string = "Square Feet")
	categ_id = fields.Many2one('product.category', string="Type")
	user_id = fields.Many2one('res.users', string='Responsible Persons', default=lambda self: self.env.user)
	order_from_receipt = fields.Boolean(string='Order from Receipt', default=False)


# 	@api.multi
	# def update_entries(self):
	# 	self.ensure_one()
	# 	action = self.env.ref('ticl_management.update_inventory_entries_action')
	# 	result = action.read()[0]
	# 	result['context']={'default_old_serial':self.serial_number}
	# 	return result
 
# 	@api.multi
	# def update_entries_model(self):
	# 	self.ensure_one()
	# 	action = self.env.ref('ticl_management.update_inventory_entries_action_model')
	# 	result = action.read()[0]
	# 	result['context']={'default_old_model':self.product_id.id}
	# 	return result