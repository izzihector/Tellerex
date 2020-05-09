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

_logger = logging.getLogger(__name__)



class TelAsnReceiving(models.Model):
    _name = 'tel.asn.receiving'
    _inherit = ['mail.thread']
    _description = "ASN Receiving"
    _order = "id desc"


    name = fields.Char(string='ASN Number', index=True)
    #asn_number = fields.Char(string='ASN Number', index=True)
    asn_received_date = fields.Date(string='ASN Received Date')
    bill_of_lading_number = fields.Char(string='Bill Of Lading Number')
    sending_location_id = fields.Many2one('stock.location', string='Sending Location')

    state = fields.Selection([
        ('draft', 'draft'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    asn_order_line = fields.One2many('tel.asn.receiving.line', 'asn_receiving_id', string='ASN Revceiving Lines', copy=True)    





class TelAsnReceivingLine(models.Model):
    _name = 'tel.asn.receiving.line'
    _inherit = ['mail.thread']
    _description = "ASN Receiving"
    _order = "id desc"


    name = fields.Text(string='Description')
    asn_receiving_id = fields.Many2one('tel.asn.receiving', string='ASN Reference', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    product_id = fields.Many2one('product.product', string='Model Name')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    model_serial_number = fields.Char(string='Serial #')
    count_number = fields.Char(string='Count')
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    tel_type = fields.Many2one('product.category', string="Type")
    funding_doc_type = fields.Char(string = "Funding Doc Type")
    funding_doc_number = fields.Char(string = "Funding Doc Number")
    ticl_project_id = fields.Char(string = "Project Id")
