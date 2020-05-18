from odoo import api, fields, models, _
from datetime import datetime, timedelta
import dateutil.relativedelta
import xlwt
from xlwt import easyxf
import io
import base64
import xlrd
import logging

_logger = logging.getLogger(__name__)


class rigger_email_warehouse_extend(models.Model):
    _inherit = 'warehouse.email'

    rigger_type_email = fields.Selection(
        [('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('lockbox', 'Lockbox')], default='none',
        string="Type for Rigger Arrival report")
    warehouse_notify = fields.Boolean(string='Warehouse Notification')
    weekly = fields.Boolean(string='Rigger Arrival Weekly')
    daily = fields.Boolean(string='Rigger Arrival Daily')
    lockbox = fields.Boolean(string='Lockbox')


class ticl_shipment_log_for_rigger(models.Model):
    _name = 'ticl.rigger.arrival.report'
    _description = "Ticl Rigger Arrival Report"

    name = fields.Char('File Name')
    rigger_arrival_file = fields.Binary('Rigger Arrival Report')
    rigger_type = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly')],
                                   string="Type for Rigger Arrival report")

    @api.model
    #@api.multi
    def _rigger_arrival_report_daily(self):
        workbook = xlwt.Workbook()
        rigger = self
        emails = []
        warehouse = self.env['warehouse.email'].sudo().search([('daily', '=', True)])
        for email in warehouse:
            emails.append(email.name)
        today_date = datetime.strptime(str(datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        previous_date = today_date - timedelta(days=1)
        previous_date_start = datetime.strptime(str(previous_date).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        previous_date_end = datetime.strptime(str(previous_date).split(' ')[0] + " 23:59:59", '%Y-%m-%d %H:%M:%S')
        self._cr.execute("""select * from ticl_shipment_log_line,ticl_shipment_log where ticl_shipment_log_line.ticl_ship_id= ticl_shipment_log.id
                and ticl_shipment_log.state='shipped' and ticl_shipment_log.appointment_date_new >= '{0}' and ticl_shipment_log.appointment_date_new <= '{1}';""".format(
            previous_date_start, previous_date_end))
        records = self._cr.dictfetchall()
        if records == []:
            return True
        column_heading_style = easyxf(
            'font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('Rigger Arrival Report')
        worksheet.write(0, 0, _('Destination ID Rigger'), column_heading_style)
        worksheet.write(0, 1, _('Shipment ID'), column_heading_style)
        worksheet.write(0, 2, _('Shipped Date'), column_heading_style)
        worksheet.write(0, 3, _('Estimated Delivery'), column_heading_style)
        worksheet.write(0, 4, _('Carrier'), column_heading_style)
        worksheet.write(0, 5, _('BOL'), column_heading_style)
        worksheet.write(0, 6, _('Project ID'), column_heading_style)
        worksheet.write(0, 7, _('Terminal ID'), column_heading_style)
        worksheet.write(0, 8, _('Common Name'), column_heading_style)
        worksheet.write(0, 9, _('Manufacturer'), column_heading_style)
        worksheet.write(0, 10, _('Model'), column_heading_style)
        worksheet.write(0, 11, _('Serial #'), column_heading_style)
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5500
        worksheet.col(2).width = 3800
        worksheet.col(3).width = 5500
        worksheet.col(4).width = 4500
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5800
        worksheet.col(7).width = 6000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 6000
        worksheet.col(10).width = 5000
        worksheet.col(11).width = 6000
        row = 1
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'mm/dd/yy'
        for recs in records:
            shipment_id = self.env['ticl.shipment.log'].search([('id', '=', recs['ticl_ship_id'])])
            manufacturer_id = self.env['manufacturer.order'].search([('id', '=', recs['manufacturer_id'])])
            product_id = self.env['product.product'].search([('id', '=', recs['product_id'])])
            lot_id = self.env['stock.production.lot'].search([('id', '=', recs['lot_id'])])
            worksheet.write(row, 0, shipment_id.receiving_location_id.name or shipment_id.receiving_rigger_id.name or '')
            worksheet.write(row, 1, shipment_id.name or '')
            worksheet.write(row, 2, datetime.strptime(str(shipment_id.appointment_date_new) + " 00:00:00",
                                                      '%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y "), date_format or '')
            if shipment_id.estimated_delivery_date_new:
                worksheet.write(row, 3, datetime.strptime(str(shipment_id.estimated_delivery_date_new) + " 00:00:00",'%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y"), date_format or '')
            else:
                if shipment_id.delivery_date_new:
                    worksheet.write(row, 3, datetime.strptime(str(shipment_id.delivery_date_new) + " 00:00:00",'%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y"), date_format or '')
                else:
                    worksheet.write(row, 3,'')
            worksheet.write(row, 4, shipment_id.shipping_carrier_id.name or '')
            worksheet.write(row, 5, shipment_id.echo_tracking_id or '')
            worksheet.write(row, 6, recs['ticl_project_id'] or '')
            worksheet.write(row, 7, recs['tid'] or '')
            worksheet.write(row, 8, recs['common_name'] or '')
            worksheet.write(row, 9, manufacturer_id.name or '')
            worksheet.write(row, 10, product_id.name or '')
            worksheet.write(row, 11, lot_id.name or recs['serial_number'] or '')
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        excel_file = base64.decodestring(excel_file)
        book = xlrd.open_workbook(file_contents=excel_file, formatting_info=True)
        wbk = xlwt.Workbook()
        for i in range(len(book.sheets())):
            sheet = book.sheets()[i]
            if sheet.name == "Rigger Arrival Report":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: (len(x[10]), x[10]))
                data.sort(key=lambda x: x[3])
                data.sort(key=lambda x: x[1])
                data.sort(key=lambda x: x[0])
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 8500
                sheet.col(1).width = 4000
                sheet.col(2).width = 4800
                sheet.col(3).width = 3800
                sheet.col(4).width = 5650
                sheet.col(5).width = 4100
                sheet.col(6).width = 5200
                sheet.col(7).width = 5200
                sheet.col(8).width = 5000
                sheet.col(9).width = 6000
                sheet.col(10).width = 5000
                sheet.col(11).width = 4600
                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        sheet.write(idx_r + 1, idx_c, value)
        fp = io.BytesIO()
        wbk.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        rigger_id = self.sudo().create(
            {'name': 'Daily Rigger Arrival Report', 'rigger_arrival_file': excel_file, 'rigger_type': 'daily'})
        fp.close()
        attach = {
            'name': 'Daily Rigger Arrival Report',
            'datas': excel_file,
            'datas_fname': 'Daily Rigger Arrival Report.xls',
            'res_model': 'ticl.rigger.arrival.report',
            'type': 'binary'
        }
        attachment = self.env['ir.attachment'].create(attach)
        email_template = self.env.ref('ticl_rigger_arrival_report.email_template_rigger_report')
        str_emails = ', '.join(emails)
        template_values = {
            'email_to': str_emails,
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'subject': 'Daily Rigger Arrival Report',
            'scheduled_date': False,
            'attachment_ids': [(4, attachment.id)],
            "body_html": """
        </br>
        <div>
        Please find the below attachment for Daily Rigger Arrival Report.</div></br></br></br>
           <div>

        Thanks,</br>
        Tellerex Inc.</div>"""
        }
        email_template.write(template_values)
        _logger.info("Warehouse Notification emails before sent for user <%s> to ", str_emails)
        email_template.send_mail(rigger_id.id, raise_exception=True, force_send=True)
        _logger.info("Warehouse Notification emails after sent for user <%s> to ", str_emails)
        rigger.sudo().is_notified = True
        email_template.attachment_ids = [(3, attachment.id)]
        return True

    @api.model
    #@api.multi
    def _rigger_arrival_report_weekly(self):
        workbook = xlwt.Workbook()
        rigger = self
        emails = []
        warehouse = self.env['warehouse.email'].sudo().search([('weekly', '=', True)])
        for email in warehouse:
            emails.append(email.name)
        today_date = datetime.strptime(str(datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        self._cr.execute("""select * from ticl_shipment_log_line,ticl_shipment_log where ticl_shipment_log_line.ticl_ship_id= ticl_shipment_log.id
                and ticl_shipment_log.state='shipped' and ticl_shipment_log.appointment_date_new >= '{0}' and ticl_shipment_log.appointment_date_new <= '{1}';""".format(
            today_date - timedelta(days=7), today_date))
        records = self._cr.dictfetchall()
        if records == []:
            return True
        column_heading_style = easyxf(
            'font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('Rigger Arrival Report')
        worksheet.write(0, 0, _('Destination ID Rigger'), column_heading_style)
        worksheet.write(0, 1, _('Shipment ID'), column_heading_style)
        worksheet.write(0, 2, _('Shipped Date'), column_heading_style)
        worksheet.write(0, 3, _('Estimated Delivery'), column_heading_style)
        worksheet.write(0, 4, _('Carrier'), column_heading_style)
        worksheet.write(0, 5, _('BOL'), column_heading_style)
        worksheet.write(0, 6, _('Project ID'), column_heading_style)
        worksheet.write(0, 7, _('Terminal ID'), column_heading_style)
        worksheet.write(0, 8, _('Common Name'), column_heading_style)
        worksheet.write(0, 9, _('Manufacturer'), column_heading_style)
        worksheet.write(0, 10, _('Model'), column_heading_style)
        worksheet.write(0, 11, _('Serial #'), column_heading_style)
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5500
        worksheet.col(2).width = 38000
        worksheet.col(3).width = 5500
        worksheet.col(4).width = 4500
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5800
        worksheet.col(7).width = 6000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 6000
        worksheet.col(10).width = 5000
        worksheet.col(11).width = 6000
        row = 1
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'mm/dd/yy'
        for recs in records:
            shipment_id = self.env['ticl.shipment.log'].search([('id', '=', recs['ticl_ship_id'])])
            manufacturer_id = self.env['manufacturer.order'].search([('id', '=', recs['manufacturer_id'])])
            product_id = self.env['product.product'].search([('id', '=', recs['product_id'])])
            lot_id = self.env['stock.production.lot'].search([('id', '=', recs['lot_id'])])
            worksheet.write(row, 0, shipment_id.receiving_location_id.name or shipment_id.receiving_rigger_id.name or '')
            worksheet.write(row, 1, shipment_id.name or '')
            worksheet.write(row, 2, datetime.strptime(str(shipment_id.appointment_date_new) + " 00:00:00",
                                                      '%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y "), date_format or '')
            if shipment_id.estimated_delivery_date_new:
                worksheet.write(row, 3, datetime.strptime(str(shipment_id.estimated_delivery_date_new) + " 00:00:00",'%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y"), date_format or '')
            else:
                if shipment_id.delivery_date_new:
                    worksheet.write(row, 3, datetime.strptime(str(shipment_id.delivery_date_new) + " 00:00:00",'%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y"), date_format or '')
                else:
                    worksheet.write(row, 3,'')

            worksheet.write(row, 4, shipment_id.shipping_carrier_id.name or '')
            worksheet.write(row, 5, shipment_id.echo_tracking_id or '')
            worksheet.write(row, 6, recs['ticl_project_id'] or '')
            worksheet.write(row, 7, recs['tid'] or '')
            worksheet.write(row, 8, recs['common_name'] or '')
            worksheet.write(row, 9, manufacturer_id.name or '')
            worksheet.write(row, 10, product_id.name or '')
            worksheet.write(row, 11, lot_id.name or recs['serial_number'] or '')
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        fp = io.BytesIO()
        workbook.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        excel_file = base64.decodestring(excel_file)
        book = xlrd.open_workbook(file_contents=excel_file, formatting_info=True)
        wbk = xlwt.Workbook()
        for i in range(len(book.sheets())):
            sheet = book.sheets()[i]
            if sheet.name == "Rigger Arrival Report":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                data.sort(key=lambda x: (len(x[10]), x[10]))
                data.sort(key=lambda x: x[3])
                data.sort(key=lambda x: x[1])
                data.sort(key=lambda x: x[0])
                sheet = wbk.add_sheet(sheet.name)
                sheet.col(0).width = 8500
                sheet.col(1).width = 4000
                sheet.col(2).width = 4800
                sheet.col(3).width = 3800
                sheet.col(4).width = 5650
                sheet.col(5).width = 4100
                sheet.col(6).width = 5200
                sheet.col(7).width = 5200
                sheet.col(8).width = 5000
                sheet.col(9).width = 6000
                sheet.col(10).width = 5000
                sheet.col(11).width = 4600
                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label, column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        sheet.write(idx_r + 1, idx_c, value)
        fp = io.BytesIO()
        wbk.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        rigger_id = self.sudo().create(
            {'name': 'Weekly Rigger Arrival Report', 'rigger_arrival_file': excel_file, 'rigger_type': 'weekly'})
        fp.close()
        attach = {
            'name': 'Weekly Rigger Arrival Report',
            'datas': excel_file,
            'datas_fname': 'Weekly Rigger Arrival Report.xls',
            'res_model': 'ticl.rigger.arrival.report',
            'type': 'binary'
        }
        attachment = self.env['ir.attachment'].create(attach)
        email_template = self.env.ref('ticl_rigger_arrival_report.email_template_rigger_report')
        str_emails = ', '.join(emails)
        template_values = {
            'email_to': str_emails,
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'subject': 'WeeklyRigger Arrival Report',
            'scheduled_date': False,
            'attachment_ids': [(4, attachment.id)],
            "body_html": """
                            </br>
                            <div>
                            Please find the below attachment for Weekly Rigger Arrival Report.</div></br></br></br>
                               <div>
                        
                            Thanks,</br>
                            Tellerex Inc.</div>"""
                                }
        email_template.write(template_values)
        _logger.info("Warehouse Notification emails before sent for user <%s> to ", str_emails)
        email_template.send_mail(rigger_id.id, raise_exception=True, force_send=True)
        _logger.info("Warehouse Notification emails after sent for user <%s> to ", str_emails)
        rigger.sudo().is_notified = True
        email_template.attachment_ids = [(3, attachment.id)]
        return True
