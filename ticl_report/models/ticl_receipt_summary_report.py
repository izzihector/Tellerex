import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import os


class ticl_receipt_log_summary(models.Model):
    _inherit = 'ticl.receipt.log.summary'


    def print_placard_label(self):
    	print("-----gfhfghfgh------")
    	for line in self.ticl_receipt_summary_lines:
    		print("===atm22222=====")
	    	if line.tel_type.name == 'ATM':
	    		print("===atm=====")
	    		return self.env.ref('ticl_report.action_report_ticl_receipt')\
	    		.with_context({'discard_logo_check': True}).report_action(self)
