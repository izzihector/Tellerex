# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class wizardScrap(models.TransientModel):
    _name = 'ticl.stock.move.scrap'

    scrap_lines = fields.One2many('ticl.stock.move.scrap.line', 'scrap_id', ondelete='cascade',track_visibility='onchange')
    scrap = fields.Many2one('stock.scrap',domain=[('state', '=', 'draft')])
    show_scrap = fields.Boolean(default=False)
    
    @api.multi
    def new_scrap(self):
        scrap_lines = []
        condition = self.env['ticl.condition'].sudo().search([('name','=','To Recommend')])
        condition_ids = self.scrap_lines.mapped('condition_id')
        print(condition_ids.ids)
        print(condition.ids)
        extra_condition = list(set(condition_ids.ids) - set(condition.ids))
        print(extra_condition)
        if extra_condition:
            raise ValidationError(_("All scrap items condition should be To Recommend. Please review it."))
        view_id = self.env.ref('ticl_scrap_management.stock_scrap_view_form_inherit_ticl').id
        locations = self.scrap_lines.mapped('location_id')
        if len(locations) > 1:
            raise ValidationError(_("All scrap items location must be same. Please review it."))
        oth_state = self.scrap_lines.filtered(lambda r: r.state != 'inventory')
        if oth_state:
            raise ValidationError(_("Remove items which are not inventory state."))
        unique_ids = self.scrap_lines.mapped('unique_id')
        if unique_ids:
            scr_ln_store = self.env['ticl.stock.move.scrap.line.store'].sudo().search([('unique_id','in',unique_ids)])
            scr_ln_store.sudo().unlink()
        for line in self.scrap_lines:
            d = {
                'product_id':line.product_id.id,
                'manufacturer_id':line.manufacturer_id.id,
                'tel_type':line.tel_type.id,
                'scrap_qty':1,
                'tel_note':line.tel_note,
                'location_id':line.location_id.id,
                'lot_id':line.lot_id.id
            }
            scrap_lines.append((0,0,d))
        scrp_id = self.env['stock.scrap'].create({'scrap_lines':scrap_lines,'location_id':locations[0].id})
        action = self.env.ref('stock.action_stock_scrap').read()[0]
        action['views'] = [(view_id, 'form')]
        action['context'] = {'form_view_initial_mode': 'edit'}
        action['res_id'] = scrp_id.id
        return action
    
    @api.multi
    def update_scrap(self):
        if not self.scrap:
            raise ValidationError(_("Please choose a scrap order."))
        
        scrap_lines = []
        condition = self.env['ticl.condition'].sudo().search([('name','=','To Recommend')])
        condition_ids = self.scrap_lines.mapped('condition_id')
        extra_condition = list(set(condition_ids.ids) - set(condition.ids))
        if extra_condition:
            raise ValidationError(_("All scrap items condition should be To Recommend. Please review it."))
        view_id = self.env.ref('ticl_scrap_management.stock_scrap_view_form_inherit_ticl').id
        locations = self.scrap_lines.mapped('location_id')
        if len(locations) > 1:
            raise ValidationError(_("All scrap items location must be same. Please review it."))
        if len(locations) == 1:
            if self.scrap.location_id.id != locations.id:
                raise ValidationError(_("All scrap items location must be same. Please review it."))
        
        oth_state = self.scrap_lines.filtered(lambda r: r.state != 'inventory')
        if oth_state:
            raise ValidationError(_("Remove items which are not inventory state."))
        
        unique_ids = self.scrap_lines.mapped('unique_id')
        if unique_ids:
            scr_ln_store = self.env['ticl.stock.move.scrap.line.store'].sudo().search([('unique_id','in',unique_ids)])
            scr_ln_store.sudo().unlink()
        
        for line in self.scrap_lines:
            d = {
                'product_id':line.product_id.id,
                'manufacturer_id':line.manufacturer_id.id,
                'tel_type':line.tel_type.id,
                'scrap_qty':1,
                'tel_note':line.tel_note,
                'location_id':line.location_id.id,
                'lot_id':line.lot_id.id
            }
            scrap_lines.append((0,0,d))
        self.scrap.scrap_lines = scrap_lines
        return {
            'name':'Scrap Data',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.scrap',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': self.scrap.id,
            'context': {},
        }
        
       
        
    @api.multi
    def select_scap(self):
        self.ensure_one()
        self.show_scrap = True
        return {
            'name':'Scrap Data',
            'type': 'ir.actions.act_window',
            'res_model': 'ticl.stock.move.scrap',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': {'default_scrap_lines':self.scrap_lines},
        }
        
    @api.multi
    def cancel_select_scap(self):
        self.ensure_one()
        self.show_scrap = False
        return {
            'name':'Scrap Data',
            'type': 'ir.actions.act_window',
            'res_model': 'ticl.stock.move.scrap',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': {'default_scrap_lines':self.scrap_lines},
        }

class wizardScrapLine(models.TransientModel):
    _name = 'ticl.stock.move.scrap.line'
       
    product_id = fields.Many2one(
        'product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])],
        )
    scrap_qty = fields.Float('Quantity', default=1.0)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Serial Number')
    tel_type = fields.Many2one('product.category', string="Type")
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    tel_note = fields.Char(string='Comment/Note')
    move_id = fields.Many2one('stock.move', 'Scrap Move')
    unique_id = fields.Char('Unique No.')
    location_id = fields.Many2one('stock.location', 'Location')
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location')
    tel_note = fields.Char(string='Comment/Note')
    state = fields.Selection( string='Inventory Status', related="move_id.status",store=True)
    scrap_id = fields.Many2one('ticl.stock.move.scrap', invisible=1)
    origin = fields.Char(string='Source Document')
    user_id = fields.Many2one('res.users')
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    
    
        
    
class wizardScrapLineStore(models.Model):
    _name = 'ticl.stock.move.scrap.line.store'
    
    product_id = fields.Many2one(
        'product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])],
        required=True)
    scrap_qty = fields.Float('Quantity', default=1.0)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Serial Number')
    tel_type = fields.Many2one('product.category', string="Type")
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    tel_note = fields.Char(string='Comment/Note')
    move_id = fields.Many2one('stock.move', 'Scrap Move')
    unique_id = fields.Char()
    location_id = fields.Many2one('stock.location', 'Location')
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location')
    tel_note = fields.Char(string='Comment/Note')
    state = fields.Selection( string='Inventory Status', related="move_id.status",store=True)
    origin = fields.Char(string='Source Document')
    user_id = fields.Many2one('res.users')
    is_scrap = fields.Boolean(default=False)
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    
    @api.model
    def delete_related(self, vals):
        d_record = self.sudo().search([('unique_id','=',vals.get('delete_id'))])
        if d_record:
            d_record.sudo().unlink()
        return True
    
    
