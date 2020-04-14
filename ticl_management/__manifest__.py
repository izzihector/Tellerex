###################################################################################
# 
#    Created By Delaplex
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Project", 
    "summary": """TICL Project Management""",
    "version": '12.0.2.5.14',   
    "category": 'Inventory Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": [
        "Delaplex Team",
    ],
    "depends": ['web', 'base', 'mail', 'stock', 'product','hr'],
    "data": [
        'security/ticl_security.xml',
        'security/ir.model.access.csv',
        'views/ticl_order_view.xml',
        'views/ticl_warehouse_view.xml',
        'views/menufacturer_order_view.xml',
        'views/res_user_view.xml',
        'views/ticl_config_view.xml',
        'views/product_view.xml',
        'views/res_partner_view.xml',
        'views/ticl_condition_view.xml',
        'views/stock_location_view.xml',
#         'views/ticl_stock_view.xml',
        'views/rigger_address_view.xml',
        'views/tel_serial_number_view.xml',
        'security/hide_db_link.xml',
	    'views/shipping_carrier_view.xml',
#         'views/employee_details_view.xml',
        'views/template.xml',
        'views/ticl_epp_manufacturer_view.xml',
        'views/ticl_hdd_manufacturer_view.xml',
#         'wizards/update_inventory_entries.xml',
#         'wizards/update_inventory_model.xml'
    ],
    "demo": [
    ],
    "qweb": ['static/src/xml/remove_discard.xml'],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
