# -*- encoding: utf-8 -*-
##############################################################################
#
#    Samples module for Odoo Web Login Screen
##############################################################################
{
    'name': 'Odoo Web Login Screen',
    'summary': 'The new configurable Odoo Web Login Screen',
    'version': '13.0',
    'category': 'Website',
    'summary': """
The new configurable Odoo Web Login Screen
""",
    'author': "Delaplex Team",
    'website': "https://www.delaplex.in",
    'license': 'AGPL-3',
    'depends': ['base','web'],
    'data': [
        'data/ir_config_parameter.xml',
        #'templates/website_templates.xml',
        'templates/webclient_templates.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'images': ['static/description/banner.png'],
}
