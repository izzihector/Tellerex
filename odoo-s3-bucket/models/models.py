# -*- coding: utf-8 -*-
import hashlib
import base64
from odoo import models, fields, api, _
from . import s3_helper

class S3Attachment(models.Model):
    _inherit = "ir.attachment"


    def _connect_to_S3_bucket(self, s3, bucket_name):
        s3_bucket = s3.Bucket(bucket_name)
        exists = s3_helper.bucket_exists(s3, bucket_name)

        if not exists:
            s3_bucket = s3.create_bucket(Bucket=bucket_name)
        return s3_bucket

    @api.model
    def _file_read(self, fname, bin_size=False):
        storage = self._storage()
        #print("====storage==",storage)       
        for i in self:
            #print("====attachment==",i.res_model)
            if storage[:5] == 's3://' and i.res_model == 'ticl.receipt.log.summary.line':#i.res_model == 'ticl.receipt.log.summary.line':
                access_key_id, secret_key, bucket_name, encryption_enabled = s3_helper.parse_bucket_url(storage)
                s3 = s3_helper.get_resource(access_key_id, secret_key)
                s3_bucket = i._connect_to_S3_bucket(s3, bucket_name)
               # print("====s3_bucket==",s3_bucket)
                file_exists = s3_helper.object_exists(s3, s3_bucket.name, fname)
                #print("====file_exists==",file_exists)
                if not file_exists:
                    print("====try==",i.res_model)
                    # Some old files (prior to the installation of odoo-s3) may
                    # still be stored in the file system even though
                    # ir_attachment.location is configured to use S3
                    try:
                        read = super(S3Attachment, i)._file_read(fname, bin_size=False)
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
                read = super(S3Attachment, i)._file_read(fname, bin_size=False)
                print("====read==",read)
            return read

    @api.model
    def _file_write(self, value, checksum):
        #print("modellll read ....", self.res_model)
        storage = self._storage()
        if storage[:5] == 's3://' and self.res_model == 'ticl.receipt.log.summary.line':
            access_key_id, secret_key, bucket_name, encryption_enabled = s3_helper.parse_bucket_url(storage)
            s3 = s3_helper.get_resource(access_key_id, secret_key)
            s3_bucket = self._connect_to_S3_bucket(s3, bucket_name)
            bin_value = base64.b64decode(value)
            fname = hashlib.sha1(bin_value).hexdigest()
            fname += self.name
            print("=====fname11111111111111=====",fname)
            if encryption_enabled:
                s3.Object(s3_bucket.name, fname).put(Body=bin_value, ServerSideEncryption='AES256')
            else:
                s3.Object(s3_bucket.name, fname).put(Body=bin_value)

        else: # falling back on Odoo's local filestore
            fname = super(S3Attachment, self)._file_write(value, checksum)

        return fname