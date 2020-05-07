# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ticl_epp_manufacturer(models.Model):
	_name = 'ticl.epp.manufacturer'
	_description = "EPP Manufacturer"

	 
	name = fields.Char(string=" EPP Manufacturer")
	active = fields.Boolean(string="Active", default=True)