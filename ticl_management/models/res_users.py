import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Users(models.Model):
    _inherit = 'res.users'

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    location_dest_id = fields.Many2one('stock.location', string="Location")
    funding_doc_type = fields.Char(string = "Funding Doc Type")
    funding_doc_number = fields.Char(string = "Funding Doc No.")
    ticl_project_id = fields.Char(string = "Project Id")
	