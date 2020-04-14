# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Employee(models.Model):
	_inherit = 'hr.employee'

	employee_code = fields.Char(string="Employee Id")
	employee_email = fields.Char(string="Personal Email")
	employee_mobile = fields.Char(string="Personal Mobile") 
	employee_address = fields.Text(string="Personal Address")
	street = fields.Char('Street')
	street2 = fields.Char('Street2')
	city_id = fields.Many2one('city.name', string="City")
	zip_ids = fields.Many2many('zip.code', string="Zip Code")
	state_id = fields.Many2one("res.country.state", string='State')
	country_id = fields.Many2one('res.country', string='Country')


# 	@api.multi
	def name_get(self):
		result = []
		for emp in self:
			employee_id = emp.employee_code
			if employee_id:
				emp_name_id = emp.name + '(' + str(employee_id) + ')'
			else:
				emp_name_id = emp.name
			result.append((emp.id, emp_name_id))	
		return result
