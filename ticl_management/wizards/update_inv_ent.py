# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import Warning

class AccountAgedTrialBalance(models.TransientModel):
    _name = 'stock.move.update'

    
    old_serial = fields.Char(string = "Old Serial")
    new_serial = fields.Char(string = "New Serial")
    
    
    def inh_update(self):
        if self.new_serial:
            if_lot = self.env['stock.production.lot'].search([('name','=',self.new_serial)])
            mid = self._context.get('active_id')
            move = self.env['stock.move'].browse(mid)
            if move.manufacturer_id.name == 'NCR':
                if len(self.new_serial) != 8:
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view or False
                    context = dict(self._context or {})
                    context['message'] = "Serial Number length for NCR is 8."
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
            elif move.manufacturer_id.name in ["Nautilus Hyosung", "Wincor"]:
                if len(self.new_serial) != 10:
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view or False
                    context = dict(self._context or {})
                    m = "Serial Number length for %s is 10." % move.manufacturer_id.name
                    context['message'] = m
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
            elif move.manufacturer_id.name == "Diebold":
                if len(self.new_serial) != 12:
                    view = self.env.ref('sh_message.sh_message_wizard')
                    view_id = view or False
                    context = dict(self._context or {})
                    context['message'] = "Serial Number length for Diebold is 12."
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
            else:
                pass
            tables = [
                {'stock_move':'serial_number'},
                {'stock_production_lot':'name'},
                {'ticl_receipt_log_summary_line':'serial_number'}]
            for table in tables:
                k = [*table.keys()]
                v = [*table.values()]
                query = 'UPDATE '+ str(k[0]) +' SET '+ str(v[0])+ '= %s WHERE '+str(v[0])+' = %s'
                if k[0] == 'stock_move':
                    query += ' and id = %s'
                    self._cr.execute(query, (self.new_serial, self.old_serial,int(mid),))
                elif k[0] == 'stock_production_lot':
                    if not if_lot:
                        self._cr.execute(query, (self.new_serial, self.old_serial,))
                else:
                    self._cr.execute(query, (self.new_serial, self.old_serial,))
        return  True
    
    
