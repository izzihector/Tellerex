# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockMoveModelUpdate(models.TransientModel):
    _name = 'stock.move.model.update'

    def _product_filter(self):
        mid = self._context.get('active_id')
        move = self.env['stock.move'].browse(mid)
        if move.categ_id.name == 'ATM':
            return [('categ_id', '=', 'ATM'),('type', '=', 'product'),('manufacturer_id', '=', move.manufacturer_id.id)]
        elif move.categ_id.name == 'Signage':
            return [('categ_id', '=', 'Signage'),('type', '=', 'product'),('manufacturer_id', '=', move.manufacturer_id.id)]
        elif move.categ_id.name == 'Accessory':
            return [('categ_id', '=', 'Accessory'),('type', '=', 'product'),('manufacturer_id', '=', move.manufacturer_id.id)]
        elif move.categ_id.name == 'XL':
            return [('categ_id', '=', 'XL'),('type', '=', 'product'),('manufacturer_id', '=', move.manufacturer_id.id)]
        else:
            move.categ_id.name == 'Lockbox'
            return [('categ_id', '=', 'Lockbox'),('type', '=', 'product'),('manufacturer_id', '=', move.manufacturer_id.id)]

    
    old_model = fields.Many2one('product.product', string="Old Model")
    new_model = fields.Many2one('product.product', string="New Model", domain=_product_filter)

    
    def inh_update_model(self):
        if not self.new_model:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Please Select Model Number from the Dropdown List!"
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
        if self.new_model:      
            mid = self._context.get('active_id')
            move = self.env['stock.move'].browse(mid)
            lot = self.env['stock.production.lot'].search([('name','=',move.serial_number)])
            
            if move.status not in ['inventory']:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view or False
                context = dict(self._context or {})
                context['message'] = "Only Inventory Status item(s) can be updated!"
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

            if move.location_dest_id.name == "Chase Las Vegas":
                loc =self.env['stock.location'].search([('barcode', '=', 'USCLV-STOCK'),('name', '=', 'Stock')])
            elif move.location_dest_id.name == "Chase Atlanta":
                loc =self.env['stock.location'].search([('barcode', '=', 'USCHA-STOCK'),('name', '=', 'Stock')])
            elif move.location_dest_id.name == "Chase Chicago - OLD":
                loc =self.env['stock.location'].search([('barcode', '=', 'USCHC-STOCK'),('name', '=', 'Stock')])
            elif move.location_dest_id.name == "Chase Chicago":
                loc =self.env['stock.location'].search([('barcode', '=', 'LUCAS-STOCK'),('name', '=', 'Stock')])
            elif move.location_dest_id.name == "Chase Allentown":
                loc =self.env['stock.location'].search([('barcode', '=', 'USCAL-STOCK'),('name', '=', 'Stock')])
            elif move.location_dest_id.name == "Chase Dallas":
                loc =self.env['stock.location'].search([('barcode', '=', 'USCHD-STOCK'),('name', '=', 'Stock')])
            elif move.location_dest_id.name == "Chase Newark":
                loc =self.env['stock.location'].search([('barcode', '=', 'CHNEW-STOCK'),('name', '=', 'Stock')])
            else:
                move.location_dest_id.name == "Atlanta Overflow"
                loc =self.env['stock.location'].search([('barcode', '=', 'ATLAN-STOCK'),('name', '=', 'Stock')])
                        
                
            tables = [
                {'stock_move':'product_id'},
                {'stock_production_lot': 'product_id'},
                {'ticl_receipt_log_summary_line':'product_id'},
                {'stock_quant':['product_id', 'quantity', 'location_id','reserved_quantity']},
                {'ticl_monthly_service_line': 'product_id'}]


            for table in tables:
                k = [*table.keys()]
                v = [*table.values()]

                query = 'UPDATE '+ str(k[0]) +' SET '+ str(v[0])+ '= %s WHERE '+str(v[0])+' = %s'
                if k[0] == 'stock_production_lot' and move.serial_number:
                    query += ' and '+'name'+' = %s'
                    self._cr.execute(query, (self.new_model.id, self.old_model.id, move.serial_number))                

                elif k[0] == 'stock_production_lot' and not move.serial_number:
                    pass

                elif k[0] == 'ticl_monthly_service_line' and move.serial_number:
                    query += ' and '+'serial_number'+' = %s'
                    self._cr.execute(query, (self.new_model.id, self.old_model.id, move.serial_number)) 

                elif k[0] == 'ticl_monthly_service_line' and not move.serial_number:
                    pass

                elif k[0] == 'stock_quant' and lot:
                    query_stock_lot = 'UPDATE '+ str(k[0]) +' SET '+ str(v[0][0])+ '= %s WHERE '+str(v[0][0])+' = %s'
                    query_stock_lot += ' and '+'lot_id'+' = %s'
                    self._cr.execute(query_stock_lot, (self.new_model.id, self.old_model.id, lot.id))


                elif k[0] == 'stock_quant' and not lot:
                    query_stock = 'UPDATE '+ str(k[0]) +' SET '+ str(v[0][1])+ '= %s WHERE '+str(v[0][0])+' = %s'
                    query_stock += ' and '+'id'+' = %s'
                    sq = self.env['stock.quant'].search([('location_id', '=', loc.id),('product_id', '=', self.old_model.id)],limit=1)
                    sq_new = self.env['stock.quant'].search([('location_id', '=', loc.id),('product_id', '=', self.new_model.id)],limit=1)
                    if not sq_new:
                        lx = 1
                    else:
                        lx = int(sq_new.quantity) + 1
                    if sq:
                        kx = int(sq.quantity) - 1
                        self._cr.execute(query_stock, (kx, self.old_model.id, sq.id))
                        if sq_new:
                            self._cr.execute(query_stock, (lx, self.new_model.id, sq_new.id))
                        else:
                            raw_sql = 'INSERT INTO '+  str(k[0]) +  ' ('+ (str(v[0][0])+ ', '+ str(v[0][1])+ ', '+str(v[0][2])+ ', '+str(v[0][3]))+ ') VALUES ' +  str((self.new_model.id, lx, loc.id, 0))+';'
                            self._cr.execute(raw_sql)
                    else:
                        pass

                else:
                    query += ' and '+'tel_unique_no'+' = %s'
                    self._cr.execute(query, (self.new_model.id, self.old_model.id, move.tel_unique_no))

        return  True
    
    
