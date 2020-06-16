# -*- coding: utf-8 -*-

##############################################################################
#
#    delaplex Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.delaplex.com>).
#    Author: Sayooj A O (<https://www.delaplex.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Rigger Arrival Reports',
    'version': '12.0.1.0.0',
    'summary': 'Rigger Arrival Reports',
    'description': 'Rigger Arrival Reports will be sent automatically.',
    'author': 'delaplex',
    'maintainer': 'delaplex',
    'company': 'delaplex',
    'website': 'https://www.delaplex.com',
    'depends': ['web', 'base', 'mail', 'stock','ticl_management','ticl_shipment','ticl_wh_user_notification','ticl_user_management'],
    'category': 'Shipment with Inventory Management',
    'demo': [],
    'data': ['security/ir.model.access.csv',
             'views/ticl_rigger_template_view.xml',
             'views/email_view.xml',
             'views/rigger_report_chron.xml'],
    'installable': True,
    'images': [''],
    'qweb': [],
    'license': 'AGPL-3',
}
