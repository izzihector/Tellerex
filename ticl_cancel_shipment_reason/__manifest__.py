###################################################################################
# Created By Delaplex
###################################################################################
{
    'name': 'Ticl Cancel Reason',
    'version': '12.0.1.0.0',
    'author': 'Delaplex Team',
    'category': 'Inbound/Outbound',
    'license': 'AGPL-3',
    'complexity': 'normal',
    'website': "http://www.delaplex.in",
    'depends': ['ticl_receiving','ticl_shipment',],
    'data': [
        'wizard/ticl_cancel_reason_view.xml',
        'wizard/ticl_cancel_reason_shipment_view.xml',
        'wizard/ticl_cancel_reason_scrap_view.xml',
        'view/ticl_receiving_cancel_view.xml',
        'view/ticl_shipment_cancel_view.xml',
        'view/ticl_scrap_cancel_view.xml',
    ],
    'auto_install': False,
    'installable': True,
}
