from odoo import models, fields, api, _
import math
import logging
_logger = logging.getLogger(__name__)

class ticl_monthly_service_line(models.Model):
    _name = 'ticl.monthly.service.line'   
    

    @api.model
    def get_storage_count(self, domain, wh_domain):
        move = self.env['stock.move.line'].sudo()
        dom = [('received_date', '>=', domain[0][2]), ('received_date', '<', domain[1][2])]
        dom += [('status','in',('assigned','picked','packed'))]
        dom += [('xl_items','=','n')]
        dom += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        dom += wh_domain
        non_inv_moves = move.search(dom)

        dom_inv = [('received_date', '<', domain[1][2])]
        dom_inv += [('status','=','inventory')]
        dom_inv += [('xl_items','=','n')]
        dom_inv += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        dom_inv += wh_domain
        inv_moves = move.search(dom_inv)

        dom_shp = [('shipment_date', '>=', domain[0][2]), ('shipment_date', '<', domain[1][2])]
        dom_shp += [('status','=','shipped')]
        dom_shp += [('xl_items','=','n')]
        dom_shp += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        dom_shp += wh_domain
        shipped_moves = move.search(dom_shp)

        dom_str = [('received_date', '<', domain[1][2]), ('shipment_date', '>', domain[1][2])]
        dom_str += [('status','=','shipped')]
        dom_str += [('xl_items','=','n')]
        dom_str += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        dom_str += wh_domain
        storeg_moves = move.search(dom_str)
        _logger.info("moves <%s> to ", storeg_moves)
        _logger.info("rcv date <%s> to ", domain[1][2])
        _logger.info("ship date <%s> to ", domain[1][2])

        moves_unship = non_inv_moves | inv_moves
        ship_unship_moves = moves_unship | shipped_moves
        moves = ship_unship_moves | storeg_moves
        product_ids = moves.mapped('product_id')
        qty = 0
        for pr_id in product_ids:
            product_mn = moves.filtered(lambda x: x.product_id.id == pr_id.id)
            p_count = self.env['ticl.monthly.service.line'].get_pallet_count(pr_id.categ_id.id, pr_id)
            t_qty = len(product_mn)
            ftq = (t_qty/p_count)
            frac, whole = math.modf(ftq)
            qty += whole + 1 if frac > 0 else whole
        return qty
    
    @api.model
    def get_storage_xl_count(self, domain, wh_domain):
        move = self.env['stock.move.line'].sudo()
        d = [('received_date', '>=', domain[0][2]), ('received_date', '<', domain[1][2])]
        d += [('status','in',('assigned','picked','packed'))]
        d += [('xl_items','=','y')]
        d += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        d += wh_domain
        non_inv_moves = move.search_count(d)
        dd = [('received_date', '<', domain[1][2])]
        dd += [('status','=','inventory')]
        dd += [('xl_items','=','y')]
        dd += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        dd += wh_domain
        inv_moves = move.search_count(dd)
        ddd = [('shipment_date', '>=', domain[0][2]), ('shipment_date', '<', domain[1][2])]
        ddd += [('status','=','shipped')]
        ddd += [('xl_items','=','y')]
        ddd += [('condition_id.name','not in',('Quarantine','To Recommend'))]
        ddd += wh_domain
        shipped_moves = move.search_count(ddd)
        qty = non_inv_moves + inv_moves + shipped_moves
       
        return qty
    
    receipt_id = fields.Many2one('ticl.receipt', string='Receipt')
    warehouse_id = fields.Many2one('stock.warehouse',string='Service Location')
    product_id = fields.Many2one('product.product', string='Model Name')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    serial_number = fields.Char(string='Serial #   ')
    quantity = fields.Char(string='Quantity', default=1)
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    service_location = fields.Many2one('res.partner',string='Service Location')
    tel_type = fields.Many2one('product.category', string="Type")
    funding_doc_type = fields.Char(string="Funding Doc Type")
    funding_doc_number = fields.Char(string="Funding Doc Number")
    ticl_project_id = fields.Char(string="Project Id")
    xl_items = fields.Selection(string="XL", selection=[('y', 'Y'), ('n', 'N')])
    repalletize = fields.Selection(string="Repalletize", selection=[('y', 'Y'), ('n', 'N')])
    tel_cod = fields.Selection([('Y', 'Y'), ('N', 'N')], string='COD')
    tid = fields.Char(string="Terminal ID")
    document_date = fields.Datetime(string='Document Date')
    vendor_name = fields.Many2one('res.partner', string="Vendor Name")
    ven_cmp_name = fields.Char(string="Vendor Name")
    vendor_number = fields.Char(string="Vendor Number")
    ticl_ship_id = fields.Many2one('ticl.shipment.log', string='Shipment', readonly=True)
    invoice_number = fields.Many2one('account.move', string='Invoice Number', readonly=True)
    ref_invoice = fields.Char(string="R Invoice")
    formula = fields.Char(string="Formula")
    state = fields.Char(string="State")
    zip = fields.Char(string="Zip")
    vendor_description = fields.Char(string="Vendor Description")
    invoice_type = fields.Char(string="Invoice Type")
    service_date = fields.Datetime(string='Service Date')
    billed_quantity = fields.Integer(string='Billed Quantity', default=1)
    unit_price = fields.Char(string='Unit Charge')
    summary_invoice= fields.Char(string='Summary Invoice')
    payment = fields.Char(string='Payment')
    move_id = fields.Many2one('stock.move', string='Move', readonly=True)
    move_status = fields.Selection(related='move_id.status', store=True)
    active = fields.Boolean(default=True)
    repalletize_charge = fields.Float(string="Repalletize Charge")
    one_charge = fields.Boolean(default=False)
    total_charge = fields.Float(string='Total Charge')
    cost_center = fields.Char(string='Cost center')
    gl = fields.Char(string='General Ledger')
    shipped = fields.Boolean(default=False)
    
    # @api.multi
    def write(self, vals):
        if vals.get('move_status'):
            if vals.get('move_status') != 'inventory':
                vals.update({'active':False})
        return super(ticl_monthly_service_line, self).write(vals)
    
    def get_pallet_count(self, typ, product):
        p_count = 1
        pallet_cong = self.env['pallet.count'].search([('tel_type','=',typ)])
        if pallet_cong:
            pallet_items = pallet_cong.filtered(lambda x: x.product_id.id == product.id)
            if pallet_items:p_count = pallet_items[0].count
            else:
                pallet_items = pallet_cong.filtered(lambda x: not x.product_id)
                if pallet_items: p_count = pallet_items[0].count
        return p_count
        
    
    # @api.multi
    def create_detail_mnth_service_inv(self, obj, typ):
        vals = {}
#         misc_product = self.env.ref('ticl_sale.misc_fees')
#         associated_product = self.env.ref('ticl_sale.associated_fees')
        
        if typ == 'receipt':
            rcv_pl = self.env.ref('ticl_invoice.ticl_receiving_per_pallet')
            product_rcv_pl = self.env['ticl.service.charge'].search([('product_id','=',rcv_pl.id)],limit=1)
            for line in obj.ticl_receipt_lines:
                p_count = self.get_pallet_count(line.tel_type.id,line.product_id)
                ftq = abs(int(line.count_number)/p_count)
                frac, whole = math.modf(ftq)
                qty = whole + 1 if frac > 0 else whole
                vals.update({
                        'vendor_description':line.ticl_receipt_id.name,
                        'receipt_id':line.ticl_receipt_id.id,
                        'warehouse_id':line.ticl_receipt_id.warehouse_id.id,
                        'product_id':line.product_id.id,
                        'manufacturer_id':line.manufacturer_id.id,
                        'serial_number':line.serial_number,
                        'quantity':line.count_number,
                        'condition_id':line.condition_id.id,
                        'service_location':line.ticl_receipt_id.sending_location_id.id,
                        'tel_type':line.tel_type.id,
                        'funding_doc_type':line.funding_doc_type,
                        'funding_doc_number':line.funding_doc_number,
                        'ticl_project_id':line.ticl_project_id,
                        'xl_items':line.xl_items,
                        'repalletize':line.repalletize,
                        'tel_cod':line.tel_cod,
                        'document_date':line.ticl_receipt_id.delivery_date,
                        'ven_cmp_name':self.env.user.company_id.name,
                        'vendor_number':self.env.user.company_id.phone,
                        'invoice_type':rcv_pl.name,
                        'service_date':line.ticl_receipt_id.delivery_date,
                        'billed_quantity':line.count_number,
                        'unit_price':product_rcv_pl.service_price,
                        'state':line.ticl_receipt_id.warehouse_id.state_id.name,
                        'zip':line.ticl_receipt_id.warehouse_id.zip_code,
                        'repalletize_charge':line.repalletize_charge,
                        'total_charge':(product_rcv_pl.service_price * int(line.count_number)),
                        'gl':'7831300021',
                        
                        'cost_center':'285362'
                    })
                if line.tel_type.name not in ('ATM','XL') and line.xl_items == 'n':
                    vals.update({
                        'billed_quantity':1,
                        'total_charge':(product_rcv_pl.service_price * int(1))
                    })
                self.create(vals)
                if line.repalletize == 'y':
                    product = self.env.ref('ticl_invoice.ticl_palletization_per_pallet')
                    product_price = self.env['ticl.service.charge'].search([('product_id','=',product.id)],limit=1)
                    vals.update({'billed_quantity':1,'invoice_type':product.name,'unit_price':product_price.service_price,'total_charge':(product_price.service_price * 1)})
                    self.create(vals)
#                 if line.condition_id.name != 'To Recommend':
#                     prod_per_pallet = self.env.ref('ticl_invoice.ticl_storage_per_pallet')
#                     if line.tel_type.name == 'ATM':
#                         seq = self.env['ir.sequence'].next_by_code('store_sequence')
#                         product_atm = self.env.ref('ticl_invoice.ticl_storage_per_atms')
#                         product_price_atm = self.env['ticl.service.charge'].search([('product_id','=',product_atm.id)],limit=1)
#                         vals.update({
#                             'billed_quantity':qty,
#                             'invoice_type':prod_per_pallet.name,
#                             'unit_price':product_price_atm.service_price,
#                             'vendor_description':'STORE- '+str(seq),
#                             'gl':'7829900000',
#                             'total_charge':(product_price_atm.service_price * int(qty))})
#                         self.create(vals)
#                     elif line.tel_type.name == 'Signage':
#                         seq = self.env['ir.sequence'].next_by_code('store_sequence')
#                         product_sng = self.env.ref('ticl_invoice.ticl_storage_per_signages')
#                         product_price_sng = self.env['ticl.service.charge'].search([('product_id','=',product_sng.id)],limit=1)
#                         vals.update({
#                             'billed_quantity':qty,
#                             'invoice_type':prod_per_pallet.name,
#                             'unit_price':product_price_sng.service_price,
#                             'vendor_description':'STORE- '+str(seq),
#                             'gl':'7829900000',
#                             'total_charge':(product_price_sng.service_price * int(qty))})
#                         self.create(vals)
#                     
#                     elif line.tel_type.name == 'Lockbox':
#                         product_lxb = self.env.ref('ticl_invoice.ticl_storage_per_lockbox')
#                         product_price_lxb = self.env['ticl.service.charge'].search([('product_id','=',product_lxb.id)],limit=1)
#                         vals.update({
#                             'billed_quantity':qty,
#                             'invoice_type':prod_per_pallet.name,
#                             'unit_price':product_price_lxb.service_price,
#                             'vendor_description':'STORE- LOCKBOX',
#                             'gl':'7829900000',
#                             'total_charge':(product_price_lxb.service_price * int(qty))})
#                         self.create(vals)
#                     
#                     elif line.tel_type.name == 'xl':
#                         seq = self.env['ir.sequence'].next_by_code('store_sequence')
#                         product_xl = self.env.ref('ticl_invoice.ticl_storage_per_xl_items')
#                         product_price_xl = self.env['ticl.service.charge'].search([('product_id','=',product_xl.id)],limit=1)
#                         vals.update({
#                             'billed_quantity':line.count_number,
#                             'invoice_type':prod_per_pallet.name,
#                             'unit_price':product_price_xl.service_price,
#                             'vendor_description':'STORE- '+str(seq),
#                             'gl':'7829900000',
#                             'total_charge':(product_price_xl.service_price * int(line.count_number))})
#                         self.create(vals)
#                     
#                     elif line.tel_type.name != 'ATM' and line.xl_items == 'y':
#                         seq = self.env['ir.sequence'].next_by_code('store_sequence')
#                         product_xl = self.env.ref('ticl_invoice.ticl_storage_per_xl_items')
#                         product_price_xl = self.env['ticl.service.charge'].search([('product_id','=',product_xl.id)],limit=1)
#                         vals.update({
#                             'invoice_type':product_xl.name,
#                             'unit_price':product_price_xl.service_price,
#                             'vendor_description':'STORE- '+str(seq),
#                             'gl':'7829900000',
#                             'total_charge':(product_price_xl.service_price * int(line.count_number))
#                         })
#                         self.create(vals)
#                     elif line.tel_type.name == 'Accessory' and line.xl_items == 'n':
#                         prod_assry = self.env.ref('ticl_invoice.ticl_storage_per_accessory')
#                         product_price_assry = self.env['ticl.service.charge'].search([('product_id','=',prod_assry.id)],limit=1)
#                         vals.update({
#                             'invoice_type':prod_per_pallet.name,
#                             'unit_price':product_price_assry.service_price,
#                             'vendor_description':'STORE- '+str(line.product_id.name)+'  (8 per)',
#                             'billed_quantity':qty,
#                             'gl':'7829900000',
#                             'total_charge':(product_price_assry.service_price * int(qty))
#                         })
#                         self.create(vals)
                    
                    
        elif typ == 'destroyed':
            product_cod = self.env.ref('ticl_invoice.ticl_data_sanitization_per_atm')
            product_price_cod = self.env['ticl.service.charge'].search([('product_id','=',product_cod.id)],limit=1)
            vals.update({
                'vendor_description':'COD-'+obj.serial_number,
                'receipt_id':obj.ticl_receipt_summary_id.tel_receipt_log_id.id,
                'warehouse_id':obj.ticl_receipt_summary_id.warehouse_id.id,
                'product_id':obj.product_id.id,
                'manufacturer_id':obj.manufacturer_id.id,
                'serial_number':obj.serial_number,
                'quantity':obj.count_number,
                'condition_id':obj.condition_id.id,
                'service_location':obj.ticl_receipt_summary_id.sending_location_id.id,
                'tel_type':obj.tel_type.id,
                'funding_doc_type':obj.funding_doc_type,
                'funding_doc_number':obj.funding_doc_number,
                'ticl_project_id':obj.ticl_project_id,
                'xl_items':obj.xl_items,
                'repalletize':obj.repalletize,
                'tel_cod':obj.tel_cod,
                'document_date':obj.ticl_receipt_summary_id.delivery_date,
                'ven_cmp_name':self.env.user.company_id.name,
                'vendor_number':self.env.user.company_id.phone,
                'service_date':obj.ticl_receipt_summary_id.delivery_date,
                'billed_quantity':1,
                'unit_price':product_price_cod.service_price,
                'state':obj.ticl_receipt_summary_id.warehouse_id.state_id.name,
                'zip':obj.ticl_receipt_summary_id.warehouse_id.zip_code,
                'invoice_type':product_cod.name,
                'repalletize_charge':obj.repalletize_charge,
                'total_charge':(product_price_cod.service_price * int(1)),
                'gl':'7831300021',
                'cost_center':'285362'
            })
            
            self.create(vals)
                
                
                
        elif typ == 'shipment':
            for line in obj.ticl_ship_lines:
                
                vals.update({
                    'vendor_description':line.ticl_ship_id.name,
                    'warehouse_id':line.ticl_ship_id.warehouse_id.id,
                    'product_id':line.product_id.id,
                    'manufacturer_id':line.manufacturer_id.id,
                    'serial_number':line.lot_id.name if line.lot_id else line.serial_number,
                    'quantity':1,
                    'service_location':line.ticl_ship_id.receiving_location_id.id,
                    'tel_type':line.tel_type.id,
                    'funding_doc_type':line.funding_doc_type,
                    'funding_doc_number':line.funding_doc_number,
                    'ticl_project_id':line.ticl_project_id,
                    'xl_items':line.xl_items,
                    'tid':line.tid,
                    'document_date':line.ticl_ship_id.appointment_date_new,
                    'ven_cmp_name':self.env.user.company_id.name,
                    'vendor_number':self.env.user.company_id.phone,
                    'ticl_ship_id':line.ticl_ship_id.id,
                    'state':line.ticl_ship_id.warehouse_id.state_id.name,
                    'zip':line.ticl_ship_id.warehouse_id.zip_code,
                    'service_date':line.ticl_ship_id.appointment_date_new,
                    'billed_quantity':1,
                    'unit_price':line.service_price
                    
                })
                if line.tel_type.name in ('ATM','Signage','Accessory') and line.xl_items != 'y':
                    out_atm = self.env.ref('ticl_invoice.ticl_outbound_per_atm_pallet')
                    pr_out_atm = self.env['ticl.shipment.charge'].search([('product_id','=',out_atm.id)],limit=1)
                    vals.update({'invoice_type':out_atm.name,'unit_price':pr_out_atm.shipment_service_charges,'total_charge':(pr_out_atm.shipment_service_charges * int(1))})
                    self.create(vals)
                elif line.tel_type.name == 'Lockbox' and line.xl_items != 'y':
                    out_small = self.env.ref('ticl_invoice.ticl_outbound_small_item_non_freight')
                    pr_out_small = self.env['ticl.shipment.charge'].search([('product_id','=',out_small.id)],limit=1)
                    vals.update({'invoice_type':out_small.name,'unit_price':pr_out_small.shipment_service_charges,'total_charge':(pr_out_small.shipment_service_charges * int(1))})
                    self.create(vals)
                elif line.xl_items == 'y' or line.tel_type.name == 'XL':
                    out_xl = self.env.ref('ticl_invoice.ticl_outbound_services_for_xl_items')
                    pr_out_xl = self.env['ticl.shipment.charge'].search([('product_id','=',out_xl.id)],limit=1)
                    vals.update({'invoice_type':out_xl.name,'unit_price':pr_out_xl.shipment_service_charges,'total_charge':(pr_out_xl.shipment_service_charges * int(1))})
                    self.create(vals)
        elif typ == 'misc':
            misc_product = self.env.ref('ticl_invoice.ticl_misc_fees')
            product_misc = self.env['ticl.service.charge'].search([('product_id','=',misc_product.id)],limit=1)
            vals.update({
                    'vendor_description':obj.description,
                    'warehouse_id':obj.warehouse_id.id,
                    'product_id':obj.model_name.id,
                    'serial_number':obj.serial_number,
                    'quantity':obj.work_time,
                    'document_date':obj.document_date,
                    'ven_cmp_name':self.env.user.company_id.name,
                    'vendor_number':self.env.user.company_id.phone,
                    'state':obj.warehouse_id.state_id.name,
                    'zip':obj.warehouse_id.zip_code,
                    'service_date':obj.document_date,
                    'billed_quantity':obj.work_time,
                    'unit_price':product_misc.service_price,
                    'manufacturer_id':obj.model_name.manufacturer_id.id,
                    'invoice_type':misc_product.name,
                    'total_charge':(product_misc.service_price * int(obj.work_time)),
                    'gl':'7831300021',
                    'cost_center':'285362',
                    'tel_type':obj.model_name.categ_id.id,
                    
                })
            self.create(vals)
        
        elif typ == 'inventory':
            pass
#             warehouse = self.env['stock.warehouse'].search([('name','=',obj.location_dest_id.name)],limit=1)
#             vals.update({
#                 'move_id':obj.id,
#                 'warehouse_id':warehouse.id,
#                 'product_id':obj.product_id.id,
#                 'manufacturer_id':obj.manufacturer_id.id,
#                 'serial_number':obj.serial_number,
#                 'quantity':1,
#                 'condition_id':obj.condition_id.id,
#                 'service_location':obj.location_id.id,
#                 'tel_type':obj.categ_id.id,
#                 'xl_items':obj.xl_items,
#                 'billed_quantity':1,
#                 'unit_price':obj.service_price,
#                 'state':warehouse.state_id.name,
#                 'zip':warehouse.zip_code,
#                 'ven_cmp_name':self.env.user.company_id.name,
#                 'vendor_number':self.env.user.company_id.phone,
#                 'service_date':fields.Date.today(),
#                 'document_date':fields.Date.today(),
#             })
#             if obj.categ_id.name == 'ATM':
#                 str_atm = self.env.ref('ticl_sale.storage_per_atm')
#                 pr_str_atm = self.env['ticl.service.charge'].search([('product_id','=',str_atm.id)],limit=1)
#                 vals.update({'invoice_type':str_atm.name,'unit_price':pr_str_atm.service_price})
#                 self.create(vals)
#             elif obj.categ_id.name == 'Signage':
#                 str_sng = self.env.ref('ticl_sale.storage_per_signage')
#                 pr_str_sng = self.env['ticl.service.charge'].search([('product_id','=',str_sng.id)],limit=1)
#                 vals.update({'invoice_type':str_sng.name,'unit_price':pr_str_sng.service_price})
#                 self.create(vals)
#             elif obj.categ_id.name != 'ATM' and obj.xl_items == 'y':
#                 str_xl = self.env.ref('ticl_sale.storage_per_xl_item')
#                 pr_str_xl = self.env['ticl.service.charge'].search([('product_id','=',str_xl.id)],limit=1)
#                 vals.update({'invoice_type':str_xl.name,'unit_price':pr_str_xl.service_price})
#                 self.create(vals)

        
        return True
    
# class WarehouseService(models.Model):
#     _inherit = 'common.misc.line'
    
#     @api.model
#     def create(self, vals):
#         res = super(WarehouseService, self).create(vals)
#         if res:
#             self.env['ticl.monthly.service.line'].create_detail_mnth_service_inv( res, 'misc')
#         return res
    
    
       