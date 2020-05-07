import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ManufacturerOrder(models.Model):
	_name = 'manufacturer.order'
	_description = "Manufacturer"

	 
	name = fields.Char(string="Manufacturer Name")
	active = fields.Boolean(string="Active", default=True)