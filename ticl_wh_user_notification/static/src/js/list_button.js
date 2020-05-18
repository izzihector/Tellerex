odoo.define('ticl_wh_user_notification.list_button', function (require) {
"use strict";

var config = require('web.config');

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require("web.rpc");
var Dialog = require('web.Dialog');
var core = require('web.core');
var _t = core._t;

ListController.include({
    init: function () {
        this._super.apply(this, arguments);
        
    },

    renderButtons: function () {
        this._super.apply(this, arguments);
         this.$buttons.on('click', '.btn_shipment_notification', this._onShipmentRecord.bind(this));
    },
    _onShipmentRecord: function (event) {
        var self = this;
        rpc.query({
                model: 'ticl.shipment.log',
                method: 'warehouse_pending_shipment_notification',
                args: [{'ids':this.getSelectedIds()}],
            })
            .then(function (results) {
          	  if(results.status == 'f'){
          		Dialog.confirm(self, _t(results.message), {});
          	  }else if(results.status == 'p'){
          		//var s = results.message.replace(/[&\/\\#, +()$~%.'":*?<>{}]/g, '\');
            		Dialog.confirm(self, _t(results.message), {});
              }else{
            	  //var s = results.message.replace(/[&\/\\#, +()$~%.'":*?<>{}]/g, '\');
            	  Dialog.confirm(self, _t(results.message), {});
              }
          	  
            });
    }
});


});
