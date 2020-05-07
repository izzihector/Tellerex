# -*- coding: utf-8 -*-
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
