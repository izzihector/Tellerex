# -*- coding: utf-8 -*-

{
    'name': 'Ticl Inventory Excel And Pdf Report',
    'version': '1.0',
    'category': 'Inventory',
    'summary': '''
        Prints Inventory Excel And Pdf Report based on start date,end date,both and you can also select
        whether the Inventory state.
        ''',
    'author': 'delaplex',
    'license': "OPL-1",
    'support': 'delaplex.com',
    'depends': ['stock', 'ticl_management','ticl_user_management'],
    'data': [
        # 'wizard/inventory_xls_menu_report_view.xml',
        # 'wizard/stock_summary_report.xml',
        # 'wizard/stock_summary_report_pdf.xml',
        # 'wizard/stock_used_atm_report.xml',
        # 'wizard/stock_used_atm_report_pdf.xml',
        'wizard/sold_item_report_view.xml',
        'wizard/sold_item_report_pdf.xml',
        'wizard/warehouse_shipping_report.xml',
        'wizard/warehouse_shipping_report_pdf.xml',
        # 'wizard/service_charge_report.xml',
        # 'wizard/service_charge_report_pdf.xml'
    ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True
}
