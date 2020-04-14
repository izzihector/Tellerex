# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Partner(models.Model):
	_inherit = 'res.partner'

	name_gc = fields.Char(string="GC")
	company_name = fields.Char(string="Company Name")
	comments = fields.Char(string="Comments")
	gc_warehouse_identifier = fields.Char(String = "GC Warehouse unique Identifier")
	gc_address_id = fields.Char(String="GC Address Id")
	is_rigger = fields.Boolean(string="Is a Rigger", default=True)
