# -*- coding: utf-8 -*-

##############################################################################
#
#    delaplex Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.delaplex.com>).
#    Author: Sayooj A O (<https://www.delaplex.com>)
#
###################################################################################
{
    'name': 'Placards/Labels',
    'version': '12.0.1.0.0',
    'summary': 'Auto Ganarete Placards/Labels',
    'description': 'THis module provide auto Ganarete Placards/Labels format',
    'author': 'delaplex',
    'maintainer': 'delaplex',
    'company': 'delaplex',
    'website': 'https://www.delaplex.com',
    'depends': ['base','web', 'stock', 'ticl_management', 'ticl_receiving'],
    'category': 'Inventory',
    'demo': [],
    'data': [
             'report/placard_label_report.xml',
             'report/placard_label_report_templates.xml',
             'report/placard_label_report_summary_templates.xml'

	    ],
    'installable': True,
    'images': [''],
    'qweb': [],
    'license': 'AGPL-3',
}
