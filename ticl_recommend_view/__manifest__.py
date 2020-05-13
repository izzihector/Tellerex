###################################################################################
#    Created By Delaplex
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
###################################################################################

{
    "name": "TICL Recommend Views",
    "summary": """TICL Recommend Views""",
    "version": '12.0',
    "license": "AGPL-3",
    "website": "http://www.delaplex.in",
    "author": "Delaplex",
    "contributors": ["Delaplex Team"],
    "depends": ['ticl_receiving','web'],
    "data": ['security/ir.model.access.csv',
             'views/ticl_recommend_view.xml',
             'views/template.xml',
             ],
    "demo": [
    ],
    'qweb': ['static/xml/export_file.xml'],
    'images': [],
    "application": True,
    "installable": True,
}
