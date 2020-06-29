import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning
import threading
import urllib3
import json
import requests
import logging
from datetime import datetime, timedelta
from collections import OrderedDict

_logger = logging.getLogger(__name__)

class TiclScrapCancel(models.TransientModel):
    _name = 'ticl.scrap.cancel'
    _description = __doc__


    ticl_cancel_reason = fields.Char(string="Cancel Reason Scrap")


    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        print("Act close", act_close)
        scrap_ids = self._context.get('active_ids')
        print("Scrap Ids", scrap_ids)
        if scrap_ids is None:
            return act_close
        assert len(scrap_ids) == 1, "Only 1 Scrap ID expected"
        scrap = self.env['stock.scrap'].browse(scrap_ids)
        scrap.ticl_scrap_cancel_reason = self.ticl_cancel_reason

        if scrap.state == 'draft':
            scrap.state = 'cancel'
            for ids in scrap.scrap_lines:
                ids.move_line_id.write({'status': 'inventory'})
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Scrap cancelled successfully!"
            return {
            'name': 'Warning',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'view': [('view', 'form')],
            'target': 'new',
            'context': context,
            }

        return act_close
