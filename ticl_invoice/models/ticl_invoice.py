from datetime import datetime, timedelta, date
from functools import partial
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from werkzeug.urls import url_encode
from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC
import calendar
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import math

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.move"

    is_service_mf = fields.Boolean(string='Is Service',default=False)

    
    
    # @api.multi
    def unlink(self):
        monthly_invs = self.env['ticl.monthly.service.line'].search([('invoice_number','in',self.ids)])
        if monthly_invs:
            monthly_invs.write({'one_charge':False})
        fright_invs = self.env['ticl.fright.service.line'].search([('invoice_number','in',self.ids)])
        if fright_invs:
            for fright_inv in fright_invs:
                if fright_inv.receipt_id:
                    fright_inv.receipt_id.is_invoice = False
                if fright_inv.ticl_ship_id:
                    fright_inv.ticl_ship_id.is_invoice = False
        return super(AccountInvoice, self).unlink()

    # @api.multi
    def button_cancel(self):
        monthly_invs = self.env['ticl.monthly.service.line'].search([('invoice_number','in',self.ids)])
        if monthly_invs:
            monthly_invs.write({'one_charge':False})
        fright_invs = self.env['ticl.fright.service.line'].search([('invoice_number','in',self.ids)])
        if fright_invs:
            for fright_inv in fright_invs:
                if fright_inv.receipt_id:
                    fright_inv.receipt_id.is_invoice = False
                if fright_inv.ticl_ship_id:
                    fright_inv.ticl_ship_id.is_invoice = False
        return super(AccountInvoice, self).button_cancel()

    # @api.multi
    def button_draft(self):
        monthly_invs = self.env['ticl.monthly.service.line'].search([('invoice_number','in',self.ids)])
        if monthly_invs:
            monthly_invs.write({'one_charge':True})
        fright_invs = self.env['ticl.fright.service.line'].search([('invoice_number','in',self.ids)])
        if fright_invs:
            for fright_inv in fright_invs:
                if fright_inv.receipt_id:
                    fright_inv.receipt_id.is_invoice = True
                if fright_inv.ticl_ship_id:
                    fright_inv.ticl_ship_id.is_invoice = True
        return super(AccountInvoice, self).button_draft()
    
    
    def _prepare_invoice_line_service(self, product, price, key=False, quantity=1,warehouse_id=False):
        journal = self.env['account.move'].with_context(default_type='out_invoice')._get_default_journal()
        account_id = journal.default_debit_account_id.id
        line = {
            
            'display_type': False, 
            'analytic_tag_ids': [[6, False, []]],
            'analytic_account_id': False,
            'disassembly_unit': False,
            'tax_ids': [[6, False, []]],
            'product_uom_id': product.product_tmpl_id.uom_id.id,
            'account_id': account_id,
            'chase_contract_date': False,
            'price_unit': price if price else 0,
            'product_id': product.id,
            'bank_chanrges': 0,
            'is_rounding_line': False,
            'name': product.name,
            'quantity': quantity,
            'discount': 0,
            'tellerex_charges': 0,
            'state_code':key,
            'warehouse_id':warehouse_id,
            
        }
        return [0,0,line]
    
    def create_fright_invoice(self,domain):
        invoices = []
        fright_lines = self.env['ticl.fright.service.line'].search(domain)
        if not fright_lines:
            raise UserError(_('Nothing to Invoice.'))
        if fright_lines:
            rcpt = fright_lines.mapped('receipt_id')
            shps = fright_lines.mapped('ticl_ship_id')
            rcpt.write({'is_invoice':True})
            shps.write({'is_invoice':True})
            state_cost = {}
            prevent_duplicate = []
            for receipt in fright_lines:
                if receipt.receipt_id:
                    if receipt.receipt_id not in prevent_duplicate:
                        if receipt.state not in state_cost.keys():
                            state_cost.update({receipt.state:float(receipt.fright_price)})
                        else:
                            cost = state_cost.get(receipt.state) + float(receipt.fright_price)
                            state_cost.update({receipt.state:cost})
                        prevent_duplicate.append(receipt.receipt_id)
                if receipt.ticl_ship_id:
                    if receipt.ticl_ship_id not in prevent_duplicate:
                        if receipt.state not in state_cost.keys():
                            state_cost.update({receipt.state:float(receipt.fright_price)})
                        else:
                            cost = state_cost.get(receipt.state) + float(receipt.fright_price)
                            state_cost.update({receipt.state:cost})
                        prevent_duplicate.append(receipt.ticl_ship_id)
                    
            
            invoice_line_ids = []
            
            partner_id = self.env['res.partner'].search([('name','ilike','%chase%'),('customer','=',True)], limit=1).id
            vals = { 'partner_id': partner_id,'is_service_mf':True }
            
            if state_cost:
                for key in state_cost.keys():
                    product = self.env.ref('ticl_invoice.ticl_freight_shipment')
                    line = self._prepare_invoice_line_service(product,state_cost.get(key),key)
                    invoice_line_ids.append(line)
                vals.update({'invoice_line_ids':invoice_line_ids})
                inv = self.create(vals)
                fright_lines.write({'invoice_number':inv.id,'ref_invoice':inv.name,'summary_invoice':inv.name})
                invoices.append(inv.id)
        return invoices
    
    def create_monthly_invoice(self, domain):
        invoices = []
        warehouses = self.env['stock.warehouse'].search([])
        _logger.info("warehouses  <%s> to ", warehouses)
        invoice_line_ids = []
        mninv_lines = []
        first_date = domain[0][2]
#         pallet_count = self.env['pallet.count'].search([('name','=','accessory')],limit=1).count
        partner_id = self.env['res.partner'].search([('name','ilike','%chase%'),('customer_rank','>',0)], limit=1).id
        journal = self.env['account.move'].with_context(default_type='out_invoice')._get_default_journal()
        vals = { 
            'partner_id': partner_id ,
            'is_service_mf':True ,
            'type': 'out_invoice',
            'invoice_user_id': 2,
            'currency_id': 2,
            'company_id':1,
            'journal_id': journal.id
            }
        for warehouse in warehouses:
            warehouse_domain = [('ticl_warehouse_id','=',warehouse.id)]
            mnthly_inv_lines = self.env['ticl.monthly.service.line'].search(warehouse_domain+domain+[('one_charge','=',False)])
            
            
            if mnthly_inv_lines:
                misc_obj = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Warehouse Service')
                if misc_obj:
                    misc_product = self.env.ref('ticl_invoice.ticl_misc_fees')
                    product_misc = self.env['ticl.service.charge'].search([('product_id','=',misc_product.id)],limit=1)
                    line = self._prepare_invoice_line_service(misc_product, product_misc.service_price, warehouse.state_id.code, sum([int(x) for x in misc_obj.mapped('quantity')]), warehouse.id)
                    invoice_line_ids.append(line)
                    misc_obj.write({'one_charge':True})
                
                rcv_per_plt = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Receiving per Pallet')
                if rcv_per_plt:
                    qty = abs(sum(rcv_per_plt.mapped('billed_quantity')))
                    product = self.env.ref('ticl_invoice.ticl_receiving_per_pallet')
                    product_price = self.env['ticl.service.charge'].search([('product_id','=',product.id)],limit=1)
                    line = self._prepare_invoice_line_service(product, product_price.service_price, warehouse.state_id.code, qty, warehouse.id)
                    invoice_line_ids.append(line)
                    rcv_per_plt.write({'one_charge':True})
                cod = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Data Sanitization per ATM')
                if cod:
                    qty = abs(sum(cod.mapped('billed_quantity')))
                    cod_product = self.env.ref('ticl_invoice.ticl_data_sanitization_per_atm')
                    product_price = self.env['ticl.service.charge'].search([('product_id','=',cod_product.id)],limit=1)
                    line = self._prepare_invoice_line_service(cod_product, product_price.service_price, warehouse.state_id.code, qty,warehouse.id)
                    invoice_line_ids.append(line)
                    cod.write({'one_charge':True})
                repalletize = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Palletization per Pallet')
                if repalletize:
                    qty = abs(sum(repalletize.mapped('billed_quantity')))
                    repalletize_charge = abs(sum(repalletize.mapped('repalletize_charge')))
                    repalletize_product = self.env.ref('ticl_invoice.ticl_palletization_per_pallet')
                    product_price = self.env['ticl.service.charge'].search([('product_id','=',repalletize_product.id)],limit=1)
                    line = self._prepare_invoice_line_service(repalletize_product, product_price.service_price, warehouse.state_id.code, qty,warehouse.id)
                    invoice_line_ids.append(line)
                    repalletize.write({'one_charge':True})
            
                outbound_atm_pallet = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Outbound per ATM / Pallet')
                if outbound_atm_pallet:
                    qty = abs(sum(outbound_atm_pallet.mapped('billed_quantity')))
                    out_product_atm = self.env.ref('ticl_invoice.ticl_outbound_per_atm_pallet')
                    product_price = self.env['ticl.shipment.charge'].search([('product_id','=',out_product_atm.id)],limit=1)
                    line = self._prepare_invoice_line_service(out_product_atm, product_price.shipment_service_charges, warehouse.state_id.code, qty,warehouse.id)
                    invoice_line_ids.append(line)
                    outbound_atm_pallet.write({'one_charge':True})
                
                small_items_total = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Outbound Small Item (non-freight)')
                if small_items_total:
                    qty = abs(sum(small_items_total.mapped('billed_quantity')))
                    small_product = self.env.ref('ticl_invoice.ticl_outbound_small_item_non_freight')
                    product_price = self.env['ticl.shipment.charge'].search([('product_id','=',small_product.id)],limit=1)
                    line = self._prepare_invoice_line_service(small_product, product_price.shipment_service_charges, warehouse.state_id.code, qty,warehouse.id)
                    invoice_line_ids.append(line)
                
                total_xl_items = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Outbound Services for XL Items')
                if total_xl_items:
                    qty = abs(sum(total_xl_items.mapped('billed_quantity')))
                    xl_product = self.env.ref('ticl_invoice.ticl_outbound_services_for_xl_items')
                    product_price = self.env['ticl.shipment.charge'].search([('product_id','=',xl_product.id)],limit=1)
                    line = self._prepare_invoice_line_service(xl_product, product_price.shipment_service_charges, warehouse.state_id.code, qty,warehouse.id)
                    invoice_line_ids.append(line)
                    total_xl_items.write({'one_charge':True})
                
                total_ship_signage = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Outbound Services per Signage Piece')
                if total_ship_signage:
                    qty = abs(sum(total_ship_signage.mapped('billed_quantity')))
                    signage_product = self.env.ref('ticl_invoice.ticl_outbound_services_per_signage_piece')
                    product_price = self.env['ticl.shipment.charge'].search([('product_id','=',signage_product.id)],limit=1)
                    line = self._prepare_invoice_line_service(signage_product, product_price.shipment_service_charges, warehouse.state_id.code, qty,warehouse.id)
                    invoice_line_ids.append(line)
                    total_ship_signage.write({'one_charge':True})

                mninv_lines = mninv_lines + mnthly_inv_lines.ids
            
            store_mnthly_inv_lines = self.env['ticl.monthly.service.line']
#                 store_pr_pallet = mnthly_inv_lines.filtered(lambda x: x.invoice_type == 'Storage per Pallet')
            storage_count = 0
            # if store_mnthly_inv_lines:
            storage_count = store_mnthly_inv_lines.get_storage_count(domain,warehouse_domain)
                
                
            if storage_count > 0:
                str_pallet_product = self.env.ref('ticl_invoice.ticl_storage_per_pallet')
                product_price = self.env['ticl.service.charge'].search([('product_id','=',str_pallet_product.id)],limit=1)
                line = self._prepare_invoice_line_service(str_pallet_product, product_price.service_price, warehouse.state_id.code, storage_count,warehouse.id)
                invoice_line_ids.append(line)
                
            # store_mnthly_xl_inv_lines = self.env['ticl.monthly.service.line']
            xl_storage_count = 0
            # if store_mnthly_xl_inv_lines:
            xl_storage_count = store_mnthly_inv_lines.get_storage_xl_count(domain,warehouse_domain)
                   
            if xl_storage_count > 0:
                stroe_xl_product = self.env.ref('ticl_invoice.ticl_storage_per_xl_items')
                product_price = self.env['ticl.service.charge'].search([('product_id','=',stroe_xl_product.id)],limit=1)
                line = self._prepare_invoice_line_service(stroe_xl_product, product_price.service_price, warehouse.state_id.code, xl_storage_count,warehouse.id)
                invoice_line_ids.append(line)

                
        
        if invoice_line_ids:
            vals.update({'invoice_line_ids':invoice_line_ids})
            inv = self.create(vals)
            mnthly_in_lines = self.env['ticl.monthly.service.line'].browse(mninv_lines)
            mnthly_in_lines.write({'invoice_number':inv.id,'ref_invoice':inv.name,'summary_invoice':inv.name})
            invoices.append(inv.id)
        return invoices
    
    
    # @api.multi
    def monthly_fright_invoice(self, vals):
        invoices = []
        mnth_yr_lst = vals.get('month').split('-')
        month = int(mnth_yr_lst[0])
        year = int(mnth_yr_lst[1])
        month_last = date(year, month, calendar.monthrange(year,month)[-1])
        month_first = date(year,month, 1)
        month_mid = date(year,month, 16)
        
        last_date_str = month_last.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        last_day_mth = datetime.strptime(last_date_str, DEFAULT_SERVER_DATETIME_FORMAT)
        last_day_month = last_day_mth + timedelta(days=1)
        
        mid_day_str = month_mid.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        mid_day_mnth = datetime.strptime(mid_day_str, DEFAULT_SERVER_DATETIME_FORMAT)
        
        first_day_str = month_first.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        fir_day_mnth = datetime.strptime(first_day_str, DEFAULT_SERVER_DATETIME_FORMAT)
        first_day_mnth = fir_day_mnth# - timedelta(days=1)
        
        if vals.get('type') == 'fright':
            domain = ['|',('invoice_number','=',False),('invoice_status','=','cancel')]
            invoices = self.create_fright_invoice(domain)
        
        if vals.get('type') == 'monthly':
            if date.today().day != 11:
#             if date.today().day == calendar.monthrange(date.today().year, date.today().month)[-1]:
                
                r_domain = [
                    ('document_date','>=',first_day_mnth.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                    ('document_date','<',last_day_month.strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
                
                invoices = self.create_monthly_invoice(r_domain)
            else:
                raise UserError(_('Fright Invoice generate only Last day and 15th of the month.'))
        
        if invoices:
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            action['domain'] = [('id', 'in', invoices)]
        else:
            action = True
        return action