odoo.define('ticl_receiving.atm_processing', function (require) {
"use strict";

var core = require('web.core');
var crash_manager = require('web.crash_manager');
var data = require('web.data');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var pyUtils = require('web.py_utils');
var rpc = require("web.rpc");
var ActionManager = require('web.ActionManager');

var QWeb = core.qweb;
var _t = core._t;

var TenderImport = Dialog.extend({
    template: 'ImportATMImages',
    events: {
    	'change #fileinput': function(e) {

    		if($('#fileinput').val()){
    			$('.sb_control').attr('disabled',false);
    		}


        },
    },
    init: function(parent, defaultExportFields) {
        var options = {
            title: _t(defaultExportFields[1]),
            buttons: [
                {text: _t("Import"), click: this.import_tender, classes: "btn-primary sb_control",disabled:true},

                {text: _t("Close"), close: true},
            ],
        };

        this.defaultExportFields = defaultExportFields;
        this._super(parent, options);

    },
    start: function() {
        var self = this;
//        if (self.defaultExportFields[0] == 'asn'){
//          self.$('.asn').hide();
//          self.$('.tender').show();
//        }
//        if (self.defaultExportFields[0] == 'tender'){
//          self.$('.tender').hide();
//          self.$('.asn').show();
//        }

    },

    import_tender: function(event) {
    	var self = this;
    	var myFile = $('#fileinput').prop('files')[0];
    	var fileReader = new FileReader();
        fileReader.onload = function () {
          var data = fileReader.result;
          console.log(self.defaultExportFields[0]);
          if (self.defaultExportFields[0] == 'asn'){
        	  rpc.query({
                  model: 'ticl.receipt.log.summary.line',
                  method: 'import_atm_process_images',
                  args: [{'file':data}],
              })
              .then(function (results) {
            	    $('.modal').modal('hide');
            	    if(results.status == 's'){
            	    	Dialog.confirm(self, _t(results.message), {
                            confirm_callback: function() {
                              window.location.reload();
                            },
                            title: _t('Import ATM Processing Images'),
                        }).on("closed", null, function () {
                          $('.ui-button:contains("Ok")').hide();
                          window.location.reload();
                        });
/*              			window.location.reload();*/
                    }else if(results.status == 'p'){
            	    	Dialog.confirm(self, _t(results.message), {
                            confirm_callback: function() {
                              window.location.reload();
                            },
                            title: _t('Import'),
                        }).on("closed", null, function () {
                          window.location.reload();
                        });
            	    }else{
              			Dialog.confirm(self, _t(results.message), {
                            confirm_callback: function() {
                              //window.location.reload();
                            },
                            title: _t('Import'),
                        }).on("closed", null, function () {
                          //window.location.reload();
                        });
              		}

              })
          }
        };
        fileReader.readAsDataURL(myFile);



    },
  });
//core.action_registry.add('shipment_action', DataExport);
return TenderImport;

});