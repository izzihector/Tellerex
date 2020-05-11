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
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ticl_sale_contract(models.Model):
	_name = 'ticl.sale.contract'
	_description = "Sale Contract"

	name = fields.Char(string="Contract Name")
	active = fields.Boolean(string="Active", default=True, help="Set active to false to hide the Condition without removing it.")
	contract_attachment_ids = fields.Many2many('ir.attachment', string='Upload Contract #')
	contract_line = fields.One2many('ticl.sale.contract.line', 'contract_id', string='Contract Lines', auto_join=True)
	
	@api.model
	def create(self, vals):
		contract = self.search([('active','=',True)])
		if contract:
			raise UserError('Allready there is a active contract.')
		return super(ticl_sale_contract, self).create(vals)


class SaleContractLine(models.Model):
	_name = 'ticl.sale.contract.line'
	_description = "Sale Contract Line"
	
	commission = fields.Float(string='Commission')
	start_date = fields.Datetime(string="Contract Start Date")
	end_date = fields.Datetime(string="Contract End Date")
	contract_id = fields.Many2one('ticl.sale.contract', string='Contract', ondelete='cascade', index=True, copy=False)
	