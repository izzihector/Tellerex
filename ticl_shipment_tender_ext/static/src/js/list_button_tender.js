odoo.define('ticl_shipment_tender_ext.list_button_tender', function (require) {
"use strict";

var config = require('web.config');

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require("web.rpc");

var Dialog = require('web.Dialog');
var tenderImport = require('ticl_shipment_tender_ext.shipTenderExport');


ListController.include({
    init: function () {
        this._super.apply(this, arguments);
        
    },

    renderButtons: function () {
        this._super.apply(this, arguments);
//        this.$buttons.on('click', '.o_button_import_tender', function () {
//
//        	var data = ['tender','Import Tender File'];
//        	new tenderImport(this, data).open();
//        });
        this.$buttons.on('click', '.o_button_import_outbond', function () {
        	
        	var data = ['tender','Import Inbound Tender File'];
        	new tenderImport(this, data).open();
        });
    }
});


});
