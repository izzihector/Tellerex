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


class shipping_carrier(models.Model):
	_name = 'shipping.carrier'
	_description = "Shipping Carrier"


	name = fields.Char(string="Carrier Name")
	address = fields.Char(string="Carrier Address")
	active = fields.Boolean(string="Active", default=True, help="Set active to false to hide the Condition without removing it.")
