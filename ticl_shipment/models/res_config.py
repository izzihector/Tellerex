# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    autontication_key = fields.Char(string='Authontication Key')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key'),
        )
        return res

    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("ticl_shipment.autontication_key", self.autontication_key)
        return res
