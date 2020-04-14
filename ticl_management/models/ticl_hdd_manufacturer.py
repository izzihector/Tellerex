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


class ticl_hdd_manufacturer(models.Model):
	_name = 'ticl.hdd.manufacturer'
	_description = "HDD Manufacturer"

	 
	name = fields.Char(string="HDD Manufacturer")
	active = fields.Boolean(string="Active", default=True)