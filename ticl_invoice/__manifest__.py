###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Invoices", 
    "summary": """TICL Account Management""",
    "version": '12.0',   
    "category": 'TICL Acounts Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'product', 'sale_management','sale','sale_stock','stock','purchase','account','ticl_management','ticl_receiving'],
    "data": [
        'security/ir.model.access.csv',
        'data/product_demo.xml',
        'views/ticl_invoice_view.xml',
        'views/monthly_service_inv_lines.xml',
        'views/ticl_fright_inv.xml',
        'wizards/invoice.xml',
        
    ],
    "demo": [
    ],
    "qweb": [
    ],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
