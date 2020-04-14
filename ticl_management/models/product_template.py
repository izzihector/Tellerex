# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

from odoo import api, fields, models, tools, _


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    #Onchange for XL Items
    @api.onchange('categ_id')
    def onchange_product_type(self):
        if self.categ_id.name == 'ATM':
            self.xl_items = 'n'
        else:
            self.xl_items = 'y'

    model_name = fields.Char(string="Model Name")
    monitory_value = fields.Char(string="Monitory Value")
    part_name = fields.Char(string="Version Number")
    serial_number = fields.Char(string = "Serial Number")
    oem_pm = fields.Char(string = "OEM PM")
    product_function = fields.Char(string = "Function")
    product_weight = fields.Char(string = "Weight")
    product_lenght = fields.Float(string = "Lenght")
    product_width = fields.Float(string = "Width")
    product_height = fields.Float(string = "Height")
    product_squre_feet = fields.Float(string = "Square Feet")
    sale_ok = fields.Boolean('Can be Sold', default=False)
    purchase_ok = fields.Boolean('Can be Purchased', default=False)
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    atm_ok = fields.Boolean('ATM', default=True)
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')])
    #cost_currency_id = fields.Many2one('res.currency', string="Cost Currency")
    ticl_product_id = fields.Many2one('product.product', string='Attached Accessories')


    # @api.multi
    # def name_get(self):
    #     self.read(['name', 'part_name'])
    #     return [(template.id, '%s %s' % (template.name, template.part_name and '[%s] ' % template.part_name or '')) for template in self]

class ProductProduct(models.Model):
    _inherit = "product.product"


    atm_ok = fields.Boolean('ATM', default=True)

    # @api.multi
    # def name_get(self):
    #     self.read(['name', 'part_name'])
    #     return [(template.id, '%s %s' % (template.product_tmpl_id.name, template.product_tmpl_id.part_name and '[%s] ' % template.product_tmpl_id.part_name or '')) for template in self]
