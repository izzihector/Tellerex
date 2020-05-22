from odoo import models, api, _
import base64
import xlrd
from datetime import datetime, timedelta
from odoo.exceptions import AccessError
import datetime as real_datetime

class ticl_shipment_log(models.Model):
    _name = 'ticl.tender.import'

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
    def shipment_tender_import_ext(self, vals):
        message = 'Tender Imported Successfully!'
        status = 's'
        product_list = []
        act_date = []

        #         valslist = []
        try:
            xl = vals.get('file').split(',')
            xlsx_file = xl[1].encode()
            xls_file = base64.decodestring(xlsx_file)
            wb = xlrd.open_workbook(file_contents=xls_file)
            condition = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
            for sheet in wb.sheets():
                col_count = sheet.ncols
                if col_count != 11:
                    raise Exception("One of the column missing, Please review the file.")
                shipTo_list = sheet.col_values(8)
                shipTo = [elem.strip() for elem in shipTo_list]
                shipTo.pop(0)
                locations = self.env['res.partner'].sudo().search(
                    [('name', 'in', shipTo)]).ids
                if not locations:
                    raise Exception("Please verify the ship To Locations and Import again!")
                for location in locations:
                    warehouse_vals = {}
                    vals = {}
                    warehouse = {}
                    origin_location = False
                    for row in range(sheet.nrows):
                        dt = {'count_number': 1}
                        if row == 0:
                            continue
                        try:
                            product_name = str(int(sheet.cell(row, 9).value)).strip()
                        except:
                            product_name = str(sheet.cell(row, 9).value).strip()
                        if not product_name:
                            self.env.cr.rollback()
                            raise Exception("Please verify the Models and Import again!")
                        if "." in product_name[-2:-1]:
                            prod_lst = product_name.split('.')
                            product_name = prod_lst[0]
                        print('\n\n\n product_name',product_name)
                        product = self.env['product.product'].sudo().search([('name', '=', product_name)], limit=1)
                        if not product:
                            product_list.append(product_name)
                            self.env.cr.rollback()
                            raise Exception("Model (%s) is not found, Please review the file." % (product_name))

                        fdt = sheet.cell(row, 2).value
                        if not fdt:
                            cl_r_fdt = sheet.cell(0, 2).value
                            self.env.cr.rollback()
                            raise Exception("One of the %s is missing, Please review the file." % (cl_r_fdt))
                        dt.update({'funding_doc_type': fdt})

                        fdn = sheet.cell(row, 3).value
                        if not fdn:
                            cl_r_fdn = sheet.cell(0, 3).value
                            self.env.cr.rollback()
                            raise Exception("One of the %s is missing, Please review the file." % (cl_r_fdn))
                        try:
                            fdn = int(fdn)
                        except:
                            fdn = sheet.cell(row, 3).value

                        dt.update({'funding_doc_number': fdn})

                        projectname = sheet.cell(row, 4).value
                        if not projectname:
                            self.env.cr.rollback()
                            raise Exception(
                                "Please verify the Project ID's and Import again!")
                        else:
                            try:
                                projectname = int(projectname)
                            except:
                                projectname = sheet.cell(row, 4).value
                            dt.update({'ticl_project_id': projectname})
                        try:
                            tid = sheet.cell(row, 5).value
                            tid = int(tid)
                        except:
                            tid = sheet.cell(row, 5).value
                        dt.update({'tid': tid})

                        cmname = str(sheet.cell(row, 6).value)
                        if "." in cmname[-2:-1]:
                            cmname = cmname.split('.')
                            cmname = cmname[0]
                        if not cmname:
                            cl_r_cmn = sheet.cell(0, 6).value
                            self.env.cr.rollback()
                            raise Exception("One of the %s is missing, Please review the file." % (cl_r_cmn))
                        dt.update({'common_name': cmname})

                        dt.update({
                            'product_id': product.id,
                            'tel_type': product.categ_id.id,
                            'manufacturer_id': product.manufacturer_id.id
                        })
                        dft = sheet.cell(row, 0).value

                        if isinstance(dft, float) == True or isinstance(dft, int) == True:
                            x = datetime(*xlrd.xldate_as_tuple(dft, wb.datemode))
                            sp = str(x).split(' ')
                            dft = sp[0]
                            # print('\n\n\n nnnnnnnnnn',dft)
                            dates = datetime(int(dft[0:4]), int(dft[5:7]), int(dft[-2:]), 00, 00, 00)
                            # print('\n\n',dft)
                            # print('\n\n',int(dft[-4:]), int(dft[:2]), int(dft[3:5]))
                        else:
                            dates = datetime(int(dft[-4:]), int(dft[:2]), int(dft[3:5]), 00, 00, 00)
                        # print('\n\n\n sheet.cell(row, 0).value',dates.strftime("%Y-%m-%d %H:%M:%S"))

                        # print('\n\n\n dft',dft)
                        # split_date =  dft.split('/')
                        # dates = dft[2] +'-'+dft[1]+'-'+dft[0] + '00:00:00'
                        eqpDate = dates
                        # print('\n\n 34567',dates)
                        # eqpDate = datetime.strptime(dates, '%Y-%m-%d %H:%M:%S')
                        # eqpDate = datetime.strptime(dates, "%d/%m/%Y").date()
                        # eqpDate = datetime(*xlrd.xldate_as_tuple(sheet.cell(row, 0).value, wb.datemode))
                        # print('\n\n\n eqpDate',eqpDate)

                        eqpDay, eqpMonth, eqpYr = eqpDate.day, eqpDate.month, eqpDate.year
                        eqp_grp = str(eqpDay) + '_' + str(eqpMonth) + '_' + str(eqpYr)

                        required_delivery_date = datetime(eqpYr, eqpMonth, eqpDay) - timedelta(days=7)
                        print('\n\n\n\n88888',required_delivery_date)

                        if required_delivery_date < datetime.today():
                            required_delivery_date = datetime.today()

                        today_day = (datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ).weekday() + 1) % 7
                        if today_day in [0, 1, 2, 3]:
                            pick_up_date_new = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=2)
                        elif today_day in [4, 5]:
                            pick_up_date_new = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=4)
                        elif today_day in [6]:
                            pick_up_date_new = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=3)

                        # today_day = (datetime.today().weekday() + 1) % 7
                        # if today_day in [0, 1, 2, 3]:
                        #     pick_up_date = datetime.today() + timedelta(days=2)
                        # elif today_day in [4, 5]:
                        #     pick_up_date = datetime.today() + timedelta(days=4)
                        # elif today_day in [6]:
                        #     pick_up_date = datetime.today() + timedelta(days=3)
                        activity_date_new = eqpDate.strftime("%Y-%m-%d")

                        dt.update({'activity_date': eqpDate.strftime("%Y-%m-%d %H:%M:%S"), 'eqp_grp': eqp_grp})
                        eqpDtTime = eqpDate.strftime("%Y-%m-%d %H:%M:%S")
                        shipment_type = 'Regular'
                        vals.update({
                            # 'activity_date': eqpDtTime,
                            'shipment_types': shipment_type,
                            #'required_delivery_date': required_delivery_date,
                            'delivery_date_new': required_delivery_date,
                            'pick_up_date_new': pick_up_date_new,
                            'activity_date_new': eqpDate.strftime("%Y-%m-%d"),

                        })
                        # get warehouse key
                        rcv_loc = str(sheet.cell(row, 8).value).strip()
                        if not rcv_loc:
                            raise Exception("One of the Ship From is missing, Please review the file.")

                        if rcv_loc:
                            rcv_location = self.env['res.partner'].sudo().search([
                                ('name', '=', rcv_loc)], limit=1)
                            if location == rcv_location.id:
                                vals.update({'sending_location_id': rcv_location.id})
                                warehouse_name = str(sheet.cell(row, 7).value).strip()
                                serial_number = str(sheet.cell(row, 1).value).strip()
                                if not warehouse_name and not serial_number:
                                    raise Exception("One of the Ship From is missing, Please review the file.")
                                # if product.categ_id.name == 'ATM':
                                #     raise Exception("Ship Equip from is not required for ATM(s). Please review the file and upload again!")
                                if product.categ_id.name == 'ATM' and not serial_number:
                                    raise Exception("Serial number is required for ATM(s), Please review the file and upload again!")
                                if warehouse_name:
                                    ware_name = float(warehouse_name)
                                    origin_location = self.env['stock.location'].sudo().search([
                                        ('warehouse_key', '=', int(ware_name))], limit=1).id
                                    # origin_location = self.env['stock.location'].sudo().search([
                                    #     ('name', '=', warehouse_name),
                                    #     ('state', '!=', False)], limit=1)

                                    dict_ky = str(rcv_location.id) + '_' + str(origin_location)
                                    print(dict_ky)
                                    if not serial_number:
                                        qty = sheet.cell(row, 10).value
                                        if not qty:
                                            raise Exception("One of the Quantity is missing, Please review the file.")
                                        moves = self.env['stock.move.line'].sudo().search([
                                            ('product_id', '=', product.id),
                                            ('status', '=', 'inventory'),
                                            ('condition_id', '!=', condition.id),
                                            ('ticl_warehouse_id', '=', origin_location)], limit=int(qty))

                                        if moves:
                                            if len(moves) >= int(qty):
                                                for move in moves:
                                                    dt.update({'tel_available': 'Y'})
                                                    if dict_ky in warehouse_vals:
                                                        ware_lst = warehouse_vals.get(dict_ky)
                                                        dt.update({'move_id': move.id})
                                                        ware_lst.append(dt)
                                                        warehouse_vals.update({dict_ky: ware_lst})
                                                        move.status = 'assigned'
                                                    else:
                                                        dt.update({'move_id': move.id})
                                                        warehouse_vals.update({dict_ky: [dt]})
                                                        move.status = 'assigned'

                                            elif len(moves) < int(qty):
                                                x_vals = vals.copy()
                                                for move in moves:
                                                    dt.update({'tel_available': 'Y'})
                                                    if dict_ky in warehouse_vals:
                                                        ware_lst = warehouse_vals.get(dict_ky)
                                                        dt.update({'move_id': move.id})
                                                        ware_lst.append(dt)
                                                        warehouse_vals.update({dict_ky: ware_lst})
                                                        move.status = 'assigned'
                                                    else:
                                                        dt.update({'move_id': move.id})
                                                        warehouse_vals.update({dict_ky: [dt]})
                                                        move.status = 'assigned'

                                                warehouse_list = []
                                                loop_qty = int(qty) - len(moves)
                                                for i in range(loop_qty):
                                                    x_dt = dt.copy()
                                                    x_dt.update({'tel_available': 'N'})
                                                    warehouse_list.append((0, 0, x_dt))
                                                x_vals.update({'ticl_ship_lines': warehouse_list,
                                                               'receiving_location_id': origin_location})
                                                
                                                dat = datetime.strptime(vals['activity_date_new']+" 00:00:00", '%Y-%m-%d %H:%M:%S')

                                                vals['delivery_date_new'] = dat - timedelta(days=7)
                                                today_day = (datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ).weekday() + 1) % 7
                                                if today_day in [0, 1, 2, 3]:
                                                    vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=2)
                                                elif today_day in [4, 5]:
                                                    vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' )+ timedelta(days=4)
                                                elif today_day in [6]:
                                                    vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=3)
                                                ship_log = self.env['ticl.shipment.log.ext'].create(x_vals)
                                        else:
                                            warehouse_list = []
                                            for i in range(int(qty)):
                                                dt.update({'tel_available': 'N'})
                                                warehouse_list.append((0, 0, dt))
                                            vals.update({'ticl_ship_lines': warehouse_list,
                                                         'receiving_location_id': origin_location})

                                            dat = datetime.strptime(vals['activity_date_new']+" 00:00:00", '%Y-%m-%d %H:%M:%S')

                                            vals['delivery_date_new'] = dat - timedelta(days=7)
                                            today_day = (datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ).weekday() + 1) % 7
                                            if today_day in [0, 1, 2, 3]:
                                                vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=2)
                                            elif today_day in [4, 5]:
                                                vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=4)
                                            elif today_day in [6]:
                                                vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=3)

                                            ship_log = self.env['ticl.shipment.log.ext'].create(vals)

                                if not warehouse_name:
                                    if not serial_number:
                                        cl_r_srl = sheet.cell(0, 1).value
                                        self.env.cr.rollback()
                                        raise Exception(
                                            "One of the %s is missing, Please review the file." % (cl_r_srl))
                                if serial_number:
                                    if "." in serial_number:
                                        ser_number_lst = serial_number.split('.')
                                        serial_number = ser_number_lst[0]
                                    dt.update({'serial_number': str(serial_number)})
                                    if not warehouse_name:
                                        move = self.env['stock.move.line'].sudo().search([
                                            ('product_id', '=', product.id),
                                            ('status', '=', 'inventory'),
                                            ('serial_number', '=', serial_number)
                                        ], limit=1)
                                    else:
                                        move = self.env['stock.move.line'].sudo().search([
                                            ('product_id', '=', product.id),
                                            ('status', '=', 'inventory'),
                                            ('serial_number', '=', serial_number),
                                            ('ticl_warehouse_id', '=', origin_location)
                                        ], limit=1)

                                    if warehouse_name and not move:
                                        dict_ky = str(rcv_location.id) + '_' + str(origin_location)
                                        vals.update({'receiving_location_id': origin_location})
                                    if move:
                                        if move.condition_id.name == 'Quarantine':
                                            raise Exception("ATM %s is in quarantine state,So can not be Shipped !" % (
                                                serial_number))

                                        dict_ky = str(rcv_location.id) + '_' + str(move.location_dest_id.id)
                                        dt.update({'tel_available': 'Y'})
                                        if dict_ky in warehouse_vals:
                                            ware_lst = warehouse_vals.get(dict_ky)
                                            dt.update({'move_id': move.id})
                                            ware_lst.append(dt)
                                            warehouse_vals.update({dict_ky: ware_lst})
                                            # move.status = 'assigned'
                                        else:
                                            dt.update({'move_id': move.id})
                                            warehouse_vals.update({dict_ky: [dt]})
                                            # move.status = 'assigned'
                                    else:
                                        warehouse_list = []
                                        dt.update({'tel_available': 'N'})
                                        warehouse_list.append((0, 0, dt))
                                        vals.update({'ticl_ship_lines': warehouse_list})
                                        dat = datetime.strptime(vals['activity_date_new']+" 00:00:00", '%Y-%m-%d %H:%M:%S')
                                        vals['delivery_date_new'] = dat - timedelta(days=7)
                                        today_day = (datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ).weekday() + 1) % 7
                                        if today_day in [0, 1, 2, 3]:
                                            vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=2)
                                        elif today_day in [4, 5]:
                                            vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=4)
                                        elif today_day in [6]:
                                            vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=3)
                                        ship_log = self.env['ticl.shipment.log.ext'].create(vals)

                    if warehouse_vals:
                        print('warehouse------------------', warehouse_vals)
                        # print('values------------------', warehouse_vals)
                        for ware in warehouse_vals.keys():
                            lst = []
                            act_date = []
                            eqp_dict = {}
                            for data in warehouse_vals.get(ware):
                                #                                 warehouse_list.append((0,0,data))
                                if data.get('eqp_grp') in eqp_dict:
                                    eqp_lst = eqp_dict.get(data.get('eqp_grp'))
                                    eqp_lst.append(data)
                                else:
                                    eqp_dict.update({data.get('eqp_grp'): [data]})
                                act_date.append(data['activity_date'])
                            for eqp_key in eqp_dict.keys():
                                warehouse_list = []
                                for tender_data in eqp_dict.get(eqp_key):
                                    lst.append((0, 0, tender_data))
                                    shipment_type = 'Regular'
                                    vals.update({'shipment_types': shipment_type})
                            print('\n\n\n datesssss', act_date)
                            act_date.sort(key = lambda date: datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
                            # print('\n\n\n 234567',act_date)
                            spilt_lst = ware.split('_')
                            vals.update({
                                'receiving_location_id': origin_location,
                                'ticl_ship_lines': lst,
                                'activity_date' : act_date[0]
                            })
                            b = str(vals['activity_date'])
                            import dateutil.parser
                            d = dateutil.parser.parse(b).date()
                            vals['activity_date_new'] = d
                            dat = datetime.strptime(vals['activity_date'], '%Y-%m-%d %H:%M:%S')

                            vals['delivery_date_new'] = dat - timedelta(days=7)
                            today_day = (datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ).weekday() + 1) % 7
                            if today_day in [0, 1, 2, 3]:
                                vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=2)
                            elif today_day in [4, 5]:
                                vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=4)
                            elif today_day in [6]:
                                vals['pick_up_date_new'] = datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S' ) + timedelta(days=3)
                            del vals['activity_date']
                            ship_log = self.env['ticl.shipment.log.ext'].create(vals)
                            ship_log.picked_shipment_log_ext()
            #                         vals.update({'receiving_location_id':int(ware)})
            # # avl_shp = self.env['ticl.shipment.log.ext'].create(vals)
            # #avl_shp.picked_shipment_log_ext()
            # if lst:
            #     vals.update({'ticl_ship_lines':lst})
            #     ship_log = self.env['ticl.shipment.log.ext'].create(vals)
            #     pending = ship_log.ticl_ship_lines.filtered(lambda p: p.tel_available == 'N')
            #     if not pending:
            #         pass
            #     else:
            #         ship_log.picked_shipment_log_ext()
            #     lst = []
            # else:
            #     avl_shp.picked_shipment_log_ext()
            #     if avl_shp.state == 'approved':
            #         for ticl_ship_line in avl_shp.ticl_ship_lines:
            #             move_inv = self.env['stock.move'].search(
            #                 [['serial_number', '=', ticl_ship_line.serial_number],
            #                  ['status', '=', 'inventory']],limit=1)
            #             if move_inv:
            #                 move_inv.status = 'assigned'
            #                 ticl_ship_line.move_id = move_inv.id

            # else:
            #                     vals.update({'ticl_ship_lines':lst})
            #                     if vals['ticl_ship_lines']:
            # valslist.append(vals)
            #                         ship_log = self.env['ticl.shipment.log.ext'].create(vals)
            #                         ship_log.ticl_ship_lines.filtered(lambda p: p.tel_available == 'N')
            # if not pending:
            #     pass
            # else:
            #                         ship_log.picked_shipment_log_ext()
            # if ship_log.state == 'approved':
            #     for ticl_ship_line in ship_log.ticl_ship_lines:
            #         move_inv = self.env['stock.move'].search(
            #             [['serial_number', '=', ticl_ship_line.serial_number],
            #              ['status', '=', 'inventory']],limit=1)
            #         if move_inv:
            #             move_inv.status = 'assigned'
            #             ticl_ship_line.move_id = move_inv.id
            # ship_log = self.env['ticl.shipment.log.ext'].create(valslist)
        except Exception as e:
            self._cr.rollback()
            status = 'n'
            message = str(e)
        return {'message': message, 'status': status}
    

    @api.model
    def shipment_drop_ship_import_ext(self,vals):
        message = 'Dropship Imported Successfully!'
        status = 's'
        try:
            xl = vals.get('file').split(',')
            xlsx_file = xl[1].encode()
            xls_file = base64.decodestring(xlsx_file)
            wb = xlrd.open_workbook(file_contents=xls_file)
            # condition = self.env['ticl.condition'].search([('name', '=', 'Quarantine')])
            data = {}
            out = {}
            x = []
            for sheet in wb.sheets():
                shipFrom_list = sheet.col_values(7)
                if '' in shipFrom_list:
                    raise Exception("Please verify the Ship Equip From and Import again!")
                shipFrom = [elem.strip() for elem in shipFrom_list]
                shipFrom.pop(0)
                shipTo_list = sheet.col_values(8)
                if '' in shipTo_list:
                    raise Exception("Please verify the Ship Equip To and Import again!")
                shipTo = [elem.strip() for elem in shipTo_list]
                shipTo.pop(0)
                for row in range(0,len(shipFrom)):
                    data[row] = [str(shipFrom[row])+'-'+str(shipTo[row])]
            if data != {}:
                for i in data:
                    x.append(data[i][0])
                for i in x:
                    val = i
                    for key, value in data.items():
                        if val == value[0]:
                            if val not in out.keys():
                                out[val] = []
                            out[val].append(key)
            for i in out:
                out[i] = list(set(out[i]))
            vals = {}
            ticl_ship_lines = []
            activity_date = []
            for recs in out:
                location = recs.split('-')
                from_location = self.env['res.partner'].search([('name','=',location[0])],limit=1)
                to_location = self.env['res.partner'].search([('name','=',location[1])],limit=1)
                vals['receiving_location_id'] = from_location.id
                vals['sending_rigger_id'] = to_location.id
                for cols in out[recs]:
                    try:
                        product_name = str(int(sheet.cell(cols+1, 9).value)).strip()
                    except:
                        product_name = str(sheet.cell(cols+1, 9).value).strip()
                    if not product_name:
                        self.env.cr.rollback()
                        raise Exception("Please verify the Models and Import again!")
                    if "." in product_name[-2:-1]:
                        prod_lst = product_name.split('.')
                        product_name = prod_lst[0]
                    product = self.env['product.product'].sudo().search([('name', '=', product_name)], limit=1)
                    condition = sheet.cell(cols+1, 11).value
                    if condition == '':
                        raise Exception("Please verify the Condition and Import again!")
                    count = sheet.cell(cols+1, 10).value
                    if count == '':
                        raise Exception("Please verify Count and Import again!")
                    condition_id = self.env['ticl.condition'].search([('name', '=', condition)])
                    serial_number = str(sheet.cell(cols + 1, 1).value)
                    if serial_number != '':
                        count = 1
                    if "." in serial_number[-2:-1]:
                        serial_number = serial_number.split('.')
                        serial_number = serial_number[0]
                    funding_doc_type = str(sheet.cell(cols + 1, 2).value)
                    if funding_doc_type == '':
                        raise Exception("Please verify the Funding Doc Type and Import again!")
                    if "." in funding_doc_type[-2:-1]:
                        funding_doc_type = funding_doc_type.split('.')
                        funding_doc_type = funding_doc_type[0]
                    funding_doc_number = sheet.cell(cols + 1, 3).value
                    if funding_doc_number == '':
                        raise Exception("Please verify the Funding Doc Number and Import again!")
                    if "." in funding_doc_number[-2:-1]:
                        funding_doc_number = funding_doc_number.split('.')
                        funding_doc_number = funding_doc_number[0]
                    ticl_project_id = str(sheet.cell(cols + 1, 4).value)
                    if ticl_project_id == '':
                        raise Exception("Please verify the Project ID and Import again!")
                    if "." in ticl_project_id[-2:-1]:
                        ticl_project_id = ticl_project_id.split('.')
                        ticl_project_id = ticl_project_id[0]
                    common_name = str(sheet.cell(cols + 1, 6).value)
                    if "." in common_name[-2:-1]:
                        common_name = common_name.split('.')
                        common_name = common_name[0]
                    tid = str(sheet.cell(cols + 1, 5).value)
                    if "." in tid[-2:-1]:
                        tid = tid.split('.')
                        tid = tid[0]
                    lines = (0,0,{'funding_doc_type': funding_doc_type,'serial_number': serial_number,
                             'funding_doc_number': funding_doc_number,'ticl_project_id':ticl_project_id,
                             'tid': tid,
                             'common_name': common_name,'count_number': count,'condition_id': condition_id.id,
                             'product_id': product.id,'tel_type': product.categ_id.id,'manufacturer_id': product.manufacturer_id.id})
                    ticl_ship_lines.append(lines)
                    dft = sheet.cell(cols+1, 0).value
                    if isinstance(dft, float) == True or isinstance(dft, int) == True:
                        x = datetime(*xlrd.xldate_as_tuple(dft, wb.datemode))
                        sp = str(x).split(' ')
                        dft = sp[0]
                        if '/' in dft:
                            x = dft.split('/')
                        elif '-' in dft:
                            x = dft.split('-')
                        dates = datetime(int(x[0]), int(x[1]), int(x[2]), 00, 00, 00)
                        # dates = datetime(int(dft[0:4]), int(dft[-2:]), int(dft[5:7]), 00, 00, 00)
                    else:
                        if '/' in dft:
                            x = dft.split('/')
                        elif '-' in dft:
                            x = dft.split('-')
                        dates = datetime(int(x[2]), int(x[0]), int(x[1]), 00, 00, 00)
                        # dates = datetime(int(dft[-4:]), int(dft[:2]), int(dft[3:5]), 00, 00, 00)
                    eqpDate = str(dates).split(" ")
                    eqpDate = eqpDate[0].split("-")
                    eqpDay, eqpMonth, eqpYr = int(eqpDate[2]), int(eqpDate[1]), int(eqpDate[0])
                    act_date = datetime(eqpYr, eqpMonth, eqpDay)
                    print('\n\n\n act_date',act_date,'act_date \n\n\n')
                    activity_date.append(act_date.date().strftime("%m/%d/%Y"))

                activity_date.sort()
                vals['activity_date_new'] = activity_date[0]
                import dateutil.parser
                d = dateutil.parser.parse(vals['activity_date_new']).date()
                vals['activity_date_new'] = d
                dat = datetime.strptime(str(activity_date[0])+ ' 00:00:00', '%m/%d/%Y %H:%M:%S')
                vals['delivery_date_new'] = dat - timedelta(days=7)
                today_day = (datetime.strptime(str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00",
                                               '%Y-%m-%d %H:%M:%S').weekday() + 1) % 7
                if today_day in [0, 1, 2, 3]:
                    vals['pick_up_date_new'] = datetime.strptime(
                        str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S') + timedelta(
                        days=2)
                elif today_day in [4, 5]:
                    vals['pick_up_date_new'] = datetime.strptime(
                        str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S') + timedelta(
                        days=4)
                elif today_day in [6]:
                    vals['pick_up_date_new'] = datetime.strptime(
                        str(real_datetime.datetime.today()).split(' ')[0] + " 00:00:00", '%Y-%m-%d %H:%M:%S') + timedelta(
                        days=3)
                vals['ticl_ship_lines'] = ticl_ship_lines
                # ship_id = self.env['ticl.shipment.log'].search([],order="id desc",limit=1)
                # last_ship_name = ship_id.name.split('/')
                # new_ship_name = int(last_ship_name[1]) + 1
                # vals['name'] = 'SM/'+str(new_ship_name)
                vals['shipment_types'] = 'Regular'
                ship_log = self.env['ticl.shipment.log.ext.drop'].create(vals)
                ship_log.picked_shipment_log_ext_drop()
                activity_date = []
                vals ={}
                ticl_ship_lines = []
        except Exception as e:
            self._cr.rollback()
            status = 'n'
            message = str(e)
        return {'message': message, 'status': status}

    
