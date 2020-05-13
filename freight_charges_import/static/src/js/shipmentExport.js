odoo.define('freight_charges_import.shipmentExport', function (require) {
"use strict";

var core = require('web.core');
/*var crash_manager = require('web.crash_manager');
*/var data = require('web.data');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var pyUtils = require('web.py_utils');
var rpc = require("web.rpc");
var ActionManager = require('web.ActionManager');

var QWeb = core.qweb;
var _t = core._t;

var TenderImport = Dialog.extend({
    template: 'FreightChargesImportDialog',
    events: {
    	'change #fileinput': function(e) {
    		
    		if($('#fileinput').val()){
    			$('.sb_control').attr('disabled',false);
    		}
              
            
        },
    },
    init: function(parent, defaultExportFields) {
        var options = {
            title: _t(defaultExportFields[0]),
            buttons: [
                {text: _t("Import"), click: this.import_freight_charge, classes: "btn-primary sb_control",disabled:true},
                
                {text: _t("Close"), close: true},
            ],
        };
        
        this.defaultExportFields = defaultExportFields;
        this._super(parent, options);
        
    },
    start: function() {
        var self = this;
        
        
    },
    import_freight_charge: function(event) {
    	var self = this;
    	console.log(this.defaultExportFields);
    	if (this.defaultExportFields[1] == 'shipment'){
	    	var myFile = $('#fileinput').prop('files')[0];
	    	var fileReader = new FileReader();
	        fileReader.onload = function () {
	          var data = fileReader.result;
	          
	        	  rpc.query({
	                  model: 'freight.charge.import',
	                  method: 'shipment_freight_charge_import',
	                  args: [{'file':data}],
	              })
	              .then(function (results) {
	            	    $('.modal').modal('hide');
	            	    if(results.status == 's'){
	            	    	alert(results.message);
	              			window.location.reload();
	            	    }else if(results.status == 'p'){
	            	    	alert(results.message);
	            	    }else{
	              			alert(results.message);
	              		}
	              	
	              })
	          
	          
	        };
	        fileReader.readAsDataURL(myFile);
    	}
    	if (this.defaultExportFields[1] == 'receipt'){
	    	var myFile = $('#fileinput').prop('files')[0];
	    	var fileReader = new FileReader();
	        fileReader.onload = function () {
	          var data = fileReader.result;
	          
	        	  rpc.query({
	                  model: 'freight.charge.import',
	                  method: 'receipt_freight_charge_import',
	                  args: [{'file':data}],
	              })
	              .then(function (results) {
	            	    $('.modal').modal('hide');
	            	    if(results.status == 's'){
	            	    	alert(results.message);
	              			window.location.reload();
	            	    }else if(results.status == 'p'){
	            	    	alert(results.message);
	            	    }else{
	              			alert(results.message);
	              		}
	              	
	              })
	          
	          
	        };
	        fileReader.readAsDataURL(myFile);
    	}
    	
    },
  });
//core.action_registry.add('shipment_action', DataExport);
return TenderImport;

});