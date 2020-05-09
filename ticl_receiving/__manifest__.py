###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL ASN Receiving", 
    "summary": """TICL ASN Receiving Management""",
    "version": '12.0',   
    "category": 'ASN with Inventory Management',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'base', 'mail', 'stock', 'product', 'ticl_management'],
    "data": [
        'data/cod_paper.xml',
        'security/ticl_asn_security.xml',
        'security/ir.model.access.csv',
        'views/ticl_service_charge_view.xml',
        'views/ticl_receipt_view.xml',
        'views/ticl_receipt_log_summary_view.xml',
        'views/tel_stock_location_view.xml',
        'views/tel_receving_stock_view.xml',
        'views/tel_dashboard_view.xml',
	    'views/placard_label_ganaret_view.xml',
        'views/cod_report.xml',
        'security/tel_sequence_view.xml',
        #'views/stock_notification.xml',
        'report/cod_report_pdf.xml',
        'views/refurbishment_charges_views.xml',
        'views/ticl_location_view.xml',
        'views/ticl_receipt_api_cron.xml',
        'views/template.xml',
        'views/ticl_stock_move_line_view.xml',
        'report/receiving_picking_operations_pdf.xml',


    ],
    "demo": [
    ],
    'qweb': [],
    'images': ['static/description/icon.png'],
    "application": True,
    "installable": True,
}
