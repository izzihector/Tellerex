# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Partner(models.Model):
	_inherit = 'res.partner'

	contact_name = fields.Char(string="Contact Name")
	is_rigger = fields.Boolean(string="Is a Rigger", default=True)
