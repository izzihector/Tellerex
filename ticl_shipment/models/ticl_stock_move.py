from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    
    shippable = fields.Boolean(string='Shipment Log', help="to identify which moves need to send")
    tel_user_ids = fields.Many2many('res.users', string='Users')
    add_pallet = fields.Char(string='Pallet ID')

    @api.model
    def get_scrapview_action(self, ids):
        view_id = self.env.ref('ticl_shipment.scrap_inventory_entries_form').id
        scrap_lines = []
        moves = self.browse(ids.get('ids'))
        my_list = [str(i) for i in moves.ids]
        ex_selections = self.env['ticl.stock.move.scrap.line.store'].sudo().search(
            [('unique_id','not in',my_list),
             ('is_scrap','=',False)
            ])
        for mv in moves:
            d = {
                'product_id':mv.product_id.id,
                'manufacturer_id':mv.manufacturer_id.id,
                'move_id':mv.id,
                'unique_id':mv.id,
                'tel_type':mv.categ_id.id,
                'origin':mv.origin,
                'scrap_qty':1,
                'tel_note':mv.tel_note,
                'state':mv.status,
                'location_id':mv.location_dest_id.id,
                'user_id':self.env.user.id,
                'condition_id':mv.condition_id.id
            }
            if mv.serial_number:
                lot = self.env['stock.production.lot'].search([('name', '=', mv.serial_number)])
                d.update({'lot_id':lot.id})
            scrap_lines.append((0,0,d))
            self.env['ticl.stock.move.scrap.line.store'].sudo().create(d)
        for ex_selection in ex_selections:
            c = {
                'product_id':ex_selection.product_id.id,
                'manufacturer_id':ex_selection.manufacturer_id.id,
                'tel_type':ex_selection.tel_type.id,
                'origin':ex_selection.origin,
                'scrap_qty':1,
                'tel_note':ex_selection.tel_note,
                'state':ex_selection.state,
                'location_id':ex_selection.location_id.id,
                'user_id':ex_selection.user_id.id,
                'lot_id':ex_selection.lot_id.id,
                'move_id':ex_selection.move_id.id,
                'unique_id':ex_selection.unique_id,
                'condition_id':ex_selection.condition_id.id
            }
            scrap_lines.append((0,0,c))
        return {
            'name':'Scrap Data',
            'type': 'ir.actions.act_window',
            'res_model': 'ticl.stock.move.scrap',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'res_id': False,
            'context': {'default_scrap_lines':scrap_lines},
        }

    @api.model
    def remove_selected_shipment(self, vals):
        move = self.browse(int(vals.get('move_id')))
        print("===move1111=====",move)
        if move: 
            move.write({'shippable':False,'tel_user_ids':[(3, self.env.user.id)]})
    
    @api.model
    def search_select(self, vals):
        move = self.search([('tel_unique_no','=',vals.get('tel_unique_no'))], limit=1)
        print("===move=====",move)
        if move: 
#             move.shippable = vals.get('shippable')
            self._cr.execute('UPDATE stock_move '\
                       'SET shippable=%s '\
                       'WHERE id IN %s', (vals.get('shippable'), tuple(move.ids),))
            if vals.get('shippable'):
                self._cr.execute("""
                    SELECT * from res_users_stock_move_rel where stock_move_id = %s and 
                    res_users_id = %s
                """, (move.id, self.env.user.id))
                record = self._cr.fetchone()
                if not record:
                    self._cr.execute("""
                        INSERT INTO res_users_stock_move_rel(stock_move_id, res_users_id)
                        VALUES (%s, %s)
                    """, (move.id, self.env.user.id))
                
#                 move.write({'shippable':vals.get('shippable'),'tel_user_ids':[(4, self.env.user.id)]})
#                 move.tel_user_ids = [(4, self.env.user.id)]
            else:
                self._cr.execute("""
                    delete from res_users_stock_move_rel where stock_move_id = %s and res_users_id = %s
                """, (move.id, self.env.user.id))
#                 move.write({'shippable':vals.get('shippable'),'tel_user_ids':[(3, self.env.user.id)]})
#                 move.tel_user_ids = [(3, self.env.user.id)]
        return True
    
    @api.model
    def remove_shipment(self):
        moves = self.search([
            ('shippable','=',True),
            ('tel_user_ids','in',self.env.user.ids),
            ('company_id','=',self.env.user.company_id.id),
            ('status','!=','inventory')
            ])
        if moves:
            self._cr.execute('UPDATE stock_move '\
                       'SET shippable=%s '\
                       'WHERE id IN %s', (False, tuple(moves.ids),))
        
    @api.model
    def search_select_preview(self):
        moves = self.search([('shippable','=',True),('tel_user_ids','in',self.env.user.ids),('company_id','=',self.env.user.company_id.id)])
        dicm = []
        for move in moves:
            dicm.append({
                'id':move.id,
                'receipt':move.origin,
                'receipt_date':move.received_date,
                'model':move.product_id.name,
                'manufacturer':move.manufacturer_id.name,
                'serial':move.serial_number if move.serial_number else '',
                'condition':move.condition_id.name,
                'status':move.status,
                'type':move.categ_id.name,
                'xl':move.xl_items if move.xl_items else '',
                'unique_no':move.tel_unique_no
                })
        return dicm