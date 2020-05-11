# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
import datetime
from odoo import models, fields, api, _
import calendar

class ticl_pending_shipment_report(models.TransientModel):
    _name = "ticl.pending.shipment.report"
    _description = "Pending Shipment Report"

    @api.onchange('from_date', 'to_date')
    def onchange_week(self):
        from_date = str(self.from_date)
        to_date = str(self.to_date)
        if to_date < from_date:
            return {
                'warning': {
                    'title': "Warning",
                    'message': "To Date Should be higher than From Date",
                }
            }

    from_date = fields.Datetime(string='From Date')
    to_date = fields.Datetime(string='To Date')
    pending_shipping_file = fields.Binary('Pending Shipment Report')
    file_name = fields.Char('File Name')
    pending_report_printed = fields.Boolean('Pending Shipment Report')
    report_type = fields.Char(default="pending_shipment")
    warehouse_ids = fields.Many2many('stock.location', string='Warehouse')


    @api.multi
    def action_print_pending_shipment_report(self):
        if self.report_type == 'pending_shipment':
            return {
                'type': 'ir.actions.report',
                'report_name': 'ticl_shipment.pending_report',
                'model': 'ticl.pending.shipment.report',
                'report_type': "qweb-pdf",
            }


    @api.multi
    def get_pending_report_values(self,data=None):
        date_split_1 = str(self.from_date).split(" ")
        date_split_2 = str(self.to_date).split(" ")

        if self.warehouse_ids.ids == []:
            docs = self.env['ticl.shipment.log'].search([('appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                            ('appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                            ('state', 'in', ['draft','picked', 'packed'])
                                                            ])
        else:
            docs = self.env['ticl.shipment.log'].search([('appointment_date_new', '>=', date_split_1[0] +' 00:00:00'),
                                                            ('appointment_date_new', '<=', date_split_2[0] +' 23:59:59'),
                                                            ('state', 'in', ['draft','picked', 'packed']),
                                                            ('sending_location_id', 'in', self.warehouse_ids.ids),
                                                            ])

        return docs