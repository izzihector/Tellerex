###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Scrap Management", 
    "summary": """TICL Scrap Management""",
    "version": '12.0',   
    "category": 'TICL Scrap Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'product', 'sale_management','sale','sale_stock','stock','purchase','account','ticl_management','ticl_receiving','ticl_shipment','ticl_sale'],
    "data": [ 
        'data/recycle_report_format.xml',
        'security/ir.model.access.csv',
        'views/stock_scrap_views.xml',
        'report/recycle_report.xml'
    ],
    "demo": [
    ],
    "qweb": [
    ],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
