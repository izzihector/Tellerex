odoo.define('ticl_shipment.fields', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');
var core = require('web.core');
var rpc = require("web.rpc");
var QWeb = core.qweb;

var RemoveRelRecord = ListRenderer.include({
    
	
	_onRemoveIconClick: function (event) {
		var $crow = $(event.target).closest('tr');
        var cid = $crow.data('id');
        var arr = cid.split('_');
        var mv_id = $crow.find("td:eq(7)").text();
        if (arr[0] == 'ticl.stock.move.scrap.line'){
        	this._rpc({
            model: 'ticl.stock.move.scrap.line.store',
            method: 'delete_related',
            args: [{'delete_id': mv_id}],
         	})
	        .then(function (result) {
	        	
	        });
        }
        this._super.apply(this, arguments);
		
        
    },

    
    
    
});
  
});
