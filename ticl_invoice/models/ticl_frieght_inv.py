from odoo import models, fields, api, _

class ticl_fright_service_line(models.Model):
    _name = 'ticl.fright.service.line'
    
    
    receipt_id = fields.Many2one('ticl.receipt.log.summary', string='Receiving Log Summary')
    ticl_ship_id = fields.Many2one('ticl.shipment.log', string='Shipment ID', readonly=True)
    funding_doc_type = fields.Char(string="Funding Doc Type")
    funding_doc_number = fields.Char(string="Funding Doc Number")
    ticl_project_id = fields.Char(string="Project Id")
    tid = fields.Char(string="Terminal ID")
    document_date = fields.Datetime(string='Document Date')
    vendor_name = fields.Many2one('res.partner', string="Vendor Name")
    vendor_number = fields.Char(string="Vendor Number")
    invoice_number = fields.Many2one('account.move', string='Invoice Number', readonly=True,ondelete='set null')
    state = fields.Char(string="State")
    zip = fields.Char(string="Zip")
    vendor_description = fields.Char(string="Vendor Description")
    invoice_type = fields.Char(string="Invoice Type")
    unit_price = fields.Char(string='Unit Price')
    fright_price = fields.Char(string='Fright Price')
    approved_by = fields.Many2one('res.users', string="Approved By")
    approved_date = fields.Datetime(string='Approved Date')
    ven_cmp_name = fields.Char(string="Vendor Name")
    summary_invoice= fields.Char(string='Summary Invoice')
    invoice_status = fields.Selection(related='invoice_number.state', store=True,string='Invoice Status')
    approval_authority = fields.Char(string='Approval Authority')
    cost_center = fields.Char(string='Cost center')
    gl = fields.Char(string='General Ledger')
    
    
    # @api.multi
    def create_detail_mnth_fright_inv(self, obj, typ):
        if typ == 'receipt':
            for line in obj.ticl_receipt_summary_lines:
                ven_dsc = 'Work Order '+line.ticl_receipt_summary_id.name+','+ line.ticl_receipt_summary_id.total_weight +' pounds,'+ str(line.ticl_receipt_summary_id.miles) +' miles'
                self.create({
                    'receipt_id':line.ticl_receipt_summary_id.id,
                    'funding_doc_type':line.funding_doc_type,
                    'funding_doc_number':line.funding_doc_number,
                    'ticl_project_id':line.ticl_project_id,
                    'document_date':line.ticl_receipt_summary_id.validate_date,
                    'state':line.ticl_receipt_summary_id.warehouse_id.state_id.code,
                    'zip':line.ticl_receipt_summary_id.warehouse_id.zip_code,
                    'invoice_type':line.ticl_receipt_summary_id.receipt_type,
                    'unit_price':line.ticl_receipt_summary_id.chase_fright_cost,
                    'fright_price':line.ticl_receipt_summary_id.chase_fright_cost,
                    'vendor_description':ven_dsc,
                    'ven_cmp_name':self.env.user.company_id.name,
                    'vendor_number':self.env.user.company_id.phone,
                    'approved_by':self.env.user.id,
                    'approved_date':fields.Datetime.now(),
                    'approval_authority':line.ticl_receipt_summary_id.approval_authority,
                    'cost_center':'285362',
                    'gl':'7831300021'
                })
                
        if typ == 'shipment':
            for line in obj.ticl_ship_lines:
                ven_dsc = 'Work Order '+line.ticl_ship_id.name+','+ line.ticl_ship_id.total_weight +' pounds,'+ str(line.ticl_ship_id.miles) +' miles'
                self.create({
                    'ticl_ship_id':line.ticl_ship_id.id,
                    'funding_doc_type':line.funding_doc_type,
                    'funding_doc_number':line.funding_doc_number,
                    'ticl_project_id':line.ticl_project_id,
                    'document_date':line.ticl_ship_id.validate_date,
                    'state':line.ticl_ship_id.warehouse_id.state_id.code,
                    'zip':line.ticl_ship_id.warehouse_id.zip_code,
                    'invoice_type':line.ticl_ship_id.shipment_type,
                    'unit_price':line.ticl_ship_id.chase_fright_cost,
                    'fright_price':line.ticl_ship_id.chase_fright_cost,
                    'vendor_description':ven_dsc,
                    'ven_cmp_name':self.env.user.company_id.name,
                    'vendor_number':self.env.user.company_id.phone,
                    'approved_by':self.env.user.id,
                    'approved_date':fields.Datetime.now(),
                    'approval_authority':line.ticl_ship_id.approval_authority
                })
        return True
                    