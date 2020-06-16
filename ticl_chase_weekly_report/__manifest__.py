# -*- coding: utf-8 -*-

{
    'name': 'Ticl Chase Weekly Report',
    'version': '1.0',
    'category': 'Inventory',
    'summary': '''
        Print Chase Weekly Report for previous weeks.
        ''',
    'author': 'delaplex',
    'license': "OPL-1",
    'support': 'delaplex.com',
    'depends': ['stock', 'ticl_management','ticl_receiving','ticl_user_management'],
    'data': [
        'security/ticl_menu_security.xml',
        'security/ir.model.access.csv',
        'wizard/chase_weekly_report.xml',
        'wizard/ticl_report_type_view.xml',
        'wizard/rigger_arrivals_report.xml',
        'wizard/ticl_recommend_report.xml',
    ],
    'demo': [],
    'images': [],
    'auto_install': False,
    'installable': True,
    'application': True
}
