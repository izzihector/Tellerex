###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICLPurchase", 
    "summary": """TICL Purchase Management""",
    "version": '12.0',   
    "category": 'TICL Purchase Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'product', 'sale_management','sale','sale_stock','stock','purchase','account','ticl_management'],
    "data": [
         'views/ticl_purchase_view.xml',
         'views/ticl_account_invoice_view.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
