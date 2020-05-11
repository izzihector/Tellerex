# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps
import json
import re


class AccountMove(models.Model):
    _inherit = "account.move"

    is_service = fields.Boolean(string='Is Service')

    # def _prepare_invoice_line_from_po_line(self, line):
    # 	vals = super()._prepare_invoice_line_from_po_line(line)
    # 	vals['qty_received'] = line.qty_received
    # 	vals['qty_invoiced'] = line.qty_invoiced
    # 	vals['date_planned'] = line.date_planned
    # 	vals['quantity'] = line.product_qty
    # 	vals['price_total'] = line.price_unit
    # 	vals['price_subtotal'] = line.price_unit
    # 	vals['tel_type'] = line.type_id.id
    # 	vals['condition_id'] = line.condition_id.id
    # 	return vals

    @api.onchange('purchase_id')
    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
    	super()._onchange_purchase_auto_complete()
    	self.is_service = self.purchase_id.is_service


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    disassembly_unit = fields.Selection([('yes', 'Yes'), ('no', 'No')],string='Disassembly Unit')
    tel_type = fields.Many2one('product.category', string="Type",track_visibility='onchange')
    tellerex_charges = fields.Float(string='Tellerex Charges')
    bank_chanrges = fields.Float(string='Chase Charges')
    chase_contract_date = fields.Datetime(string='Contract Date')
    qty_received= fields.Float(string='Received Quantity')
    qty_invoiced= fields.Float(string='Billed Quantity')
    date_planned = fields.Date(string='Scheduled Date')
    state_code = fields.Char('State')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')


class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"

	def create_invoices(self):
		res = super(SaleAdvancePaymentInv, self).create_invoices()
		sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
		for order in sale_orders:
			po = order.create_purchase_order()
			if order.is_service:
				po.is_service = True
				po.sales_num = order.name

		return res

