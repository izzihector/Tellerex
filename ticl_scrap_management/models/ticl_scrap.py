from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import float_compare
import logging
from odoo.exceptions import UserError, Warning

_logger = logging.getLogger(__name__)


class ticl_scrap_stock(models.Model):
    _inherit = 'stock.scrap'
    
    def count_moves(self):
        moves = self.mapped('scrap_lines.move_id')
        self.move_count = len(moves) if moves else 0
        
    def _get_default_location_id(self):
        location = self.env['stock.location'].search([('is_location', '=', True),('name','=','Chase Atlanta')], limit=1)
        if location:
            return location.id
        return None
    
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id, track_visibility='onchange')
    scrap_lines = fields.One2many('stock.scrap.line', 'scrap_id', ondelete='cascade',track_visibility='onchange')
    move_count = fields.Integer(compute="count_moves",track_visibility='onchange')
    date_expected_new = fields.Date('Create Date', store=True,track_visibility='onchange')
    
    @api.model
    def create(self, vals_list):
        if vals_list.get('scrap_lines',False):
            for line in vals_list.get('scrap_lines'):
                product_id = line[2].get('product_id')
                product = self.env['product.product'].browse(product_id)
                uom = product.product_tmpl_id.uom_id
                line[2].update({'product_uom_id':uom.id})
                vals_list.update({'product_id':product_id,'product_uom_id':uom.id})
            return super(ticl_scrap_stock, self).create(vals_list)
        else:
            try:
                return super(ticl_scrap_stock, self).create(vals_list)
            except:

                raise UserError(_("No Scrap Items"))




    def action_validates(self, lines):
        for scrap_line in lines:
            if scrap_line[0].lot_id:
                scrap_line[0].lot_id.is_scraped = True
            mv = self.env['stock.move.line'].search(scrap_line[1],
                                                       limit=int(scrap_line[0].scrap_qty))
            mv.sudo().write({'status':'recycled','scrap_line_id':scrap_line[0].id,'recycled_date':scrap_line[0].date_expected_new,'scrap_tel_note': scrap_line[0].scrap_tel_note})


    
    def action_validate(self):
        self.ensure_one()
        condition = self.env['ticl.condition'].search([('name','=','To Recommend')])
        lst =[]
        for scrap_line in self.scrap_lines:
            print("==ttttttt===",scrap_line.location_id.name)
            if scrap_line.product_id.type != 'product':
                return scrap_line.do_scrap()
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            domain = [('product_id','=',scrap_line.product_id.id),
                      ('order_from_receipt','=',True),
                      ('condition_id','=',condition.id),
                      ('status','=','inventory')]
            print("==111111111111111===",domain)          
#             available_qty = sum(self.env['stock.quant']._gather(scrap_line.product_id,
#                                                                 scrap_line.location_id,
#                                                                 scrap_line.lot_id,
#                                                                 scrap_line.package_id,
#                                                                 scrap_line.owner_id,
#                                                                 strict=True).mapped('quantity'))
            if scrap_line.lot_id:
                domain += [('serial_number','=',scrap_line.lot_id.name)]
            
            available_move = self.env['stock.move.line'].search(domain)
            print("==domaindomaindomaindomain===",available_move)
            available_qty = float(len(available_move)) if available_move else 0.0
            scrap_qty = scrap_line.product_uom_id._compute_quantity(scrap_line.scrap_qty, scrap_line.product_id.uom_id)
            
            if float_compare(available_qty, scrap_qty, precision_digits=precision) >= 0:
                lst.append([scrap_line, domain])
                
            else:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view or False
                context = dict(self._context or {})
                context['message'] = 'The Product ' + str(scrap_line.product_id.name) + ' is not available in sufficient quantity in ' + str(self.location_id.name)
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
        if len(lst) == len(self.scrap_lines):
           self.action_validates(lst)
        return self.scrap_lines.do_scrap()
        
                
    def action_get_stock_move_lines(self):
        action = self.env.ref('stock.stock_move_line_action').read([])[0]
        move_ids = self.scrap_lines.mapped('move_id').ids
        action['domain'] = [('move_id', 'in', move_ids)]
        return action

class ticl_scrap_stock_line(models.Model):
    _name = 'stock.scrap.line'
    
    def _default_to_recommend(self):
        return self.env['ticl.condition'].search([('name', '=', 'To Recommend')], limit=1).id

    def _default_unit(self):
        return self.env['uom.uom'].search([('name', '=', 'Units')], limit=1).id
    
    product_id = fields.Many2one(
        'product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])],
        required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure',required=True, default=_default_unit)
    scrap_qty = fields.Float('Quantity', default=1.0)
    lot_id = fields.Many2one('stock.production.lot', 'Serial Number')
    scrap_id = fields.Many2one('stock.scrap', invisible=1)
    condition_id = fields.Many2one('ticl.condition', string="Condition",default=_default_to_recommend)
    tel_type = fields.Many2one('product.category', string="Type", store=True)
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    tel_note = fields.Char(string='Comment/Note')
    scrap_tel_note = fields.Char(string='Comment/Note')
    scrap_date = fields.Datetime(string='Scrap Date', default=fields.Datetime.now)
    package_id = fields.Many2one('stock.quant.package', 'Package', related="scrap_id.package_id",store=True)
    owner_id = fields.Many2one('res.partner', 'Owner', related="scrap_id.owner_id",store=True)
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    move_line_id = fields.Many2one('stock.move.line', 'Scrap Move Line', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', related="scrap_id.location_id",store=True)
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location', related="scrap_id.scrap_location_id",store=True)
    tracking = fields.Selection('Product Tracking', readonly=True, related="product_id.tracking")
    name = fields.Char(related="scrap_id.name",store=True)
    origin = fields.Char(related="scrap_id.origin",store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')], string='Status', default="draft")
    date_expected_new = fields.Date('Scrap Date', store=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', related="scrap_id.picking_id",store=True)
    ticl_checked = fields.Boolean(default=False)
    
    
    def _prepare_move_values(self):
        self.ensure_one()
        return {
            'name': self.name,
            'origin': self.origin or self.picking_id.name or self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.scrap_qty,
            'location_id': self.location_id.id,
            'scrapped': True,
            'location_dest_id': self.scrap_location_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                           'product_uom_id': self.product_uom_id.id, 
                                           'qty_done': self.scrap_qty,
                                           'location_id': self.location_id.id, 
                                           'location_dest_id': self.scrap_location_id.id,
                                           'package_id': self.package_id.id, 
                                           'owner_id': self.owner_id.id,
                                           'lot_id': self.lot_id.id, })],
#             'restrict_partner_id': self.owner_id.id,
            'picking_id': self.picking_id.id
        }

    #@api.multi
    def do_scrap(self):
        for scrap in self:
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True)._action_done()
#             move_lines = self.env['stock.move.line'].search([('move_id','=',move.id)])
#             for mv_ln in move_lines:
#                 mv_ln.
            for line in scrap.picking_id.move_ids_without_package:
                line.categ_id = line.product_id.categ_id.id
                line.manufacturer_id = line.product_id.manufacturer_id.id
                if not line.condition_id:
                    line.condition_id = scrap.condition_id.id
            scrap.write({'move_id': move.id, 'state': 'done'})
            scrap.scrap_id.write({'state': 'done'})
        return True
    
    # Filter Product Basis of Product TYpe
    # Filter Product Basis of Product TYpe
    @api.depends('tel_type','manufacturer_id','lot_id')
    @api.onchange('tel_type', 'manufacturer_id','lot_id')
    def onchange_product_type(self):
        if self.tel_type.name == 'ATM':
            lot_id = self.env['stock.move.line'].search([('serial_number', '=', self.lot_id.name)], limit=1)
            self.move_id = lot_id.id
        else:
            self.move_id = ""
        if self.tel_type.name == 'ATM':
                self.ticl_checked = False
                self.count_number = 1
        else:
            self.ticl_checked = True
            self.count_number = ''
        if self.manufacturer_id:
            if self.product_id.manufacturer_id.id != self.manufacturer_id.id:
                self.product_id = False
        
    
    # Filter Product Basis of Product TYpe
    @api.depends('product_id')
    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.xl_items = self.product_id.xl_items
            self.manufacturer_id = self.product_id.manufacturer_id.id or False
            self.tel_type = self.product_id.categ_id.id or False
            res = {}
            condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')], limit=1).id
            #stock_move_ids = self.env['stock.move'].search([('condition_id', '=', condition_id),('product_id', '=',self.product_id.id )])
            stock_move_ids = self.env['stock.move.line'].search([('status', '=', 'inventory'),('condition_id', '=', condition_id),('product_id', '=',self.product_id.id )])
            
            move_names = []
            for move in stock_move_ids:
                if move.serial_number:
                    move_names.append(move.serial_number)
            res['domain']={'lot_id':[
                ('product_id', '=', self.product_id.id),
                ('condition_id','=',condition_id),
                ('receiving_location_id','=',self.location_id.id),
                ('is_scraped','=',False),
                ('name','in',move_names)]}
            return res
    
class StockWarnInsufficientQtyScrap(models.TransientModel):
    _inherit = 'stock.warn.insufficient.qty.scrap'

    def action_done(self):
        return self.scrap_id.scrap_lines.do_scrap()