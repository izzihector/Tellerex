from odoo import models, api, _
import base64
from datetime import datetime, timedelta
from odoo.exceptions import AccessError
import lxml
import xml.etree.ElementTree as ET
import xlrd


class TiclFreightCharges(models.Model):
    _name = 'freight.charge.import'
    
    
    #Import Shipment freight charges
    @api.model
    def shipment_freight_charge_import(self, vals):
        message = 'Successfully Imported'
        status = 's'
        try:
            xl = vals.get('file').split(',')
            xlsx_file = xl[1].encode()
            xls_file = base64.decodestring(xlsx_file)
            wb = xlrd.open_workbook(file_contents=xls_file)
            for index, sheet in enumerate(wb.sheets()):
                for row in range(sheet.nrows):
                    if sheet.nrows <= 1:
                        raise Exception("Excel sheet is blank, Please review the file.")
                    if sheet.cell(0,0).value != 'BOL #':
                        raise Exception("Excel Template not valid, Please review the file.")
                    if row == 0:
                        continue
                    cell_v = sheet.cell(row,0).value
                    if type(cell_v) is float:  
                        bol = repr(cell_v).split(".")[0]
                    else:
                        bol = cell_v.strip()
                    if bol:
                        shipment = self.env['ticl.shipment.log'].sudo().search([('echo_tracking_id','=',bol)])
                        if len(shipment) > 1:
                            ship_names = shipment.mapped('name')
                            raise Exception("Multiple shipment(%s) found for BOL(%s) , Please review the file."% (ship_names,bol))
                        if shipment:
                            vals = {}
                            total_weight = sheet.cell(row,6).value
                            if not total_weight:
                                raise Exception("Total weight field is blank in row %s , Please review the file."% (row + 1))
                            total_cost = sheet.cell(row,1).value
                            if not total_cost:
                                raise Exception("Total cost field is blank in row %s , Please review the file."% (row + 1))
                            vals.update({'total_echo_cost':total_cost})
                            freight_cost = sheet.cell(row,2).value
                            if not freight_cost:
                                raise Exception("Freight cost field is blank in row %s , Please review the file."% (row + 1))
                            vals.update({'chase_fright_cost':freight_cost})
                            s_type = (sheet.cell(row,9).value).strip()
                            if not s_type:
                                raise Exception("Shipment type field is blank in row %s , Please review the file."% (row + 1))
                            if s_type:
                                if s_type not in ['Regular','Inventory Transfer','Re-Consignment','Guaranteed','Expedited','Non Freight','warehouse_transfer']:
                                    raise Exception("Shipment type not available in row %s , Please review the file."% (row + 1))
                            if s_type == 'warehouse_transfer':
                                s_type = 'Warehouse Transfer'
                            vals.update({'shipment_type':s_type})
                            if s_type in ['Guaranteed','Expedited','Re-Consignment']:
                                approval_authority = sheet.cell(row,3).value
                                if not approval_authority:
                                    raise Exception("Approval authority field is blank in row %s , Please review the file."% (row + 1))
                                vals.update({'approval_authority':approval_authority})
                                approved_date = sheet.cell(row,4).value
                                if not approved_date:
                                    raise Exception("Approval date field is blank in row %s , Please review the file."% (row + 1))
                                if approved_date:
                                    if type(approved_date) is str:  
                                        appr_date = datetime.strptime(approved_date, "%m/%d/%Y")
                                    else:
                                        appr_date = datetime(*xlrd.xldate_as_tuple(approved_date, wb.datemode))
                                    
                                    vals.update({'approved_date':appr_date.strftime("%Y-%m-%d")})
                            miles = sheet.cell(row,7).value
                            if not miles:
                                raise Exception("Miles field is blank in row %s , Please review the file."% (row + 1))
                            if miles:
                                vals.update({'miles':int(miles)})
                            shipment.sudo().write(vals)
                            is_validate = (sheet.cell(row,5).value)
                            if is_validate != '':
                                if type(is_validate) is str:
                                    is_validate = (sheet.cell(row,5).value).lower().strip()
                                else:
                                    is_validate = int(float(sheet.cell(row,5).value))
                            else:
                                raise Exception("Validate field is blank in row %s , Please review the file."% (row + 1))
                            if is_validate == 'yes' or is_validate == int(1):
                                shipment.with_env(self.env(user=self.env.user)).validate_fright_charge()
                            if is_validate not in [True, False, 1.0, 0.0, 1, 0]:
                                raise Exception("Please verify the row %s and Import again!" % (row + 1))
                        else:
                            raise Exception("BOL field is blank in row %s , Please review the file."% (row + 1))
                    else:
                        raise Exception("One of the BOL is missing, Please review the file.")
        except Exception as e:
            msg = str(e)
            message = msg
            status = 'n'
            self.env.cr.rollback()
        return {'message':message,'status':status}
    
    #Import Receipt freight charges
    @api.model
    def receipt_freight_charge_import(self, vals):
        message = 'Successfully Imported'
        status = 's'
        try:
            xl = vals.get('file').split(',')
            xlsx_file = xl[1].encode()
            xls_file = base64.decodestring(xlsx_file)
            wb = xlrd.open_workbook(file_contents=xls_file)
            for index, sheet in enumerate(wb.sheets()):
                for row in range(sheet.nrows):
                    if sheet.nrows <= 1:
                        raise Exception("Excel sheet is blank, Please review the file.")
                    if sheet.cell(0,0).value != 'BOL #':
                        raise Exception("Excel Template not valid, Please review the file.")
                    if row == 0:
                        continue
                    cell_v = sheet.cell(row,0).value
                    if type(cell_v) is float:  
                        bol = repr(cell_v).split(".")[0]
                    else:
                        bol = cell_v.strip()
                    if bol:
                        receipt = self.env['ticl.receipt.log.summary'].sudo().search([('bill_of_lading_number','=',bol)])
                        if len(receipt) > 1:
                            receipt_names = receipt.mapped('name')
                            raise Exception("Multiple receipt(%s) found for BOL(%s) , Please review the file."% (receipt_names,bol))
                        if receipt:
                            vals = {}
                            total_weight = sheet.cell(row,6).value
                            if not total_weight:
                                raise Exception("Total weight field is blank in row %s , Please review the file."% (row + 1))
                            vals.update({'total_weight':total_weight})
                            total_cost = sheet.cell(row,1).value
                            if not total_cost:
                                raise Exception("Total cost field is blank in row %s , Please review the file."% (row + 1))
                            vals.update({'total_cost':total_cost})
                            freight_cost = sheet.cell(row,2).value
                            if not freight_cost:
                                raise Exception("Freight cost field is blank in row %s , Please review the file."% (row + 1))
                            vals.update({'chase_fright_cost':freight_cost})
                            r_type = (sheet.cell(row,9).value).strip()
                            if not r_type:
                                raise Exception("Receipt type field is blank in row %s , Please review the file."% (row + 1))
                            if r_type:
                                if r_type not in ['Regular','Inventory Transfer','Re-Consignment','Guaranteed','Expedited','Non Freight','warehouse_transfer']:
                                    raise Exception("Receipt type not available in row %s , Please review the file."% (row + 1))
                            if r_type == 'warehouse_transfer':
                                r_type = 'Warehouse Transfer'
                            vals.update({'receipt_type':r_type})
                            if r_type in ['Guaranteed','Expedited','Re-Consignment']:
                                approval_authority = sheet.cell(row,3).value
                                if not approval_authority:
                                    raise Exception("Approval authority field is blank in row %s , Please review the file."% (row + 1))
                                vals.update({'approval_authority':approval_authority})
                                approved_date = sheet.cell(row,4).value
                                if not approved_date:
                                    raise Exception("Approval date field is blank in row %s , Please review the file."% (row + 1))
                                if approved_date:
                                    if type(approved_date) is str:  
                                        appr_date = datetime.strptime(approved_date, "%m/%d/%Y")
                                    else:
                                        appr_date = datetime(*xlrd.xldate_as_tuple(approved_date, wb.datemode))
                                    vals.update({'approved_date':appr_date.strftime("%Y-%m-%d")})
                            miles = sheet.cell(row,7).value
                            if not miles:
                                raise Exception("Miles field is blank in row %s , Please review the file."% (row + 1))
                            if miles:
                                vals.update({'miles':int(miles)})
                            receipt.sudo().write(vals)
                            is_validate = (sheet.cell(row,5).value)
                            if is_validate != '':
                                if type(is_validate) is str:
                                    is_validate = (sheet.cell(row,5).value).lower().strip()
                                else:
                                    is_validate = int(float(sheet.cell(row,5).value))
                            else:
                                raise Exception("Validate field is blank in row %s , Please review the file."% (row + 1))

                            if is_validate == 'yes' or is_validate == int(1):
                                receipt.with_env(self.env(user=self.env.user)).validate_fright_charge()
                            if is_validate not in [True, False, 1.0, 0.0, 1, 0]:
                                raise Exception("Please verify the row %s and Import again!" % (row + 1))
                        else:
                            raise Exception("BOL field is blank in row %s , Please review the file."% (row + 1))
                    else:
                        raise Exception("One of the BOL is missing, Please review the file.")
        except Exception as e:
            msg = str(e)
            message = msg
            status = 'n'
            self.env.cr.rollback()
        return {'message':message,'status':status}
