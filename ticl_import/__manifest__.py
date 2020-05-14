# -*- coding: utf-8 -*-
{
	'name': 'Import Data from xls',	
	'summary': 'This apps helps to import Data using CSV or Excel file',
	'description': '''Using this module is imported Data using excel sheets''',
	'author': 'Delapelx',	
	'website': 'http://www.delaplex.in',
	'category': 'Stock',
	'version': '12.0.0.2',
	'depends': ['base', 'stock', 'ticl_management'],	
	'data': [
		#'security/ir.model.access.csv',
		'wizard/import_work_order_view.xml',
		],

	'installable': True,
	#'live_test_url'	:'https://youtu.be/ONRtviwfs1s',
    'application': True,
    'qweb': [
    		],
    "images":['static/description/Banner.png']
}

