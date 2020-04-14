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



class city_name(models.Model):
	_name = 'city.name'
	_description = "City"

	name = fields.Char(string="City Name")
	active = fields.Boolean(default=True, help="Set active to false to hide the Condition without removing it.")
	zip_ids = fields.Many2many('zip.code', string="Zip Code")
	state_id = fields.Many2one('res.country.state', string="State Name")
	country_id = fields.Many2one('res.country', string="Country Name")


class zip_code(models.Model):
	_name = 'zip.code'
	_description = "Zip Code"

	name = fields.Char(string="Zip Code")
	active = fields.Boolean(default=True, help="Set active to false to hide the Condition without removing it.")


class ResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	@api.onchange('city_id', 'state_id','country_id')
	def onchange_city_id(self):
		self.state_id = self.city_id.state_id.id or ''
		self.country_id = self.city_id.country_id.id or ''

	city_id = fields.Many2one('city.name', string="City Name")
	zip_ids = fields.Many2many('zip.code', string="Zip Code")
	abc_test = fields.Char(string="test")





