# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import api, fields, models, _


class sh_message_wizard(models.TransientModel):
    _name = "sh.message.wizard"
    _description = "Message wizard to display warnings, alert ,success messages"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Text(string="Message", readonly=True, default=get_default)


class serial_number_history(models.TransientModel):
    _name = "serial.number.history"
    _description = "Message wizard to display Serial Number History !"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Html(string="Serial Number History", readonly=True, default=get_default)


class stand_not_available(models.TransientModel):
    _name = "stand.not.available"
    _description = "Message wizard to display Stand not Available !"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Html(string="Stand Not Available", readonly=True, default=get_default)

    def byepass_stand(self):
        self.env.context = dict(self.env.context)
        self.env.context.update({'byepass': True})
        ship_id = self._context.get('active_id')
        ship = self.env['ticl.shipment.log'].browse(ship_id)
        return ship.ticl_echo_shipment()


