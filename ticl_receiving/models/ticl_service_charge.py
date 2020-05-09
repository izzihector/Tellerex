# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ticl_service_charge(models.Model):
    _name = 'ticl.service.charge'
    _description = "Service Charges"


#     @api.one
    @api.depends('product_id')
    def _get_name(self):
        self.name = self.product_id.name
    
    
    name = fields.Char(string='Service',compute='_get_name',store=True)
    service_price = fields.Float(string='Price')
    active = fields.Boolean(string="Active", default=True)
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')])
    monthly_service_charge = fields.Boolean(string="Monthly Charges")
    product_id = fields.Many2one('product.product', string="Service Type",domain=[('type','=','service')])
