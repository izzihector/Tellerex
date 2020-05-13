odoo.define('freight_charges_import.freight_list_button', function (require) {
"use strict";

var config = require('web.config');

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require("web.rpc");
var shipmentImport = require('freight_charges_import.shipmentExport');
var Dialog = require('web.Dialog');


ListController.include({
    init: function () {
        this._super.apply(this, arguments);
        
    },

    renderButtons: function () {
        this._super.apply(this, arguments);
        
        this.$buttons.on('click', '.btn_frt_chrg_import_shipment', function () {
        	//alert('ggg');
        	var data = ['Freight Charges Import','shipment'];
        	new shipmentImport(this, data).open();
        });
    
        this.$buttons.on('click', '.btn_frt_chrg_import_receipt', function () {
        	//alert('ggg');
        	var data = ['Freight Charges Import','receipt'];
        	new shipmentImport(this, data).open();
        });
    }
});


});
