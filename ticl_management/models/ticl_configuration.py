# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class fund_doc_type(models.Model):
	_name = 'fund.doc.type'
	_description = "Funding Doc Type"


	name = fields.Char(string="Funding Doc Type")
	doc_desc = fields.Text(string="Description")
	doc_code = fields.Char(string="Code")
	active = fields.Boolean(string="Active", default=True, help="Set active to false to hide the Funding Doc Type without removing it.")
