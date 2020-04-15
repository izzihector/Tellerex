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


class tel_serial_number(models.Model):
	_name = 'tel.serial.number'
	_description = "Serial Number"


	serial_number = fields.Char(string='Serial #')
	product_id = fields.Many2one('product.product', string='Model Name')
	active = fields.Boolean(string="Active", default=True, help="Set active to false to hide the Condition without removing it.")
