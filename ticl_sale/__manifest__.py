###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Sales", 
    "summary": """TICL Sales Management""",
    "version": '12.0',   
    "category": 'TICL Sales Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'product', 'sale_management','sale','sale_stock','stock','purchase','account','ticl_management'],
    "data": [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        # 'data/product_demo.xml',
        'views/ticl_sale_view.xml',
        'views/ticl_account_invoice_view.xml',
        'report/ticl_sales_report.xml',
        'report/ticl_sales_report_view.xml',
        'views/ticl_sale_contract_view.xml',
        'views/monthly_service_charge.xml',

    ],
    "demo": [
    ],
    "qweb": [
    ],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
