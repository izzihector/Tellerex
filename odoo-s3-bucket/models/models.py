# -*- coding: utf-8 -*-
import hashlib
import base64
from odoo import api, fields, models, tools, _
from . import s3_helper

import sys
from PIL import Image
from io import BytesIO
import io

class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _connect_to_S3_bucket(self, s3, bucket_name):
        s3_bucket = s3.Bucket(bucket_name)
        exists = s3_helper.bucket_exists(s3, bucket_name)

        if not exists:
            s3_bucket = s3.create_bucket(Bucket=bucket_name)
        return s3_bucket  


    @api.model_create_multi
    def create(self, vals_list):
        context = dict(self._context or {})
        record_tuple_set = set()
        for values in vals_list:
            context.update({
                'name': values.get('name'),
                'res_model': values.get('res_model'),
                })
            # remove computed field depending of datas
            for field in ('file_size', 'checksum'):
                values.pop(field, False)
            values = self._check_contents(values)
            if 'datas' in values:

                values.update(self.with_context(context)._get_datas_related_values(values.pop('datas'), values['mimetype']))
            # 'check()' only uses res_model and res_id from values, and make an exists.
            # We can group the values by model, res_id to make only one query when 
            # creating multiple attachments on a single record.
            record_tuple = (values.get('res_model'), values.get('res_id'))
            record_tuple_set.add(record_tuple)
        for record_tuple in record_tuple_set:
            (res_model, res_id) = record_tuple
            self.check('create', values={'res_model':res_model, 'res_id':res_id})
        return super(IrAttachment, self).create(vals_list)


    def _file_read(self, fname, bin_size=False):
        storage = self._storage()
        for i in self:
            if storage[:5] == 's3://':#i.res_model == 'ticl.receipt.log.summary.line':
                access_key_id, secret_key, bucket_name, encryption_enabled = s3_helper.parse_bucket_url(storage)
                s3 = s3_helper.get_resource(access_key_id, secret_key)
                s3_bucket = i._connect_to_S3_bucket(s3, bucket_name)
                file_exists = s3_helper.object_exists(s3, s3_bucket.name, fname)
                if not file_exists:
                    # Some old files (prior to the installation of odoo-s3) may
                    # still be stored in the file system even though
                    # ir_attachment.location is configured to use S3
                    try:
                        read = super(IrAttachment, i)._file_read(fname, bin_size=False)
                    except Exception:
                        # Could not find the file in the file system either.
                        return False
                else:
                    s3_key = s3.Object(s3_bucket.name, fname)
                    try:
                        read = base64.b64encode(s3_key.get()['Body'].read())
                    except:
                        read = b''
            else:
                read = super(IrAttachment, i)._file_read(fname, bin_size=False)
            return read



    @api.model
    def _file_write(self, value, checksum):
        context = dict(self._context or {})
        print("Context in attachment write", context)
        storage = self._storage()
        res_model = context.get('res_model') or ''
        print("==ressssssssssssss====",res_model)
        if storage[:5] == 's3://' and res_model == 'ticl.receipt.log.summary.line':
            access_key_id, secret_key, bucket_name, encryption_enabled = s3_helper.parse_bucket_url(storage)
            s3 = s3_helper.get_resource(access_key_id, secret_key)
            s3_bucket = self._connect_to_S3_bucket(s3, bucket_name)
            bin_value = base64.b64decode(value)
            fname = hashlib.sha1(bin_value).hexdigest()

            fname += context.get('name') or ''
            print("=====fname1=====",fname)
            if encryption_enabled:
                s3.Object(s3_bucket.name, fname).put(Body=bin_value, ServerSideEncryption='AES256')
            else:
                s3.Object(s3_bucket.name, fname).put(Body=bin_value)

        else: # falling back on Odoo's local filestore
            fname = super(IrAttachment, self)._file_write(value, checksum)

        return fname  