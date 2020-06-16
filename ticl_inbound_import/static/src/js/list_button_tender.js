odoo.define('ticl_inbound_import.list_button_tender', function (require) {
"use strict";

var config = require('web.config');

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require("web.rpc");

var Dialog = require('web.Dialog');
var tenderImport = require('ticl_inbound_import.shipTenderExport');


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
    if (this.$buttons){
        this.$buttons.on('click', '.o_button_import_asn', function () {
        	
        	var data = ['asn','Import Inbound Tender File'];
        	new tenderImport(this, data).open();
        });
    }
    }
});


});
