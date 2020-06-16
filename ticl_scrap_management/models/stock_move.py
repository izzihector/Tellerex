from datetime import datetime
from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    
    recycled_date = fields.Datetime(string="Recycled Date")