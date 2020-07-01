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

    def get_scrap_data(self,scrap_id):
        return [{"lines":len(self.scrap_lines.ids),"created_date":self.date_expected_new.strftime("%m-%d-%Y"),
        'name':self.name,'email':self.env.user.company_id.email,'phone':self.env.user.company_id.phone,
                 'website':self.env.user.company_id.website}]

    def get_current_url(self):
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        return [{'url': url + '/ticl_scrap_management/static/img/0001.jpg'}]

    tot_count = []
    def get_scrap_line_data(self, scrap_id):
        count_lines = len(self.scrap_lines.ids)
        lines = []
        index = 1
        scrap_lines = self.env['stock.scrap.line'].search([('id', 'in', self.scrap_lines.ids)], order='id desc')
        for ids in scrap_lines:
            move = self.env['stock.move.line'].search([('scrap_line_id', '=', ids.id)], order='id desc')
            for mvs in move:
                if index < 19:
                    lines.append({'no': index, 'manufacturer': ids.manufacturer_id.name,
                                  'description': ids.tel_type.name,
                                  'work_order_no': self.name,
                                  'part_no': ids.product_id.name,
                                  'serial_number': ids.lot_id.name,
                                  'tel_id_no': mvs.tel_unique_no})
                    index = index + 1
        return lines

    def get_scrap_line_data_2(self,scrap_id):
        count_lines = len(self.scrap_lines.ids)
        lines = []
        count=[]
        index=0
        scrap_lines = self.env['stock.scrap.line'].search([('id','in',self.scrap_lines.ids)],order='id desc')
        for sc_l in scrap_lines:
            count.append(sc_l.scrap_qty)
        if sum(count) <=18:
            return [{'no':'False'}]
        for ids in scrap_lines:
            move = self.env['stock.move.line'].search([('scrap_line_id','=',ids.id)],order='id desc')
            for mvs in move:
                if index <= 18:
                    index=index+1
                if index > 18 and index <= 44:
                    lines.append({'no':index,'manufacturer':ids.manufacturer_id.name,
                            'description':ids.tel_type.name,
                            'work_order_no': self.name,
                            'part_no':ids.product_id.name,
                            'serial_number':ids.lot_id.name,
                            'tel_id_no':mvs.tel_unique_no})
                    index=index+1

        return lines


    def get_scrap_line_data_3(self,scrap_id):
        count_lines = len(self.scrap_lines.ids)
        lines = []
        count=[]
        index=0
        scrap_lines = self.env['stock.scrap.line'].search([('id','in',self.scrap_lines.ids)],order='id desc')
        for sc_l in scrap_lines:
            count.append(sc_l.scrap_qty)
        if sum(count) <=18:
            return [{'no':'False'}]
        for ids in scrap_lines:
            move = self.env['stock.move.line'].search([('scrap_line_id','=',ids.id)],order='id desc')
            for mvs in move:
                if index <= 44:
                    index=index+1
                if index >= 45 and index <= 69:
                    lines.append({'no':index,'manufacturer':ids.manufacturer_id.name,
                            'description':ids.tel_type.name,
                            'work_order_no': self.name,
                            'part_no':ids.product_id.name,
                            'serial_number':ids.lot_id.name,
                            'tel_id_no':mvs.tel_unique_no})
                    index=index+1
        return lines
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
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')], string='Status',
                             default="draft", track_visibility='onchange')

    def update_rec_inv(self):
        sc = []
        scraps = self.env['stock.scrap'].search([])
        mv = self.env['stock.move.line'].search([('status', '=', 'recycled'), ('scrap_line_id', '!=', False)])
        for line_ids in mv:
            sc.append(line_ids.scrap_line_id.id)
        for scrap_id in scraps:
            for ids in scrap_id.scrap_lines:
                if ids.id not in sc:
                    move = self.env['stock.move.line'].search(
                        [('product_id', '=', ids.product_id.id), ('condition_id', '!=', False),
                         ('order_from_receipt', '!=', False), ('tel_unique_no', '!=', False),
                         ('status', '=', 'recycled'), ('scrap_line_id', '=', False)], limit=1)
                    if move.categ_id.name == 'ATM':
                        if ids.lot_id.name == move.serial_number:
                            move.write({'scrap_line_id': ids.id})
                    else:
                        move.write({'scrap_line_id': ids.id})


    def download_recycle_report(self):
        report = {
            'type': 'ir.actions.report',
            'report_name': 'ticl_scrap_management.generate_recycle_report',
            'report_type': 'qweb-pdf',
            'report_file': 'ticl_scrap_management.generate_recycle_report',
            'name': 'stock.scrap',
        }
        return report

    def revert_scrap(self):
        self.state = 'draft'
        for ids in self.scrap_lines:
            condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
            if ids.lot_id.name:
                ids.move_line_id.write({'status': 'assigned'})
            else:
                x = self.env['stock.move.line'].search(
                    [('product_id', '=', ids.product_id.id),
                     ('status', '=', 'inventory'),
                     ('condition_id', '=', condition_id.id)])
                self.env['stock.move.line'].search([('id','=',x.ids[0])]).write({'status': 'assigned'})

    @api.model
    def create(self, vals):
        exist_serial_no = []
        if vals.get('scrap_lines', False):
            for lines in range(len(vals['scrap_lines'])):
                print("lem\n \n", range(len(vals['scrap_lines'])))
                type_id = self.env['product.category'].search([('id', '=', vals['scrap_lines'][lines][2]['tel_type'])])

                condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
                if type_id.name != "ATM":
                    if vals['scrap_lines'][lines][2].get('move_line_id', False):

                        x = self.env['stock.move.line'].search(
                            [('id', '=', vals['scrap_lines'][lines][2]['move_line_id'])], limit=1)
                    else:
                        x = self.env['stock.move.line'].search(
                            [('product_id', '=', vals['scrap_lines'][lines][2]['product_id']),
                             ('ticl_warehouse_id', '=', vals['location_id']),
                             ('status', '=', 'inventory'),
                             ('condition_id', '=', condition_id.id)], limit=1)
                    vals['scrap_lines'][lines][2]['move_line_id'] = x.id
                    vals['scrap_lines'][lines][2]['state'] = 'draft'
                    self.env['stock.move.line'].search(
                        [('id', '=', x.id)]).write({'status': 'assigned'})
                else:
                    print("inside ATM")
                    exist_serial_no.append(vals['scrap_lines'][lines][2]['lot_id'])
                    if 'move_line_id' in vals['scrap_lines'][lines][2]:
                        x = self.env['stock.move.line'].search([('id', '=', vals['scrap_lines'][lines][2]['move_line_id'])])

                    else:
                        x = self.env['stock.move.line'].search(
                            [('product_id', '=', vals['scrap_lines'][lines][2]['product_id']),
                             ('ticl_warehouse_id', '=', vals['location_id']),
                             ('status', '=', 'inventory'),
                             ('condition_id', '=', condition_id.id)], limit=1)
                    vals['scrap_lines'][lines][2]['move_line_id'] = x.id
                    vals['scrap_lines'][lines][2]['state'] = 'draft'
                    self.env['stock.move.line'].search([('id', '=', x.id)]).write({'status': 'assigned'})
            for line in vals.get('scrap_lines'):
                product_id = line[2].get('product_id')
                product = self.env['product.product'].browse(product_id)
                uom = product.product_tmpl_id.uom_id
                line[2].update({'product_uom_id': uom.id})
                vals.update({'product_id': product_id, 'product_uom_id': uom.id})
            if exist_serial_no:
                dup_ser = list(set([x for x in exist_serial_no if exist_serial_no.count(x) > 1]))
                if dup_ser:
                    raise UserError("Duplicate Serial Numbers not allowed")
            return super(ticl_scrap_stock, self).create(vals)

        else:
            try:
                return super(ticl_scrap_stock, self).create(vals)

            except:
                raise UserError(_("No Scrap Items"))

    def write(self, vals):
        if vals.get('scrap_lines', False):
            for lines in range(len(vals['scrap_lines'])):

                if vals['scrap_lines'][lines][2] != False and isinstance(vals['scrap_lines'][lines][1], int) == False:
                    type_id = self.env['product.category'].search(
                        [('id', '=', vals['scrap_lines'][lines][2]['tel_type'])])
                    condition_id = self.env['ticl.condition'].search([('name', '=', 'To Recommend')])
                    if type_id.name != "ATM":
                        if vals['scrap_lines'][lines][2].get('move_line_id', False):
                            x = self.env['stock.move.line'].search(
                                [('id', '=', vals['scrap_lines'][lines][2]['move_line_id'])], limit=1)
                        else:
                            x = self.env['stock.move.line'].search(
                                [('product_id', '=', vals['scrap_lines'][lines][2]['product_id']),
                                 ('ticl_warehouse_id', '=', self.location_id.id),
                                 ('status', '=', 'inventory'),
                                 ('condition_id', '=', condition_id.id)], limit=1)

                        vals['scrap_lines'][lines][2]['move_line_id'] = x.id
                        vals['scrap_lines'][lines][2]['state'] = 'draft'
                        self.env['stock.move.line'].search(
                            [('id', '=', x.id)]).write({'status': 'assigned'})

                    else:
                        if 'move_line_id' in vals['scrap_lines'][lines][2]:
                            x = self.env['stock.move.line'].search([('id', '=', vals['scrap_lines'][lines][2]['move_line_id'])])
                        else:
                            x = self.env['stock.move.line'].search(
                                [('product_id', '=', vals['scrap_lines'][lines][2]['product_id']),
                                 ('ticl_warehouse_id', '=', self.location_id.id),
                                 ('status', '=', 'inventory'),
                                 ('condition_id', '=', condition_id.id)], limit=1)

                        vals['scrap_lines'][lines][2]['move_line_id'] = x.id
                        vals['scrap_lines'][lines][2]['state'] = 'draft'
                        self.env['stock.move.line'].search(
                            [('id', '=', x.id)]).write({'status': 'assigned'})

        return super(ticl_scrap_stock, self).write(vals)

    def action_validates(self, lines):
        for scrap_line in lines:
            if scrap_line[0].lot_id:
                scrap_line[0].lot_id.is_scraped = True
            stock_mv = self.env['stock.move.line'].search([('tel_cod', 'in', ('N', False)),
                                                      ('serial_number', '=', scrap_line[0].lot_id.name)], limit=1)
            if stock_mv:
                if not scrap_line[0].scrap_tel_note:
                    raise UserError(_(
                        "Comments/Note is mandatory for the items in which COD's is 'NO'. Please check the Model %s! " % (
                            scrap_line[0].product_id.name)))
                    
            mv = self.env['stock.move.line'].search(scrap_line[1],
                                                       limit=int(scrap_line[0].scrap_qty))
            for mv in mv:
                mv.sudo().write({'status': 'recycled', 'recycled_date': scrap_line[0].date_expected_new,
                                 'scrap_tel_note': scrap_line[0].scrap_tel_note,
                                 'scrap_line_id': scrap_line[0].id})


    
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
                      ('status', 'in', ('inventory', 'assigned')),
                      ('ticl_warehouse_id', '=', scrap_line.location_id.id)]
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


    def unlink(self):
        for ids in self:
            self.env['stock.move.line'].search([('id', '=', ids.move_line_id.id)]).write(
                {'status': 'inventory'})
        return super(ticl_scrap_stock_line, self).unlink()
    
    
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
            scrap_name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            scrap.scrap_id.write({'state': 'done','name':scrap_name})
        return True
    
    # Filter Product Basis of Product TYpe
    # Filter Product Basis of Product TYpe
    @api.depends('tel_type','manufacturer_id','lot_id')
    @api.onchange('tel_type', 'manufacturer_id','lot_id')
    def onchange_product_type(self):
        if self.tel_type.name == 'ATM':
            lot_id = self.env['stock.move.line'].search([('serial_number', '=', self.lot_id.name)], limit=1)
            self.move_line_id = lot_id.id
        else:
            self.move_line_id = ""
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


class TiclStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    scrap_line_id = fields.Many2one('stock.scrap.line', string="Scrap Line ID")
    def write(self, values):
        for i in self:
            if 'scrap_tel_note' in values.keys():
                if self.scrap_line_id:
                    self.scrap_line_id.write({'scrap_tel_note': values['scrap_tel_note']})
        return super(TiclStockMoveLine, self).write(values)