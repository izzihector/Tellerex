###################################################################################
#    Created By Delaplex
###################################################################################

{
    "name": "Freight Charges  Import", 
    "summary": """Freight Charges  Import""",
    "version": '12.0',   
    "category": 'Freight Charges  Import',   
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['web', 'ticl_management','ticl_receiving','ticl_shipment'],
    "data": [
        
        'views/template.xml',
     
    ],
    "demo": [],
    'qweb': ['static/src/xml/freight_charges.xml'],
    'images': ['static/description/icon.jpg'],
    "application": True,
    "installable": True,
}
