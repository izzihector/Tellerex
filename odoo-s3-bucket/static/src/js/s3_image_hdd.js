odoo.define('odoo-s3-bucket.s3_image_hdd', function (require) {
"use strict";
/**
 * The feature is disabled as it was replaced by another feature
 * while still holding unfixed bugs and doing unnecessary rpc.
 */

var core = require('web.core');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var Sidebar = require('web.Sidebar');
var session = require('web.session');
var WebClient = require('web.WebClient');
var rootWidget = require('root.widget');
var field_utils = require('web.field_utils');
var fieldRegistry = require('web.field_registry');
var _t = core._t;
var Char = fieldRegistry.get('char');
var import_button_hdd = Char.extend({
       template : "import_button_hdd",
        events : {
           'change' : 'import_files',
        },
        init : function(){
           this._super.apply(this,arguments);
           this._start = null;
        },
        start : function() {
        },
        import_files : function(event){
            var self = this;
            var files = event.target.files;
            console.log(self.viewFields);
            console.log('ghjk');
            var attachment_ids_hdd = self.fields.attachment_ids_hdd; // Get existing attachments
            var data64 = null;
            var values_list = [];
            _.each(files, function(file){
                // Check if the file is already in the attachments, must specify field name here :/
                if(self.already_attached(attachment_ids_hdd.get_value(),file.name)){
                    return;
                }
                var filereader = new FileReader();
                filereader.readAsDataURL(file);
                filereader.onloadend = function(upload) {
                        var data = upload.target.result;
                        data64 = data.split(',')[1];
                        var values = {
                            'name' : file.name,
                            'type' : 'binary',
                            'datas' : data64,
                        };
                        values_list.push([ 0, 0, values]);
                        if(values_list.length == files.length){
                            attachment_ids_hdd.set_value(values_list);
                        }
                };
            });
        },
        already_attached : function (attachments,filename) {
              for(var i=0;i<attachments.length;i++){
                  if(attachments[i][2]['name'] == filename){
                      return true;
                  }
              }
              return false;
        },
    });

	fieldRegistry.add('import_button_hdd',import_button_hdd);
});
