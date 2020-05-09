odoo.define('ticl_receiving.TelButton', function (require) {
    "use strict";
    var core = require('web.core');
    var dom = require('web.dom');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;
    var Dialog = require('web.Dialog');

    Dialog.confirm = function (owner, message, options) {
    var buttons = [
        {
            text: _t("Ok"),
            classes: 'btn-primary custom_button', 
            close: true,
            click: options && options.confirm_callback,
        },
        {
            text: _t("Cancel"),
            close: true,
            click: options && options.cancel_callback
        }
    ];
    return new Dialog(owner, _.extend({
        size: 'medium',
        buttons: buttons,
        $content: $('<main/>', {
            role: 'alert',
            text: message,
        }),
        title: _t("Confirmation"),
    }, options)).open({shouldFocusButtons:true});
};

    
});



