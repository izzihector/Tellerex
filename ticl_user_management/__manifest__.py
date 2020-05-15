###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL User Management", 
    "summary": """TICL User Management""",
    "version": '12.0',   
    "category": 'TICL User Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail','hr', 'stock', 'product', 'ticl_management','ticl_receiving','ticl_shipment'],
    # "depends": ['web', 'base', 'mail','hr', 'stock', 'product', 'ticl_management','ticl_receiving','ticl_shipment','backend_theme_v12'],
    "data": [
            'security/ticl_menu_security.xml',
            'security/ir.model.access.csv',
            #'views/sidebar.xml',
            'views/menu.xml',
     
    ],
    "demo": [],
    'qweb': [],
    'images': [],
    "application": True,
    "installable": True,
}
