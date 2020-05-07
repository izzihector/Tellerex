# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Warehouse(models.Model):
	_inherit = 'stock.warehouse'

	warehouse_key = fields.Char(string="Warehouse Key")
	checkin_time = fields.Char(string="CheckIn Time")
	checkout_time = fields.Char(string="CheckOut Time")  
	warehouse_phone = fields.Char(string="ContactPhone", size=12)
	warehouse_email = fields.Char(string="Email")
	street = fields.Char('Address Line 1')
	street2 = fields.Char('Address Line 2')
	city_id = fields.Many2one('city.name', string="City")
	state_id = fields.Many2one("res.country.state", string='State')
	zip_code = fields.Char(string='PostalCode')
	contact_name = fields.Char(string='Contact Name')

	appointment_date = fields.Datetime(string='AppointmentDate')
	reference_number = fields.Char(string="ReferenceNumber")
	location_type = fields.Selection([('RESIDENTIAL', 'RESIDENTIAL'),
									  ('CONSTRUCTIONSITE', 'CONSTRUCTIONSITE'),
									  ('TRADESHOW', 'TRADESHOW'),
									  ('BUSINESS', 'BUSINESS')], string='Location Types')


class Location(models.Model):
	_inherit = 'stock.location'
	
	gc_name = fields.Char(string="GC")
	gc_address_id = fields.Char(String="GC Address Id")
	company_name = fields.Char(string="Company Name")
	street = fields.Char('Address')
	street2 = fields.Char('Address 2')
	city_id = fields.Many2one('city.name', string="City")
	state_id = fields.Many2one("res.country.state", string='State')
	zip_code = fields.Char(string='PostalCode')
	contact_name = fields.Char(string='Contact Name')
	location_phone = fields.Char(string="Phone", size=12)
	location_email = fields.Char(string="Email")
	comments = fields.Char(string="Comments")
	gc_warehouse_identifier = fields.Char(string="GC Identifier")

	appointment_date = fields.Datetime(string='AppointmentDate')
	reference_number = fields.Char(string="ReferenceNumber")
	location_type = fields.Selection([('RESIDENTIAL', 'RESIDENTIAL'),
									  ('CONSTRUCTIONSITE', 'CONSTRUCTIONSITE'),
									  ('TRADESHOW', 'TRADESHOW'),
									  ('BUSINESS', 'BUSINESS')], string='Location Types')
	
	