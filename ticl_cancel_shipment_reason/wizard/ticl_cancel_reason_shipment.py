import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning
import threading
import urllib3
import json
import requests
import logging
from datetime import datetime, timedelta
from collections import OrderedDict

_logger = logging.getLogger(__name__)

class TiclShipmentCancel(models.TransientModel):
    _name = 'ticl.shipment.cancel'
    _description = __doc__


    ticl_cancel_reason = fields.Char(string="Cancel Reason Shipment")


    #@api.multi
    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        shipment_ids = self._context.get('active_ids')
        if shipment_ids is None:
            return act_close
        assert len(shipment_ids) == 1, "Only 1 sale ID expected"
        shipment = self.env['ticl.shipment.log'].browse(shipment_ids)
        shipment.ticl_cancel_reason = self.ticl_cancel_reason

        #LTL Shipment Cancel API
        # if int(shipment.total_pallet) < 13 and int(shipment.total_weight) < 20000 and shipment.echo_call == 'yes' and shipment.shipment_status != 'CANCELLED':
            
        #     for ids in shipment.ticl_ship_lines:
        #         ids.ship_stock_move_id.write({'status': 'inventory','shipment_id':''})
        #     complex_object = OrderedDict()
        #     complex_object['Origin'] = OrderedDict()
        #     complex_object['Destination'] = OrderedDict()
        #     complex_object['Origin']['LocationType'] = "BUSINESS"
        #     complex_object['Origin']['LocationName'] = shipment.sending_location_id.name or ""
        #     complex_object['Origin']['AppointmentDate'] = shipment.appointment_date_new.strftime('%m/%d/%Y') or ""
        #     complex_object['Origin']['AppointmentStart'] = "13:59"
        #     complex_object['Origin']['AppointmentEnd'] = "14:59"
        #     complex_object['Origin']['AddressLine1'] = shipment.sending_location_id.street or ""
        #     complex_object['Origin']['AddressLine2'] = shipment.sending_location_id.street2 or ""
        #     complex_object['Origin']['City'] = shipment.sending_location_id.city.name or ""
        #     complex_object['Origin']['StateProvince'] = shipment.sending_location_id.state.code or ""
        #     complex_object['Origin']['PostalCode'] = shipment.sending_location_id.zip or ""
        #     complex_object['Origin']['CountryCode'] = "US"
        #     complex_object['Origin']['ContactName'] = "OriginContactName"
        #     complex_object['Origin']['ContactPhone'] = shipment.sending_location_id.phone or ""
        #     complex_object['Origin']['BolNumber'] = "0000000000"
        #     complex_object['Origin']['ReferenceNumber'] = "OriginReferenceNumber"
        #     complex_object['Origin']['Accessorials'] = ["LIFTGATEREQUIRED", "INSIDEPICKUP", "HAZARDOUSMATERIALS", "LIMITEDACCESSFEE", "SINGLESHIPMENT", "PROTECTFROMFREEZING", "EXTREMELENGTH"]
        #     #Destination data
        #     complex_object['Destination']['LocationType'] = "BUSINESS"
        #     complex_object['Destination']['LocationName'] = shipment.receiving_location_id.name or ""
        #     complex_object['Destination']['AppointmentDate'] = shipment.appointment_date.strftime('%m/%d/%Y') or ""
        #     complex_object['Destination']['AppointmentStart'] = "13:59"
        #     complex_object['Destination']['AppointmentEnd'] = "14:59"
        #     complex_object['Destination']['AddressLine1'] = shipment.receiving_location_id.street or ""
        #     complex_object['Destination']['AddressLine2'] = shipment.receiving_location_id.street2 or ""
        #     complex_object['Destination']['City'] = shipment.receiving_location_id.city.name or ""
        #     complex_object['Destination']['StateProvince'] = shipment.sending_location_id.state.code or ""
        #     complex_object['Destination']['PostalCode'] = shipment.sending_location_id.zip or ""
        #     complex_object['Destination']['CountryCode'] = "US"
        #     complex_object['Destination']['ContactName'] = "ContactName"
        #     complex_object['Destination']['ContactPhone'] = shipment.sending_location_id.phone or ""
        #     complex_object['Destination']['BolNumber'] = "0000000000"
        #     complex_object['Destination']['ReferenceNumber'] = "ReferenceNumber"
        #     complex_object['Destination']['Accessorials'] = ["LIFTGATEREQUIRED", "INSIDEPICKUP", "HAZARDOUSMATERIALS", "LIMITEDACCESSFEE", "SINGLESHIPMENT", "PROTECTFROMFREEZING", "EXTREMELENGTH"]
        #     #Product Item
        #     complex_object['Items'] = []
        #     for line in shipment.ticl_ship_lines:
        #         complex_object['Items'].append(OrderedDict([
        #                 ('ItemId', ""),
        #                 ('Description', line.product_id.name),
        #                 ('NmfcClass', "50"),
        #                 ('NmfcNumber', "100240-0"),
        #                 ('Weight', int(line.product_id.product_weight)),
        #                 ('PackageType', "BAG"),
        #                 ('PackageQuantity', "1"),
        #                 ('HandlingUnitType', "BALES"),
        #                 ('HandlingUnitQuantity', "1"),
        #                 ('HazardousMaterial', False),

        #             ]))
        #     complex_object['PalletQuantity'] = shipment.total_pallet or ""
        #     complex_object['PalletType'] = "PalletType"
        #     complex_object['PalletStackable'] = False
        #     complex_object['SkidSpotQuantity'] = 1
        #     complex_object['UnitOfWeight'] = "LB"
        #     complex_object['CustomerNotes'] = "10/17/2019"
        #     complex_object['ShipmentNotes'] = "AddressLine1"
        #     complex_object['CarrierSCAC'] = "AddressLine2"
        #     complex_object['CarrierGuarantee'] = "US"
        #     complex_object['QuoteId'] = "United state"
        #     complex_object['BolNumber'] = shipment.echo_tracking_id
        #     complex_object['OrderNumber'] = "CountryCode"
        #     complex_object['PoNumber'] = "ContactName"
        #     complex_object['ProNumber'] = "ProNumber"
        #     complex_object['PodSignature'] = "PodSignature"
        #     complex_object['GlCode'] = "ReferenceNumber"
        #     complex_object['AckNotification'] = "jb@echo.com;abc@echo.com;abcde@echo.com"
        #     complex_object['AsnNotification'] = "jb@echo.com;abc@echo.com;abcde@echo.com"

        #    # print(complex_object)
        #     double_quote_data = json.dumps((OrderedDict(complex_object)), indent=4)
        #     print("==double_quote_data===",double_quote_data)
        #     # Echo Connection
        #     warning_message = ""
        #     url = "https://prod_int.echo.com/Shipments/LTL/Cancel/Service.svc"
        #     autontication_key = self.env['ir.config_parameter'].sudo().get_param('ticl_shipment.autontication_key')
            
        #     if not autontication_key:
        #         raise Warning(_('Please Add Authontication for Rest API in General Settings.'))
        #     if autontication_key:
        #         headers = {
        #                     'Content-Type': 'application/json',
        #                     'Authorization': autontication_key,
        #                 }
        #         try:
        #             request1 = requests.post(url, data=double_quote_data, headers=headers)
        #             print("===request1===",request1)
        #             #Responce Update in Odoo
        #             if str(request1) != "<Response [200]>" or str(request1) == "<Response [500]>":
        #                 view = self.env.ref('sh_message.sh_message_wizard')
        #                 view_id = view or False
        #                 context = dict(self._context or {})
        #                 context['message'] = "BOL# cancellation request not placed successfully to ECHO!"
        #                 return {
        #                     'name': 'Warning',
        #                     'type': 'ir.actions.act_window',
        #                     'view_type': 'form',
        #                     'view_mode': 'form',
        #                     'res_model': 'sh.message.wizard',
        #                     'view': [('view', 'form')],
        #                     'target': 'new',
        #                     'context': context,
        #                 } 

        #             if str(request1) == "<Response [200]>":
        #                 print("===LTL1111111====")
        #                 shipment.state = 'cancel'
        #                 view = self.env.ref('sh_message.sh_message_wizard')
        #                 view_id = view or False
        #                 context = dict(self._context or {})
        #                 context['message'] = "BOL# cancellation request placed successfully to ECHO!"
        #                 return {
        #                     'name': 'Warning',
        #                     'type': 'ir.actions.act_window',
        #                     'view_type': 'form',
        #                     'view_mode': 'form',
        #                     'res_model': 'sh.message.wizard',
        #                     'view': [('view', 'form')],
        #                     'target': 'new',
        #                     'context': context,
        #                 }

        #         except Exception as e:
        #            _logger.exception('ECHO connection failed')
        #             #raise Warning(_('API Cancel Request was Processed Successfully'))
        #         if shipment.is_error:
        #             raise Warning(_(warning_message))



        if int(shipment.total_pallet) < 13 and int(shipment.total_weight) < 20000 and shipment.echo_call == 'yes' and shipment.shipment_status != 'CANCELLED':
            print("===TL====")
            shipment.state = 'cancel'
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "BOL# cancellation request placed successfully to ECHO!"
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

        elif shipment.echo_call == 'yes' and shipment.shipment_status == 'CANCELLED':
            print("===CANCELLED====")
            for ids in shipment.ticl_ship_lines:
                ids.ship_stock_move_line_id.write({'status': 'inventory','shipment_id':''})

            shipment.state = 'cancel'
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Shipment CANCELLED successfully!"
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


        elif (int(shipment.total_pallet) > 12 and int(shipment.total_pallet) < 21) or (int(shipment.total_weight) > 19999 and int(shipment.total_weight) < 45001) and shipment.echo_call == 'yes':
            print("===TL====")
            for ids in shipment.ticl_ship_lines:
                ids.ship_stock_move_line_id.write({'status': 'inventory','shipment_id':''})

            shipment.state = 'cancel'
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "BOL# cancellation request placed successfully to ECHO!"
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

        elif shipment.echo_call == 'no':
            shipment.state = 'cancel'
            for ids in shipment.ticl_ship_lines:
                ids.ship_stock_move_line_id.write({'status': 'inventory','shipment_id':''})
                            
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Shipment cancelled successfully!"
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
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view  or False
            context = dict(self._context or {})
            context['message']="Please Check This Shipment Is Overloded"
            return{
                 'name':'Warning',
                 'type':'ir.actions.act_window',
                 'view_type':'form',
                 'view_mode':'form',
                 'res_model':'sh.message.wizard',
                 'view':[('view','form')],
                 'target':'new',
                 'context' : context,
            }
        return act_close
