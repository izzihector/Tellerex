# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from odoo import fields, models, tools, api,_
import xlwt
import io
import base64
from xlwt import easyxf
from xlrd import open_workbook
import xlrd
import datetime as r_datetime

class ticl_recommend_model(models.Model):
    _name = "ticl.recommend.model"
    _order = 'sending_location_id asc, m_id asc,product_id asc, delivery_date asc'
    _description = "Pending Inprogress and Completed data"

    sending_location_id = fields.Many2one('stock.location', string='Location')
    manufacturer_id = fields.Many2one('manufacturer.order', string="Manufacturer")
    m_id = fields.Char(string='Manufacturer Name')
    product_id = fields.Many2one('product.product', string='Model Name')
    serial_number = fields.Char(string='Serial #')
    condition_id = fields.Many2one('ticl.condition', string="Condition")
    tel_note = fields.Char(string='Comment/Note')
    ticl_age = fields.Char(string='Aging')
    delivery_date = fields.Date(string='Received Date')
    status = fields.Char('Status')

    def update_view(self):
        self._cr.execute("""DELETE FROM ticl_recommend_model;""")
        self._cr.execute("""select ticl_receipt.state as status,receiving_location_id as sending_location_id,manufacturer_id,product_id,serial_number,condition_id,ticl_receipt_line.tel_note from ticl_receipt_line,ticl_receipt,ticl_condition,stock_location 
        where ticl_condition.name = 'To Recommend' and ticl_receipt.id = ticl_receipt_line.ticl_receipt_id and stock_location.is_location = True and ticl_receipt.receiving_location_id = stock_location.id
        and ticl_receipt_line.condition_id = ticl_condition.id and ticl_receipt.state = 'pending';""")
        records = self._cr.dictfetchall()
        for recs in records:
            recs['status'] = recs['status'].capitalize()
            recs['ticl_age'] = 'Pre Arrival'
            manufacturer_id = self.env['manufacturer.order'].search([('id', '=', recs['manufacturer_id'])])
            if manufacturer_id.name == 'NCR':
                recs['m_id'] = 'Ncr'
            else:
                recs['m_id'] = manufacturer_id.name
            self.env['ticl.recommend.model'].create(recs)
        self._cr.execute("""select ticl_receipt_log_summary.state as status,receiving_location_id as sending_location_id,CAST(received_date AS DATE) AS delivery_date,CAST(DATE_PART('day', NOW()::timestamp - received_date::timestamp) as int) AS ticl_age,manufacturer_id,product_id,serial_number,condition_id,ticl_receipt_log_summary_line.tel_note from ticl_receipt_log_summary_line,ticl_receipt_log_summary,ticl_condition,stock_location 
        where ticl_condition.name = 'To Recommend' and ticl_receipt_log_summary.id = ticl_receipt_log_summary_line.ticl_receipt_summary_id and stock_location.is_location = True and ticl_receipt_log_summary.receiving_location_id = stock_location.id
        and ticl_receipt_log_summary_line.condition_id = ticl_condition.id and ticl_receipt_log_summary.state = 'inprogress' and ticl_receipt_log_summary_line.move_to_inv ='n';
        """)
        records = self._cr.dictfetchall()
        for recs in records:
            if recs['status'] == 'inprogress':
                recs['status'] = 'In-Progress'
            manufacturer_id = self.env['manufacturer.order'].search([('id', '=', recs['manufacturer_id'])])
            if manufacturer_id.name == 'NCR':
                recs['m_id'] = 'Ncr'
            else:
                recs['m_id'] = manufacturer_id.name
            self.env['ticl.recommend.model'].create(recs)
        self._cr.execute("""select stock_move_line.status as status,stock_move_line.tel_note as tel_note,ticl_warehouse_id as sending_location_id,CAST(received_date AS DATE) AS delivery_date,CAST(DATE_PART('day', NOW()::timestamp - received_date::timestamp) as int) AS ticl_age,
        manufacturer_id,product_id,serial_number,condition_id from stock_move_line,ticl_condition,stock_location  where ticl_condition.name = 'To Recommend' and stock_location.is_location = True and stock_move_line.ticl_warehouse_id = stock_location.id and
        stock_move_line.condition_id = ticl_condition.id and stock_move_line.status in ('inventory','assigned');
        """)
        records = self._cr.dictfetchall()
        for recs in records:
            recs['status'] = recs['status'].capitalize()
            manufacturer_id = self.env['manufacturer.order'].search([('id', '=', recs['manufacturer_id'])])
            if manufacturer_id.name == 'NCR':
                recs['m_id'] = 'Ncr'
            else:
                recs['m_id'] = manufacturer_id.name
            self.env['ticl.recommend.model'].create(recs)
        return True

class ticl_recommend_report(models.Model):
    _name = "ticl.recommend.report"
    _description = "Pending Inprogress and Completed data"

    to_rec_file = fields.Binary('To Recommend Report')
    file_name = fields.Char('File Name')

    def export_excel(self):
        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        worksheet = workbook.add_sheet('To Recommend Report')
        worksheet.write(0, 0, _('Location'), column_heading_style)
        worksheet.write(0, 1, _('Manufacturer'), column_heading_style)
        worksheet.write(0, 2, _('Model'), column_heading_style)
        worksheet.write(0, 3, _('Serial#'), column_heading_style)
        worksheet.write(0, 4, _('Condition'), column_heading_style)
        worksheet.write(0, 5, _('Received Date'), column_heading_style)
        worksheet.write(0, 6, _('Aging'), column_heading_style)
        worksheet.write(0, 7, _('Status'), column_heading_style)
        worksheet.write(0, 8, _('Comments'), column_heading_style)

        worksheet.col(0).width = 6000
        worksheet.col(1).width = 7000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 6000

        row = 1
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'mm-dd-yy'
        self._cr.execute("""select * from ticl_recommend_model where delivery_date is null ;""")
        rec = self._cr.dictfetchall()
        self._cr.execute("""select CAST(DATE_PART('day', NOW()::timestamp - delivery_date::timestamp) as int) AS age,* from ticl_recommend_model where ticl_age !='Pre Arrival' order by delivery_date asc;
        """)
        recs = self._cr.dictfetchall()
        records = rec+recs
        for recs in records:
            if 'age' in recs.keys():
                ticl_age = recs['age']
            location = self.env['stock.location'].search([('id','=',recs['sending_location_id'])])
            manufacturer_id = self.env['manufacturer.order'].search([('id','=',recs['manufacturer_id'])])
            product_id = self.env['product.product'].search([('id','=',recs['product_id'])])
            condition_id = self.env['ticl.condition'].search([('id','=',recs['condition_id'])])
            worksheet.write(row, 0, location.name or '')
            if manufacturer_id.name == 'NCR':
                name = 'Ncr'
            else:
                name = manufacturer_id.name
            worksheet.write(row, 1, name or '')
            worksheet.write(row, 2, product_id.name or '')
            worksheet.write(row, 3, recs['serial_number'])
            worksheet.write(row, 4, condition_id.name or '')
            if recs['delivery_date'] != None:
                c_5 = str(recs['delivery_date']).split('-')
                c5 = '{0}-{1}-{2}'.format(c_5[1], c_5[2], c_5[0])
            else:
                c5=''
            worksheet.write(row, 5, c5 or '')                
            worksheet.write(row, 6, recs['ticl_age'] or '')
            worksheet.write(row, 7, recs['status'] or '')
            worksheet.write(row, 8, recs['tel_note'] or '')
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        excel_file = base64.decodestring(excel_file)
        book = xlrd.open_workbook(file_contents=excel_file, formatting_info=True)
        wbk = xlwt.Workbook()
        column_heading_style = easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        for i in range(len(book.sheets())):
            sheet = book.sheets()[i]
            if sheet.name == "To Recommend Report":
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                labels = data[0]
                data = data[1:]
                # data.sort(key=lambda x: x[5])
                data.sort(key=lambda x: x[2])
                data.sort(key=lambda x: x[1])
                data.sort(key=lambda x: x[0])
                sheet = wbk.add_sheet(sheet.name, cell_overwrite_ok=True)
                sheet.col(0).width = 8000
                sheet.col(1).width = 7000
                sheet.col(2).width = 6000
                sheet.col(3).width = 5000
                sheet.col(4).width = 5000
                sheet.col(5).width = 5000
                sheet.col(6).width = 4000
                sheet.col(7).width = 5000
                sheet.col(8).width = 6000
                style = xlwt.easyxf('font:name Calibri;')
                green_style = xlwt.easyxf('font: colour green,name Calibri,bold True;align: horiz left;')
                orange_style = xlwt.easyxf('font: colour orange,name Calibri,bold True;align: horiz left;')
                red_style = xlwt.easyxf('font: colour red,name Calibri,bold True;align: horiz left;')
                date_formats = easyxf('font: name Calibri; align: horiz left, wrap yes', num_format_str='mm-dd-yy')
                for idx, label in enumerate(labels):
                    sheet.write(0, idx, label,column_heading_style)
                for idx_r, row in enumerate(data):
                    for idx_c, value in enumerate(row):
                        if idx_c == 5:
                            if value !='':
                                v = value.split('-')
                                x = r_datetime.datetime(int(v[2]), int(v[0]), int(v[1]))
                                sheet.write(idx_r + 1, idx_c, x.date(), date_formats)
                            else:
                                sheet.write(idx_r + 1, idx_c,value,date_formats)
                        elif idx_c == 1:
                            if value == 'Ncr':
                                value = 'NCR'
                            sheet.write(idx_r + 1, idx_c, value,style)
                        elif idx_c == 6:
                            if value not in ('Pre Arrival',' '):
                                if int(value) < 15:
                                    sheet.write(idx_r + 1, idx_c, int(value), green_style or '')
                                if int(value) >= 15 and int(value) <=29 :
                                    sheet.write(idx_r + 1, idx_c, int(value), orange_style or '')
                                if int(value) >=30 :
                                    sheet.write(idx_r + 1, idx_c, int(value), red_style or '')
                            else:
                                sheet.write(idx_r + 1, idx_c, value,green_style or '')
                        else:
                            sheet.write(idx_r + 1, idx_c, value,style)
                            sheet.write(idx_r + 1, 8, value,style)
        fp = io.BytesIO()
        wbk.save(fp)
        excel_file = base64.encodestring(fp.getvalue())
        report_id = self.env['ticl.recommend.report'].create({'to_rec_file':excel_file,'file_name':'To Recommend Report'})
        fp.close()
        return {'id':report_id.id}
