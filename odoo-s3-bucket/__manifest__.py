# -*- coding: utf-8 -*-
{
    'name': "odoo-s3",

    'summary': """
        Stores attachments in Amazon S3 instead of the local drive""",

    'description': """
        In large deployments, Odoo workers need to share a distributed
        filestore. Amazon S3 can store files (e.g. attachments and
        pictures), such that all Odoo workers can access the same files.

        This module lets you configure access to an S3 bucket from Odoo,
        by settings a System parameter.
    """,

    'author': "Delaplex",
    'website': "delaplex.com",
    'category': 'Technical Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web','ticl_management','ticl_receiving'],

    # only the admin user should be having access -so default is ok
    'data': [
         'ticl_s3_bucket_image_view.xml',
         'assets_backend.xml',

    ],
    'qweb' : [
            'static/src/xml/many2many_extend.xml',
            'static/src/xml/s3_image.xml',
            'static/src/xml/s3_image_epp.xml',
            'static/src/xml/s3_image_hdd.xml',
    ],
}
