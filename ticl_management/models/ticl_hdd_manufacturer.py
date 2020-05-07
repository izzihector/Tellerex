# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ticl_hdd_manufacturer(models.Model):
	_name = 'ticl.hdd.manufacturer'
	_description = "HDD Manufacturer"

	 
	name = fields.Char(string="HDD Manufacturer")
	active = fields.Boolean(string="Active", default=True)