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

class SaleOrderCancel(models.TransientModel):
    _name = 'ticl.receipt.cancel'
    _description = __doc__


    ticl_cancel_reason = fields.Char(string="Cancel Reason Shipment")


    #@api.multi
    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        receipt_ids = self._context.get('active_ids')
        if receipt_ids is None:
            return act_close
        assert len(receipt_ids) == 1, "Only 1 sale ID expected"
        receipt = self.env['ticl.receipt'].browse(receipt_ids)
        receipt.ticl_cancel_reason = self.ticl_cancel_reason

        #LTL Shipment Cancel API
        # if int(receipt.total_pallet) < 13 and int(receipt.total_weight) < 20000 and receipt.echo_call == 'yes' and receipt.shipment_status != 'CANCELLED':
        #     complex_object = OrderedDict()
        #     complex_object['Origin'] = OrderedDict()
        #     complex_object['Destination'] = OrderedDict()
        #     complex_object['Origin']['LocationType'] = "BUSINESS"
        #     complex_object['Origin']['LocationName'] = receipt.sending_location_id.name or ""
        #     complex_object['Origin']['AppointmentDate'] = receipt.pickup_date.strftime('%m/%d/%Y') or ""
        #     complex_object['Origin']['AppointmentStart'] = "13:59"
        #     complex_object['Origin']['AppointmentEnd'] = "14:59"
        #     complex_object['Origin']['AddressLine1'] = receipt.sending_location_id.street or ""
        #     complex_object['Origin']['AddressLine2'] = receipt.sending_location_id.street2 or ""
        #     complex_object['Origin']['City'] = receipt.sending_location_id.city_id.name or ""
        #     complex_object['Origin']['StateProvince'] = receipt.sending_location_id.state_id.code or ""
        #     complex_object['Origin']['PostalCode'] = receipt.sending_location_id.zip or ""
        #     complex_object['Origin']['CountryCode'] = "US"
        #     complex_object['Origin']['ContactName'] = receipt.sending_location_id.contact_name or ""
        #     complex_object['Origin']['ContactPhone'] = receipt.sending_location_id.phone or ""
        #     complex_object['Origin']['BolNumber'] = "0000000000"
        #     complex_object['Origin']['ReferenceNumber'] = "OriginReferenceNumber"
        #     complex_object['Origin']['Accessorials'] = []
        #     #Destination data
        #     complex_object['Destination']['LocationType'] = "BUSINESS"
        #     complex_object['Destination']['LocationName'] = receipt.receiving_location_id.name or ""
        #     complex_object['Destination']['AppointmentDate'] = receipt.echo_estimated_delivery_date.strftime('%m/%d/%Y') or ""
        #     complex_object['Destination']['AppointmentStart'] = "13:59"
        #     complex_object['Destination']['AppointmentEnd'] = "14:59"
        #     complex_object['Destination']['AddressLine1'] = receipt.receiving_location_id.warehouse_id.street or ""
        #     complex_object['Destination']['AddressLine2'] = receipt.receiving_location_id.warehouse_id.street2 or ""
        #     complex_object['Destination']['City'] = receipt.receiving_location_id.warehouse_id.city_id.name or ""
        #     complex_object['Destination']['StateProvince'] = receipt.receiving_location_id.warehouse_id.state_id.code or ""
        #     complex_object['Destination']['PostalCode'] = receipt.receiving_location_id.warehouse_id.zip_code or ""
        #     complex_object['Destination']['CountryCode'] = "US"
        #     complex_object['Destination']['ContactName'] = receipt.receiving_location_id.warehouse_id.contact_name or ""
        #     complex_object['Destination']['ContactPhone'] = receipt.receiving_location_id.warehouse_id.warehouse_phone or ""
        #     complex_object['Destination']['BolNumber'] = "0000000000"
        #     complex_object['Destination']['ReferenceNumber'] = "ReferenceNumber"
        #     complex_object['Destination']['Accessorials'] = []
        #     #Product Item
        #     complex_object['Items'] = []
        #     for line in receipt.ticl_receipt_lines:
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
        #     complex_object['PalletQuantity'] = receipt.total_pallet or ""
        #     complex_object['PalletType'] = "PalletType"
        #     complex_object['PalletStackable'] = False
        #     complex_object['SkidSpotQuantity'] = 1
        #     complex_object['UnitOfWeight'] = "LB"
        #     complex_object['CustomerNotes'] = "10/17/2019"
        #     complex_object['ShipmentNotes'] = "AddressLine1"
        #     complex_object['CarrierSCAC'] = "AddressLine2"
        #     complex_object['CarrierGuarantee'] = "US"
        #     complex_object['QuoteId'] = "United state"
        #     complex_object['BolNumber'] = receipt.bill_of_lading_number or ''
        #     complex_object['OrderNumber'] = "CountryCode"
        #     complex_object['PoNumber'] = "ContactName"
        #     complex_object['ProNumber'] = "ProNumber"
        #     complex_object['PodSignature'] = "PodSignature"
        #     complex_object['GlCode'] = "ReferenceNumber"
        #     complex_object['AckNotification'] = "ssingh@delaplex.in"
        #     complex_object['AsnNotification'] = "ssingh@delaplex.in"

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
        #                 receipt.state = 'cancel'
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
        #         if receipt.is_error:
        #             raise Warning(_(warning_message))

        if int(receipt.total_pallet) < 13 and int(receipt.total_weight) < 20000 and receipt.echo_call == 'yes' and receipt.shipment_status != 'CANCELLED':
            print("===TL====")
            receipt.state = 'cancel'
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

        elif (int(receipt.total_pallet) > 12 and int(receipt.total_pallet) < 21) or (int(receipt.total_weight) > 19999 and int(receipt.total_weight) < 45001) and receipt.echo_call == 'yes':
            print("===TL====")
            receipt.state = 'cancel'
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

        elif receipt.echo_call == 'yes' and receipt.shipment_status == 'CANCELLED':
            receipt.state = 'cancel'
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Receipt cancelled successfully!"
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

        elif receipt.echo_call == 'no':
            receipt.state = 'cancel'
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or False
            context = dict(self._context or {})
            context['message'] = "Receipt cancelled successfully!"
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
