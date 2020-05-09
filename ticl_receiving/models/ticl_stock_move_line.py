# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
import calendar


class TiclStockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _order = 'origin desc, id desc'

    order_from_receipt = fields.Boolean(string='Order from Receipt')
    product_id = fields.Many2one("product.product",string="Product ID")
    categ_id = fields.Many2one("product.category",string="type")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    ticl_warehouse_id = fields.Many2one('stock.location', string="TICL Warehouse")
    tel_receipt_id = fields.Many2one("ticl.receipt",string="TEL Receipt ID")
    manufacturer_id = fields.Many2one("manufacturer.order",string="Manufacturer")
    condition_id = fields.Many2one("ticl.condition", string="Condition")
    tel_receipt_summary_id = fields.Many2one('ticl.receipt.log.summary',string="TEL Receipt Summary ID")
    tel_unique_no = fields.Char(string="Unique Id")
    tel_note = fields.Char(string='Comment/Note')
    tel_cod = fields.Selection([('Y', 'Y'), ('N', 'N')],string='COD')
    attachment_ids = fields.Many2many('ir.attachment',string='Upload BOL #')
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')])
    pick_up_date = fields.Date(string='Pick up Date')
    shipment_date = fields.Date(string='Shipped Date')
    accepted_date = fields.Date(string='Accepted Date')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee')
    future_ship_date = fields.Date(string="Future Ship Date", track_visibility='onchange')
    future_ship_location = fields.Many2one('stock.location',string="Future Ship Location", track_visibility='onchange')
    received_date = fields.Date(string='Received Date')
    repalletize = fields.Selection(string="Repalletize", selection=[('y', 'Y'), ('n', 'N')])
    status = fields.Selection(
        [('inventory', 'Inventory'), ('assigned', 'Assigned'), ('picked', 'Picked'), ('packed', 'Packed'),
         ('shipped', 'Shipped'),
         ('sold', 'Sold'), ('cancel', 'Cancelled'), ('recycled', 'Recycled')],string='Status', default='inventory',
        track_visibility='onchange')
    processed_date = fields.Date(sring='Date Processed')
    recycled_date = fields.Date(sring='Recycled Date')
    scrap_tel_note = fields.Char(string='recycled Comments')

    monthly_service_charge = fields.Float(string='Monthly Service Charges', store=True)
    monthly_service_charge_total = fields.Char(string='Monthly Service Charges')
    total_service_charge = fields.Char(string="total_service_charge")
    inbound_charges = fields.Float(string='Inbound Charges')
    misc_log_time = fields.Char(string='Misc Log Time', default=0)
    misc_charges = fields.Float(string='Misc Charges')
    associated_fees = fields.Float(string='Inbound Associated Fees')
    cod_charges = fields.Float(string='COD Charges')
    repalletize_charge = fields.Float(string="Repalletize Charge")
    service_price = fields.Float(string='Price')
    tel_unique_no = fields.Char(string='Unique Number')
    shipping_status = fields.Selection(string=" Shipping Status",
                                       selection=[('NA', 'NA'), ('picked', 'Picked'), ('packed', 'Packed'),
                                                  ('shipped', 'Shipped')], default='NA')
    outbound_charges = fields.Float(string='Outbound Charges')
    outbound_associated_fees = fields.Float(string='Outbound Associated Fees')
    shipment_date = fields.Date(string='Shipped Date')
    cod_employee_id = fields.Many2one('hr.employee',string='COD Employee')
    refurbishment_charges = fields.Float(string='Refurbishment Charges', store=True)
    old_name = fields.Char(string='Old Receipt Id', index=True)
    shipment_id = fields.Char(string="Shipment Id")
    origin = fields.Char(string='Receipt Number')
    serial_number = fields.Char(string='Serial Number')
    sale_stock_move_id = fields.Char('Sale ID')
    sale_old_id = fields.Char('Sale Old ID')
    sale_import_data = fields.Boolean("Imported Data")
    sale_type = fields.Char('Sale Type')
    sale_date = fields.Char('Sold Date')
    sale_date_pick = fields.Date('Sold Date')
    sale_gross = fields.Char('Sale Gross')
    sale_net = fields.Char('Sale Net')
    sale_commission = fields.Char('Sale Commission')
    sale_check_number = fields.Char('Sale Check Number')
    sending_location_id = fields.Many2one('res.partner', string='Origin Location')