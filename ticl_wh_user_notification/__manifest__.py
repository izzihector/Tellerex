###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Warehouse user notification", 
    "summary": """TICL Warehouse user notification Management""",
    "version": '12.0',   
    "category": 'TICL Warehouse user notification Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'stock','ticl_management','ticl_shipment'],
    "data": [
            'security/ir.model.access.csv',
            'views/ticl_wh_user_notification.xml',
            'views/ticl_warehouse.xml',
            'views/template.xml',
    ],
    "demo": [
    ],
    "qweb": ['static/src/xml/notification.xml'],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
