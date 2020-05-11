###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Shipment", 
    "summary": """TICL Shipment""",
    "version": '12.0',   
    "category": 'Shipment with Inventory Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'stock', 'product', 'ticl_management','ticl_receiving'],
    "data": [
        'security/ticl_shipment_security.xml',
        'security/ir.model.access.csv',
        'security/ticl_shipment_sequence_view.xml',
        'views/res_config_view.xml',
        'views/ticl_shipment_service_charge_view.xml',
        'views/ticl_shipment_log.xml',
        'views/ticl_add_pallet_view.xml',
        'views/template.xml',
        'views/ticl_shipment_api_cron.xml',
        #'report/paper_format.xml',
        # 'report/delivery_report.xml',
        # 'report/pending_report.xml', 
        # 'report/pending_shipment_report.xml',
        # 'report/shipping_picking_operations_pdf.xml',
        #'wizards/inventory_scrap.xml',


    ],
    "demo": [
    ],
    'qweb': ['static/src/xml/shippment.xml'],
    'images': ['static/description/icon.jpg'],
    "application": True,
    "installable": True,
}
