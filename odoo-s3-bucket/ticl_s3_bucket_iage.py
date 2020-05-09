# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    S3 buckets image
###################################################################################

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import os


class ticl_receipt_log_summary_line(models.Model):
    _inherit = 'ticl.receipt.log.summary.line'


    # @api.one
    @api.depends('attachment_ids','atm_count')
    def count_atm(self):
        x = self.attachment_ids
        if len(x.ids) != 0:
            if len(x.ids) > 5:
                self.attachment_ids = self.attachment_ids[0:5]
        self.atm_count = len(self.attachment_ids.ids)

    # @api.one
    @api.depends('attachment_ids_epp', 'epp_count')
    def count_epp(self):
        x = self.attachment_ids_epp
        if len(x.ids) != 0:
            if len(x.ids) > 2:
                self.attachment_ids_epp = self.attachment_ids_epp[0:2]
        self.epp_count = len(self.attachment_ids_epp.ids)

    # @api.one
    @api.depends('attachment_ids_hdd', 'hdd_count')
    def count_hdd(self):
        x = self.attachment_ids_hdd
        if len(x.ids) != 0:
            if len(x.ids) > 2:
                self.attachment_ids_hdd = self.attachment_ids_hdd[0:2]
        self.hdd_count = len(self.attachment_ids_hdd.ids)



    atm_attachment1 = fields.Many2many('ir.attachment', 'class_ir_attachments1_rel', 'class_id', 'attachment_id1',string="Upload EPP Images")
    atm_attachment2 = fields.Many2many('ir.attachment', 'class_ir_attachments2_rel', 'class_id', 'attachment_id2',string="Upload Hard Disk Images")
    atm_attachment3 = fields.Many2many('ir.attachment', 'class_ir_attachments3_rel', 'class_id', 'attachment_id3',"Upload ATM Images")
    attachment_ids = fields.Many2many("ir.attachment", 'class_ir_attachmentsatm_rel', 'class_id', 'attachment_ids',string="ATM")
    attachment_ids_epp = fields.Many2many("ir.attachment", 'class_ir_attachmentsepp_rel', 'class_id', 'attachment_ids_epp',string="EPP")
    attachment_ids_hdd = fields.Many2many("ir.attachment",'class_ir_attachmentshdd_rel', 'class_id', 'attachment_ids_hdd',string="HDD")
    import_files = fields.Char(string="Files")
    import_files_epp = fields.Char(string="Files")
    import_files_hdd = fields.Char(string="Files")

    atm_count = fields.Integer('ATM Images Count',compute="count_atm")
    epp_count = fields.Integer('EPP Images Count',compute="count_epp")
    hdd_count = fields.Integer('HDD Images Count',compute="count_hdd")

    hdd_serial_num = fields.Char('HDD Serial #')
    epp_serial_num = fields.Char('EPP Serial #')
    epp_manufacturer = fields.Many2one('ticl.epp.manufacturer', string="EPP Manufacturer")
    hdd_manufacturer = fields.Many2one('ticl.hdd.manufacturer', string="HDD Manufacturer")

    # @api.onchange('attachment_ids_hdd')
    # def upload_restrict_1(self):
    #     x = self.attachment_ids_hdd
    #     if len(x.ids) != 0:
    #         if len(x.ids)>2:
    #             self.attachment_ids_hdd = self.attachment_ids_hdd[0:2]

    # @api.onchange('attachment_ids_epp')
    # def upload_restrict_2(self):
    #     x = self.attachment_ids_epp
    #     if len(x.ids) != 0:
    #         if len(x.ids) > 2:
    #             self.attachment_ids_epp = self.attachment_ids_epp[0:2]

    # @api.onchange('attachment_ids')
    # def upload_restrict_3(self):
    #     x = self.attachment_ids
    #     if len(x.ids) != 0:
    #         if len(x.ids) > 5:
    #             self.attachment_ids = self.attachment_ids[0:5]
