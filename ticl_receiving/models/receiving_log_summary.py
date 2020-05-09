# -*- coding: utf-8 -*-
import json
import re
import uuid
from functools import partial
from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode
from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
from odoo.tools.misc import formatLang
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons import decimal_precision as dp
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)



class receiving_log_summary(models.Model):
    _name = 'receiving.log.summary'
    _inherit = ['mail.thread']
    _description = "Receiving Log Shipment Summary"
    _order = "id desc"


    name = fields.Char(string='Shipment ID', index=True)
    tel_note = fields.Text(string='Note')
    asn_received_date = fields.Date(string='Received Date')
    expected_delivery_date = fields.Date(string='Delivery Date', default=datetime.date(datetime.now()))
    bill_of_lading_number = fields.Char(string='Bill of Lading (BOL)')
    sending_location_id = fields.Many2one('stock.location', string='Sending Location')
    receiving_id = fields.Many2one('tel.asn.receiving', string="ASN Number")
    warehouse_id = fields.Many2one('stock.warehouse', string='Receiving warehouse')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    state = fields.Selection([('draft', 'Draft'),('pending','Pending'),('completed','Completed'),('cancel', 'Cancelled')],
        string='Status', default='pending')

    total_atm = fields.Char(string='# of ATM')
    total_signage = fields.Char(string='# of Signage')
    total_accessory = fields.Char(string='# of Accessories')

    asn_bol_type = fields.Selection([('asn', 'ASN'),('bol','BOL')], string='Type', default='bol')

    receiving_log_line = fields.One2many('receiving.log.summary.line', 'receiving_log_id', string='ASN Revceiving Lines', copy=True)    
    tel_receiving_log_id = fields.Many2one("tel.receiving", string="TEL Received Log ID")
    tel_receipt_log_id = fields.Many2one("ticl.receipt", string="TEL Received ID")





class receiving_log_summary_line(models.Model):
    _name = 'receiving.log.summary.line'
    _inherit = ['mail.thread']
    _description = "Receiving Log Shipment Line Summary"
    _order = "id desc, tel_unique_no desc"



    name = fields.Text(string='Description')
    received_date = fields.Date(string='Received Date', default=datetime.date(datetime.now()))
    check_asn = fields.Boolean(string="Check ASN", required=True)
    receiving_log_id = fields.Many2one('receiving.log.summary', string='Receiving Log Shipment Summary', required=True, 
    ondelete='cascade', index=True, copy=False, readonly=True)
    product_id = fields.Many2one('product.product', string='Model Name')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    serial_number = fields.Char(string='Serial #   ')
    count_number = fields.Char(string='Count', default=1)
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    tel_type = fields.Many2one('product.category', string="Type")
    funding_doc_type = fields.Char(string = "Funding Doc Type")
    funding_doc_number = fields.Char(string = "Funding Doc Number")
    ticl_project_id = fields.Char(string = "Project Id")
    tel_receiving_log_id = fields.Many2one("tel.receiving", string="TEL Received Log ID")
    tel_receipt_log_id = fields.Many2one("ticl.receipt", string="TEL Received ID")

    #unique_id_number1 = fields.Integer(compute='_compute_get_number',store=True, string = "Unique Id")
    tel_unique_no = fields.Char(string="Unique Id")

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('receiving.log.summary.line') or '/'
        vals['tel_unique_no'] = seq
        return super(receiving_log_summary_line, self).create(vals)


    # @api.one
    # def _compute_get_number(self):
    #     for line in self:
    #         self.unique_id_number1 = 1 + 1


    # @api.depends('unique_id_number', 'receiving_log_id')
    # def _compute_get_number(self):
    #     for order in self.mapped('receiving_log_id'):
    #         unique_id_number = 1
    #         for line in self:
    #             line.unique_id_number = unique_id_number
    #             unique_id_number += 1
























