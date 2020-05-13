odoo.define('ticl_recommend_view.list_button_tender', function (require) {
"use strict";

var config = require('web.config');

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require("web.rpc");

var Dialog = require('web.Dialog');
var session = require('web.session');
ListController.include({
    init: function () {
        rpc.query({
                  model: 'ticl.recommend.model',
                  method: 'update_view',
                  args: [{'file':[]}],
              })
              .then(function (results) {
              })
        this._super.apply(this, arguments);

    },

    renderButtons: function () {
        this._super.apply(this, arguments);
        this.$buttons.on('click', '.o_button_update_view', this._uploadImage);
        this.$buttons.on('click', '.o_button_export_to_excel', this._exportExcel);

    },
    _uploadImage: function () {
        rpc.query({
                  model: 'ticl.recommend.model',
                  method: 'update_view',
                  args: [{'file':[]}],
              })
              .then(function (results) {
              window.location.reload();
              })
    },
    _exportExcel: function () {
        rpc.query({
                  model: 'ticl.recommend.report',
                  method: 'export_excel',
                  args: [{'file':[]}],
              })
              .then(function (results) {
              session.get_file({
                url: '/web/content/ticl.recommend.report/'+results.id+'/to_rec_file/To Recommend Report.xls?download=true',
              })
              })
    },
});


});
