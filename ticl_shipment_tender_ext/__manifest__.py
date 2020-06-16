###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Outbound Import",
    "summary": """TICL Outbound Import""",
    "version": '12.0',   
    "category": 'Shipment with Inventory Management for external user',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'stock', 'product', 'ticl_management','sh_message'],
    "data": [
        'security/ticl_shipment_security.xml',
        # 'security/menu_access.xml',
        'security/ir.model.access.csv',
        # 'views/ticl_shipment_log.xml',
        'views/ticl_shipment_log.xml',
        'views/drop_ship_import.xml',
        'views/template.xml',

        
     
    ],
    "demo": [],
    'qweb': ['static/src/xml/shipment_tender.xml','static/src/xml/drop_ship.xml'],
    'images': ['static/description/icon.jpg'],
    "application": True,
    "installable": True,
}
