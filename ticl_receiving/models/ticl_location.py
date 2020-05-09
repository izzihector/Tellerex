import time
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
import calendar

class StockLocation(models.Model):
	_name = 'stock.location'
	_inherit = ['stock.location']

	is_location = fields.Boolean('Is Location')
	warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
	warehouse_key = fields.Char(string='Warehouse')

