
from odoo import api,models, _, fields
import xlwt
from xlwt import easyxf
import io
import base64
import logging
_logger = logging.getLogger(__name__)

class StockWarehouseEmail(models.Model):
	_name = 'warehouse.email'
	
	name = fields.Char(string="Email Address", copy=False)

class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'
 	
	ticl_email_ids = fields.Many2many('warehouse.email', 'stock_warehouse_email_rel', 'warehouse_id', 'email_id', string="Emails", copy=False)

# class TiclShipmentCancel(models.TransientModel):
# 	_inherit = 'ticl.shipment.cancel'

    # @api.multi
    # def confirm_cancel(self):
    #     res = super(TiclShipmentCancel, self).confirm_cancel()
    #     shipment_ids = self._context.get('active_ids')
    #     shipment = self.env['ticl.shipment.log'].browse(shipment_ids)
    #     shipment.sudo().is_notified = False
    #     return res

class TiclShipmentCancel(models.TransientModel):
    _inherit = 'ticl.shipment.cancel'

    #@api.model
    def confirm_cancel(self):
        res = super(TiclShipmentCancel, self).confirm_cancel()
        shipment_ids = self._context.get('active_ids')
        shipment = self.env['ticl.shipment.log'].browse(shipment_ids)
        shipment_line = self.env['ticl.shipment.log.line'].search([('ticl_ship_id','in',shipment.ids),('stand_attached','=',True)])
        shipment.sudo().is_notified = False
        for line in shipment_line:
            line.unlink()
        return res




class ShipmentNotification(models.Model):
    _inherit = 'ticl.shipment.log'

    is_notified = fields.Boolean(default=False, copy=False)

    @api.model
    def warehouse_pending_shipment_notification(self, ids):

        message = 'Unable to send notification. Please select correct shipment'
        msg = ''
        status = 'f'
        column_heading_style = easyxf(
            'font:bold True;pattern: pattern solid, fore_colour ice_blue ;align: horiz left')
        column_heading_style2 = easyxf(
            'font:bold True;pattern: pattern solid, fore_colour gray25 ;align: horiz left')

        shipment_ids = ids.get('ids')
        shipment = self.env['ticl.shipment.log'].browse(shipment_ids)
        warehouse_id = shipment.mapped('sending_location_id').mapped('warehouse_key')
        warehouses = self.env['stock.warehouse'].search([('warehouse_key', 'in', warehouse_id)])

        for warehouse in warehouses:
            location = self.env['stock.location'].search([('warehouse_key', '=', shipment.sending_location_id.warehouse_key)])
            print("===location==",location)
            for location in location:
                shipments = self.env['ticl.shipment.log'].search([
                    ('sending_location_id', '=', location.id),
                    ('id', 'in', shipment.ids),
                    ('state', 'not in', ('cancel', 'shipped')),

                ], order='appointment_date_new desc')
                print("===shipments==",shipments)

                emails = []
                if shipments:
                    for email in warehouse.ticl_email_ids:
                        emails.append(email.name)
                    sheet_name = warehouse.name
                    workbook = xlwt.Workbook()
                    worksheet = workbook.add_sheet(sheet_name)
                    worksheet.col(0).width = 5000
                    worksheet.col(1).width = 5500
                    worksheet.col(2).width = 4000
                    worksheet.col(3).width = 5000
                    worksheet.col(4).width = 5000
                    worksheet.col(5).width = 4500
                    worksheet.col(6).width = 3000
                    worksheet.col(7).width = 8000
                    worksheet.col(8).width = 5000
                    worksheet.col(9).width = 5000
                    worksheet.col(10).width = 5000
                    worksheet.col(11).width = 5500
                    worksheet.col(12).width = 4000
                    worksheet.col(13).width = 4000
                    worksheet.col(14).width = 4000
                    worksheet.col(15).width = 4500
                    index = 0

                    date_format = xlwt.XFStyle()
                    date_format.num_format_str = 'mm/dd/yy'
                    for ship in shipments:

                        # header
                        worksheet.write(index, 0, _('Shipment ID'), column_heading_style)
                        worksheet.write(index, 1, _('Shipping Site'), column_heading_style)
                        worksheet.write(index, 2, _('Shipping Date'), column_heading_style)
                        worksheet.write(index, 3, _('Carrier'), column_heading_style)
                        worksheet.write(index, 4, _('BOL'), column_heading_style)
                        worksheet.write(index, 5, _('Shipment Type'), column_heading_style)
                        worksheet.write(index, 6, _('Pallet Count'), column_heading_style)
                        worksheet.write(index, 7, _('Destination'), column_heading_style)
                        worksheet.write(index, 8, _('Customer Name'), column_heading_style)
                        worksheet.write(index, 9, _('Customer Address 1'), column_heading_style)
                        worksheet.write(index, 10, _('Customer Address 2'), column_heading_style)
                        worksheet.write(index, 11, _('Contact Number'), column_heading_style)
                        worksheet.write(index, 12, _('City'), column_heading_style)
                        worksheet.write(index, 13, _('State'), column_heading_style)
                        worksheet.write(index, 14, _('Zip'), column_heading_style)
                        worksheet.write(index, 15, _('Country'), column_heading_style)

                        # content
                        index = index + 1

                        final_style = easyxf('align: wrap yes')


                        worksheet.write(index, 0, ship.name or '')
                        worksheet.write(index, 1, ship.sending_location_id.name or '', final_style)
                        worksheet.write(index, 2, ship.appointment_date_new, date_format or '')
                        worksheet.write(index, 3, ship.shipping_carrier_id.name or '', final_style)
                        worksheet.write(index, 4, ship.echo_tracking_id or '')
                        worksheet.write(index, 5, ship.shipment_type or '')
                        worksheet.write(index, 6, int(ship.total_pallet) or '')
                        worksheet.write(index, 7, ship.receiving_location_id.name or '', final_style)
                        worksheet.write(index, 8, ship.receiving_location_id.contact_name or '', final_style)
                        worksheet.write(index, 9, ship.receiving_location_id.street or '', final_style)
                        worksheet.write(index, 10, ship.receiving_location_id.street2 or '', final_style)
                        worksheet.write(index, 11, ship.receiving_location_id.phone or '')
                        worksheet.write(index, 12, ship.receiving_location_id.city_id.name or '', final_style)
                        worksheet.write(index, 13, ship.receiving_location_id.state_id.code or '', final_style)
                        worksheet.write(index, 14, ship.receiving_location_id.zip or '')
                        worksheet.write(index, 15, ship.receiving_location_id.country_id.name or '', final_style)

                        index = index + 2

                        worksheet.write(index, 0, _('Manufacturer'), column_heading_style2)
                        worksheet.write(index, 1, _('Model'), column_heading_style2)
                        worksheet.write(index, 2, _('Serial #'), column_heading_style2)
                        worksheet.write(index, 3, _('Quantity '), column_heading_style2)
                        worksheet.write(index, 4, _('Condition'), column_heading_style2)

                        for line in ship.ticl_ship_lines:
                            index = index + 1
                            worksheet.write(index, 0, line.manufacturer_id.name or '', final_style)
                            worksheet.write(index, 1, line.product_id.name or '', final_style)
                            worksheet.write(index, 2, line.lot_id.name or '')
                            worksheet.write(index, 3, 1)
                            worksheet.write(index, 4, line.ship_stock_move_id.condition_id.name or '')
                        index = index + 2
                    fp = io.BytesIO()
                    workbook.save(fp)
                    excel_file = base64.encodestring(fp.getvalue())
                    fp.close()
                    attach = {
                        'name': 'Warehouse Pending Report',
                        'datas': excel_file,
                        'datas_fname': 'Warehouse Pending Report.xls',
                        'res_model': 'stock.warehouse',
                        'type': 'binary'
                    }
                    if emails:
                        str_emails = ''
                        attachment = self.env['ir.attachment'].create(attach)
                        email_template = self.env.ref('ticl_wh_user_notification.email_template_warehouse_notify')
                        str_emails = ', '.join(emails)
                        template_values = {
                            'email_to': str_emails,
                            'email_cc': False,
                            'auto_delete': True,
                            'partner_to': False,
                            'subject': 'Warehouse Pending Shipment Notification ',
                            'scheduled_date': False,
                            'attachment_ids': [(4, attachment.id)],
                            "body_html": """<div>
                                            This is a Warehouse Pending Shipment Notification for Warehouse %s.</br>
                                            Please find the Attachment for Shipment Details.</div></br></br></br>
                                            <div>
                                            <div><p></p></div><div><p></p></div>
                                    
                                            Thanks,</br>
                                            Tellerex Inc.</div>""" % (warehouse.name,)
                        }
                        email_template.write(template_values)
                        _logger.info("Warehouse Notification emails before sent for user <%s> to ", str_emails)
                        mail_id = email_template.sudo().send_mail(2, raise_exception=True, force_send=True)
                        if mail_id: status = 's'
                        _logger.info("Warehouse Notification emails after sent for user <%s> to ", str_emails)
                        # shipments.sudo().write({'is_notified': True})
                        email_template.attachment_ids = [(3, attachment.id)]
                    msg += """ %s - Sent (%s) Shipments *
                        """ % (warehouse.name, len(shipments),)
                    if not shipments:
                        status = 'p'
                        if msg:
                            msg += """ %s - Not Sent (%s)*
                                           		""" % (warehouse.name, len(shipments),)
                        else:
                            message = "Cannot send notification for Shipped or Cancelled shipments"
                if msg: message = msg
        return {'status': status, 'message': message}
