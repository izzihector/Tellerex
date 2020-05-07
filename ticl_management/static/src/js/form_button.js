odoo.define('ticl_management.form_button', function (require) {
"use strict";

var config = require('web.config');

var FormController = require('web.FormController');

var core = require('web.core');
var qweb = core.qweb;

FormController.include({
	
    renderButtons: function ($node) {
    	var $footer = this.footerToButtons ? this.$('footer') : null;
        var mustRenderFooterButtons = $footer && $footer.length;
        if (!this.defaultButtons && !mustRenderFooterButtons) {
            return;
        }
        this.$buttons = $('<div/>');
        if (mustRenderFooterButtons) {
            this.$buttons.append($footer);

        } else {
            this.$buttons.append(qweb.render("FormView.buttons", {widget: this}));
            this.$buttons.on('click', '.o_form_button_edit', this._onEdit.bind(this));
            this.$buttons.on('click', '.o_form_button_create', this._onCreate.bind(this));
            this.$buttons.on('click', '.o_form_button_save', this._onSave.bind(this));
            this.$buttons.on('click', '.o_form_button_cancel', this._onDiscard.bind(this));
            this.$buttons.on('click', '.o_form_button_cancel_ticl', function () {
            	window.location.reload();
            	
            });
            this._assignSaveCancelKeyboardBehavior(this.$buttons.find('.o_form_buttons_edit'));
            this.$buttons.find('.o_form_buttons_edit').tooltip({
                delay: {show: 200, hide:0},
                title: function(){
                    return qweb.render('SaveCancelButton.tooltip');
                },
                trigger: 'manual',
            });
            this._updateButtons();
        }
        this.$buttons.appendTo($node);
    },
});



});
