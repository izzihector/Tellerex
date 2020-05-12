from odoo import models, api, _
import base64
import xlrd
from datetime import datetime, timedelta
from odoo.exceptions import AccessError
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class ticl_shipment_log(models.Model):
    _name = 'ticl.inbound.import'

    def getSipmentType(self, equipment_date):
        eqp_dt_time = datetime.strptime(equipment_date, '%Y-%m-%d %H:%M:%S')
        diff_sev = eqp_dt_time.date() - timedelta(days=7)
        time_between_insertion = diff_sev - datetime.now().date()
        if time_between_insertion.days >= 5:
            shipType = 'regular'
        else:
            shipType = 'expedited'
        return shipType

    @api.model
    def shipment_asn_import_ext(self, vals):
        message = 'Tender Imported Successfully!'
        status = 's'
        # try:
        xl = vals.get('file').split(',')
        xlsx_file = xl[1].encode()
        xls_file = base64.decodestring(xlsx_file)
        wb = xlrd.open_workbook(file_contents=xls_file)
        print('===========================-----Import Started!-----===========================')
        print('===================-----Import Started!-----=================', len(wb.sheets()))
        # if len(wb.sheets())!=1:
        #     message = 'Invalid file format,Please verify the file!'
        #     raise Exception(message)
        for sheet in wb.sheets():
            msg_list = []
            msg_list2 = []
            serial_no_list = []
            for row in range(sheet.nrows):
                if row == 0:
                    continue

                model = sheet.cell(row, 5).value
                serial = sheet.cell(row, 6).value
                if model:
                    try:
                        model = int(model)
                    except:
                        model = sheet.cell(row, 5).value
                        model = str(model).strip()
                    product = self.env['product.product'].sudo().search([('name', '=', str(model))], limit=1)
                    if not product:
                        cl_r_prt = sheet.cell(0, 5).value

                        msg_list2.append("model(%s) at row %s" % (model, row + 1))
                    vals.update({'product_id': product})
                    if product.categ_id.name == 'ATM':
                        if not serial:
                            cl_r_sn = sheet.cell(0, 6).value
                            msg_list.append(
                                "serial at row %s" % (row + 1))
                        if serial:
                            try:
                                serial = int(serial)
                            except:
                                serial = sheet.cell(row, 6).value
                                serial = str(serial).strip()
                                if "." in serial:
                                    serial_number = serial.split('.')
                                    serial = serial_number[0]

                            length = len(str(serial))
                            if length != 8 and product.manufacturer_id.name == "NCR":
                                raise UserError('Serial number at row %s should be 8 Digit for NCR ATM' % (row + 1))

                            if length != 10 and product.manufacturer_id.name in ["Nautilus Hyosung", "Wincor"]:
                                raise UserError("Serial number at row %s should be 10 Digit for  ATM's %s !"
                                                % (row + 1, product.manufacturer_id.name))

                            if length != 12 and product.manufacturer_id.name == "Diebold":
                                raise UserError(
                                    'Serial number at row %s should be 12 Digit for Diebold ATM' % (row + 1))

                            inv_status = []
                            move_id = self.env['stock.move'].sudo().search([('serial_number', '=', str(serial))],
                                                                           limit=1)
                            receipt_record = self.env['ticl.receipt.line'].sudo().search(
                                [('serial_number', '=', str(serial))])
                            receipt_status = []
                            for rec in receipt_record:
                                if rec.serial_number:
                                    if receipt_record:
                                        for ids2 in receipt_record:
                                            receipt_status.append(ids2.ticl_receipt_id.state)

                                    if 'draft' in receipt_status:
                                        msg_list.append("serial at row  %s" % (row + 1))
                                    elif 'pending' in receipt_status:
                                        msg_list.append("serial at row  %s" % (row + 1))
                                    elif 'inprogress' in receipt_status:
                                        msg_list.append("serial at row  %s" % (row + 1))

                                    if move_id:
                                        for ids in move_id:
                                            inv_status.append(ids.status)
                                    if 'inventory' in inv_status:
                                        msg_list.append("serial at row  %s" % (row + 1))
                                    elif 'assigned' in inv_status:
                                        msg_list.append("serial at row  %s" % (row + 1))
                                    elif 'picked' in inv_status:
                                        msg_list.append("serial at row  %s" % (row + 1))
                                    elif 'packed' in inv_status:
                                        msg_list.append("serial at row  %s" % (row + 1))
                            if serial in serial_no_list:
                                raise UserError('Duplicate Serial number not allowed')
                            serial_no_list.append(serial)
                            # receipt_record = self.env['ticl.receipt.line'].sudo().search([('serial_number', '=', str(serial))])
                            # for record in receipt_record:
                            #     if record.serial_number:
                            #         stock_move = self.env['stock.move'].search(
                            #             [('serial_number', '=', record.serial_number),
                            #              ('status', '!=', 'shipped')])
                            #
                            #         if stock_move or record.ticl_receipt_id.state != 'completed':
                            #             msg_list.append("serial at row  %s" % (row + 1))

            if msg_list:
                unique_list = []
                for elem in msg_list:
                    if elem not in unique_list:
                        unique_list.append(elem)
                raise UserError(str(unique_list) + ' is missing/already exists, Please review the file.')

            if msg_list2:
                raise UserError(str(msg_list2) + 'is not in Product list')

        origin_location = {}
        for sheet in wb.sheets():
            for row in range(sheet.nrows):
                if row == 0:
                    continue
                vals = {}
                loc = False
                pickupDate = sheet.cell(row, 0).value
                print('-----Import Started!-----')
                if pickupDate:
                    if isinstance(pickupDate, float) == True or isinstance(pickupDate, int) == True:
                        x = datetime(*xlrd.xldate_as_tuple(pickupDate, wb.datemode))
                        sp = str(x).split(' ')
                        dft = sp[0]
                        if '/' in dft:
                            x = dft.split('/')
                        elif '-' in dft:
                            x = dft.split('-')
                        dates = datetime(int(x[0]), int(x[1]), int(x[2]), 00, 00, 00)
                        # dates = datetime(int(dft[0:4]), int(dft[5:7]), int(dft[-2:]), 00, 00, 00)
                    else:
                        dft=pickupDate
                        if '/' in dft:
                            x = dft.split('/')
                        elif '-' in dft:
                            x = dft.split('-')
                        dates = datetime(int(x[2]), int(x[0]), int(x[1]), 00, 00, 00)
                        # dates = datetime(int(pickupDate[-4:]), int(pickupDate[:2]), int(pickupDate[3:5]), 00, 00, 00)
                    datetime_object = dates
                    #datetime_object = datetime(*xlrd.xldate_as_tuple(pickupDate, wb.datemode))
                    pickup_date = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
                    vals.update({'pickup_date': pickup_date})
                deliveryDate = sheet.cell(row, 1).value
                if deliveryDate:
                    if isinstance(deliveryDate, float) == True or isinstance(deliveryDate, int) == True:
                        x = datetime(*xlrd.xldate_as_tuple(deliveryDate, wb.datemode))
                        sp = str(x).split(' ')
                        dft = sp[0]
                        dates = datetime(int(dft[0:4]), int(dft[5:7]), int(dft[-2:]), 00, 00, 00)
                    else:
                        dates = datetime(int(deliveryDate[-4:]), int(deliveryDate[:2]), int(deliveryDate[3:5]), 00, 00, 00)
                    datetime_obj = dates
                    # datetime_obj = datetime(*xlrd.xldate_as_tuple(deliveryDate, wb.datemode))
                    delivery_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                    vals.update({'delivery_date': delivery_date})
                originLocation = sheet.cell(row, 2).value
                if originLocation:
                    originLocation = str(originLocation).strip()
                    loc = self.env['res.partner'].sudo().search([('name', '=', originLocation)],
                                                                   limit=1).id
                    if not loc:
                        raise UserError(
                            "Origin Location (%s) not found, Please review the file." % originLocation)

                    vals.update({'sending_location_id': loc})
                    if loc not in origin_location:
                        origin_location.update({loc: []})
                nop = sheet.cell(row, 3).value
                if type(nop) == str:
                    raise UserError("Pallet must be present and numeric, Please review the file.")
                if nop >= 1:
                    vals.update({'total_pallet': nop})
                else:
                    raise UserError("Pallet should be greater than 0, Please review the file.")
                warehouseKey = sheet.cell(row, 4).value
                if warehouseKey:
                    receiving_loc_id = self.env['stock.location'].sudo().search(
                        [('warehouse_key', '=', int(warehouseKey))], limit=1).id
                    if not receiving_loc_id:
                         raise UserError("Warehouse Key (%s) not found, Please review the file." % int(warehouseKey))
                        # receiving_loc_id = self.env['stock.location'].sudo().create(
                        #     {'name': originLocation, 'warehouse_key': warehouseKey}).id
                    vals.update({'receiving_location_id': receiving_loc_id})
                model = sheet.cell(row, 5).value

                serial = sheet.cell(row, 6).value

                if model:
                    try:
                        model = int(model)
                    except:
                        model = sheet.cell(row, 5).value
                        model = str(model).strip()
                    product = self.env['product.product'].sudo().search([('name', '=', str(model))], limit=1)
                    if not product:
                        cl_r_prt = sheet.cell(0, 5).value
                        raise UserError("One of the model(%s) at row %s is missing, Please review the file." % (model,row+1))
                    vals.update({'product_id': product})
                    if product.categ_id.name == 'ATM':
                        if not serial:
                            print('===================-----Product Categ-----=================',
                                  product.categ_id.name)
                            cl_r_sn = sheet.cell(0, 6).value
                            raise UserError("One of the serial at row %s is missing, Please review the file." % (row+1))
                    if product.categ_id.name not in ('ATM', 'XL') and serial:
                        raise UserError("Serial Number not required for %s, Please review the file." % product.categ_id.name)
                if serial:
                    try:
                        serial = int(serial)
                    except:
                        serial = sheet.cell(row, 6).value
                        serial = str(serial).strip()
                        if "." in serial:
                            serial_number = serial.split('.')
                            serial = serial_number[0]
                    vals.update({'serial_number': serial})
                quantity = sheet.cell(row, 7).value
                if type(quantity) == str:
                    raise UserError("Quantity must be present and numeric, Please review the file.")
                if quantity >= 1:
                    product = self.env['product.product'].sudo().search([('name', '=', str(model))], limit=1)
                    if product.categ_id.name == 'ATM' and quantity > 1:
                        raise UserError("Quantity should not be greater than 1 for ATMS, Please review the file.")
                    else:
                        vals.update({'count_number': int(quantity)})
                else:
                    raise UserError("Quantity should be greater than 0, Please review the file.")
                condition = sheet.cell(row, 8).value
                if condition:
                    condition = str(condition).strip()
                    condition_id = self.env['ticl.condition'].sudo().search([('name', '=', condition)], limit=1).id
                    if not condition_id:
                        raise UserError(
                            "Condition (%s) not found, Please review the file." % condition)
                    vals.update({'condition_id': condition_id})

                if not pickupDate:
                    cl_r_sn = sheet.cell(0, 0).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)
                if not originLocation:
                    cl_r_sn = sheet.cell(0, 2).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)
                if not condition:
                    cl_r_sn = sheet.cell(0, 8).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)
                if not quantity:
                    cl_r_sn = sheet.cell(0, 7).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)
                if not model:
                    cl_r_sn = sheet.cell(0, 5).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)
                if not warehouseKey:
                    cl_r_sn = sheet.cell(0, 4).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)
                if not nop:
                    cl_r_sn = sheet.cell(0, 3).value
                    raise UserError("One of the %s is missing, Please review the file." % cl_r_sn)

                origin_location.get(loc).append(vals)

            if not origin_location:
                raise UserError('Empty File cannot be imported.')

        for key in origin_location.keys():
            locationLists = origin_location.get(key)
            warehouses = {}
            for locationList in locationLists:
                if locationList.get('receiving_location_id') not in warehouses:
                    warehouses.update({locationList.get('receiving_location_id'): [locationList]})
                else:
                    warehouses.get(locationList.get('receiving_location_id')).append(locationList)

            for w_key in warehouses.keys():
                pickupdate = {}
                pickupdate_segs = warehouses.get(w_key)
                for pickupdate_seg in pickupdate_segs:
                    if pickupdate_seg.get('pickup_date') not in pickupdate:
                        pickupdate.update({pickupdate_seg.get('pickup_date'): [pickupdate_seg]})
                    else:
                        pickupdate.get(pickupdate_seg.get('pickup_date')).append(pickupdate_seg)

                for pdList in pickupdate.values():
                    lines, data, palletCount = [], {}, 0
                    for pd in pdList:
                        lines.append((
                            0, 0, {
                                'tel_type': pd.get('product_id').categ_id.id,
                                'manufacturer_id': pd.get('product_id').manufacturer_id.id,
                                'product_id': pd.get('product_id').id,
                                'count_number': int(pd.get('count_number')),
                                'condition_id': pd.get('condition_id'),
                                'serial_number': pd.get('serial_number'),
                                'xl_items': pd.get('product_id').xl_items,
                            }))
                        palletCount += int(pd.get('total_pallet'))
                        data.update({
                            'sending_location_id': pd.get('sending_location_id'),
                            'receiving_location_id': pd.get('receiving_location_id'),
                            'pickup_date': pd.get('pickup_date'),
                            'total_pallet': palletCount,
                            'delivery_date': pd.get('delivery_date', False)
                        })
                    data.update({'ticl_receipt_lines': lines})
                    receipt_obj = self.env['ticl.receipt.asn'].create(data)
                    receipt_obj.submit_asn()

        # except Exception as e:
        #     msg = str(e)
        #     message = msg
        #     status = 'n'
        #     self.env.cr.rollback()
        return {'message': message, 'status': status}
