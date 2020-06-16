from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    
    shippable = fields.Boolean(string='Shipment Log', help="to identify which moves need to send")
    tel_user_ids = fields.Many2many('res.users', string='Users')
    add_pallet = fields.Char(string='Pallet ID')

    #override Function for move
    def _action_confirm(self, merge=True, merge_into=False):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        :param: merge: According to this boolean, a newly confirmed move will be merged
        in another move of the same picking sharing its characteristics.
        """
        move_create_proc = self.env['stock.move']
        move_to_confirm = self.env['stock.move']
        move_waiting = self.env['stock.move']

        to_assign = {}
        for move in self:
            # if the move is preceeded, then it's waiting (if preceeding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting |= move
            else:
                if move.procure_method == 'make_to_order':
                    move_create_proc |= move
                else:
                    move_to_confirm |= move
            if move._should_be_assigned():
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                if key not in to_assign:
                    to_assign[key] = self.env['stock.move']
                to_assign[key] |= move

        # create procurements for make to order moves
        for move in move_create_proc:
            values = move._prepare_procurement_values()
            origin = (move.group_id and move.group_id.name or (move.origin or move.picking_id.name or "/"))
            self.env['procurement.group'].run(move.product_id, move.product_uom_qty, move.product_uom, move.location_id, move.rule_id and move.rule_id.name or "/", origin,
                                              values)

        move_to_confirm.write({'state': 'confirmed'})
        (move_waiting | move_create_proc).write({'state': 'waiting'})

        # assign picking in batch for all confirmed move that share the same details
        for moves in to_assign.values():
            moves._assign_picking()
        self._push_apply()
        if merge and self._context.get('merge'):
            return self._merge_moves(merge_into=merge_into)
        return self

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