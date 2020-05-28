# -*- coding: utf-8 -*-
import hashlib
import base64
from odoo import models
from . import s3_helper

class S3Attachment(models.Model):
    _inherit = "ir.attachment"


    def _connect_to_S3_bucket(self, s3, bucket_name):
        s3_bucket = s3.Bucket(bucket_name)
        exists = s3_helper.bucket_exists(s3, bucket_name)

        if not exists:
            s3_bucket = s3.create_bucket(Bucket=bucket_name)
        return s3_bucket

    def _file_read(self, fname, bin_size=False):
        print ("file_read################")
        storage = self._storage()
        
        for i in self:
            #print ("modellll read ....", i.res_model)
            if storage[:5] == 's3://' and i.res_model == 'ticl.receipt.log.summary.line':#i.res_model == 'ticl.receipt.log.summary.line':
                access_key_id, secret_key, bucket_name, encryption_enabled = s3_helper.parse_bucket_url(storage)
                s3 = s3_helper.get_resource(access_key_id, secret_key)
                s3_bucket = i._connect_to_S3_bucket(s3, bucket_name)
                file_exists = s3_helper.object_exists(s3, s3_bucket.name, fname)
                if not file_exists:
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
                    #print ("reads3_key#W#######", s3_key)
                    try:
                        read = base64.b64encode(s3_key.get()['Body'].read())
                        #read += i.name
                        #print ("read999999999999", read)
                    except:
                        read = b''
            else:
                read = super(S3Attachment, i)._file_read(fname, bin_size=False)
                #print ("read!!!!!!!!!!!!!!!!!", read)
            return read

    #@api.model    
    def _file_write(self, value, checksum):
        
        storage = self._storage()
        # _file_read  = self._file_read()
        # print("modellll read ....", _file_read)
        for i in self:
            print("modellll read fileeeeeeeee....", i.name)

        if storage[:5] == 's3://':
            access_key_id, secret_key, bucket_name, encryption_enabled = s3_helper.parse_bucket_url(storage)
            s3 = s3_helper.get_resource(access_key_id, secret_key)
            s3_bucket = self._connect_to_S3_bucket(s3, bucket_name)
            bin_value = base64.b64decode(value)
            fname = hashlib.sha1(bin_value).hexdigest()
            res = self.env['ir.attachment'].search([('checksum','=',fname)], limit=1)
            print("=====ressssssssssssssssss=====",res)
            fname += str(res.name)
            print("=====fname111=====",fname)
            if encryption_enabled:
                s3.Object(s3_bucket.name, fname).put(Body=bin_value, ServerSideEncryption='AES256')
            else:
                s3.Object(s3_bucket.name, fname).put(Body=bin_value)

        else: # falling back on Odoo's local filestore
            fname = super(S3Attachment, self)._file_write(value, checksum)

        return fname