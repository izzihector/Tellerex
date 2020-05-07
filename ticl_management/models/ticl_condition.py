# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ticl_condition(models.Model):
	_name = 'ticl.condition'
	_description = "Condition"


	name = fields.Char(string="Condition Name")
	active = fields.Boolean(string="Active", default=True, help="Set active to false to hide the Condition without removing it.")
