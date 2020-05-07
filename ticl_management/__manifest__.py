###################################################################################
#    Created By Delaplex
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
        'views/ticl_warehouse_view.xml',
        'views/menufacturer_order_view.xml',
        'views/res_user_view.xml',
        'views/ticl_config_view.xml',
        'views/product_view.xml',
        'views/res_partner_view.xml',
        'views/ticl_condition_view.xml',
        'views/stock_location_view.xml',
        'views/tel_serial_number_view.xml',
        'security/hide_db_link.xml',
	    'views/shipping_carrier_view.xml',
        'views/template.xml',
        'views/ticl_epp_manufacturer_view.xml',
        'views/ticl_hdd_manufacturer_view.xml',
    ],
    "demo": [
    ],
    "qweb": ['static/src/xml/remove_discard.xml'],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
