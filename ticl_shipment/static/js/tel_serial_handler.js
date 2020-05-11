odoo.define('ticl_shipment.TelSerialHandler', function (require) {
    "use strict";
    var core = require('web.core');
    var BasicModel = require('web.BasicModel');
    var FormView = require('barcodes.FormView');
    var _t = core._t;
    var TelSerialHandler = FormView.extend({
        init: function (parent, context) {
            if (parent.ViewManager.action) {
                this.form_view_initial_mode = parent.ViewManager.action.context.form_view_initial_mode;
            } else if (parent.ViewManager.view_form) {
                this.form_view_initial_mode = parent.ViewManager.view_form.options.initial_mode;
            }
            return this._super.apply(this, arguments);
        },
        start: function () {
            this._super();
            this.so_model = new BasicModel("ticl.shipment.log.line");
            this.form_view.options.disable_autofocus = 'true';
            if (this.form_view_initial_mode) {
                this.form_view.options.initial_mode = this.form_view_initial_mode;
            }
        },
        on_serial_number: function(serial_number) {
            var self = this;
            self.so_model.call('so_barcode',[serial_number]).then(function () {
                self.getParent().reload();
            });

        },
    });
    core.form_widget_registry.add(TelSerialHandler);
    return TelSerialHandler;
});
