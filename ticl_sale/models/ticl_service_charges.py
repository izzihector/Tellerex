from odoo import api, fields, models, _

class MonthlyServiceCharge(models.Model):
    _inherit = "ticl.service.charge"
    
    
    product_id = fields.Many2one('product.product', string="Service Type",domain=[('type','=','service')])
    
    
class ProductPerCount(models.Model):
    _name = "pallet.count"
    
    tel_type = fields.Many2one('product.category', string="Type")
    name = fields.Selection([('atm', 'ATM'), ('lockbox', 'Lockbox'),('accessory','Accessory'),('signage','Signage')], string="Product Type")
    count = fields.Integer('Pallet Count')
    product_id = fields.Many2one('product.product', string="Service Type",domain=[('type','!=','service')])



    # Filter Product Basis of Product TYpe
    @api.onchange('tel_type')
    def onchange_product_type(self):
        res = {}
        if self.tel_type.name == 'ATM':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
        
        #Accessory
        elif self.tel_type.name == 'Accessory':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
            
        elif self.tel_type.name == 'Signage':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}

        #Lockbox
        elif self.tel_type.name == 'Lockbox':
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}

        else:
            res['domain']={'product_id':[('categ_id', '=', self.tel_type.id)]}
        
        return res