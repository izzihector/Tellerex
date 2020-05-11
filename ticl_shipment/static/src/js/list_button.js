odoo.define('ticl_receiving.list_button', function (require) {
"use strict";

var config = require('web.config');
var KanbanController = require('web.KanbanController');
var KanbanView = require('web.KanbanView');
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require("web.rpc");
var ListRenderer = require('web.ListRenderer');
var Dialog = require('web.Dialog');
var shippExport = require('ticl_receiving.shippExport');
var FormController = require('web.FormController');
var count = 1;
var total_count = 0;
FormController.include({
    createRecord: function (parentID) {
        
        var self = this;
        var record = this.model.get(this.handle, {raw: true});
        var context = record.getContext();
        if(this.modelName == 'ticl.shipment.log'){
            context = {};
        }
        return this.model.load({
            context: context,
            fields: record.fields,
            fieldsInfo: record.fieldsInfo,
            modelName: this.modelName,
            parentID: parentID,
            res_ids: record.res_ids,
            type: 'record',
            viewType: 'form',
        }).then(function (handle) {
            self.handle = handle;
            self._updateEnv();
            return self._setMode('edit');
        });
    },
});
ListRenderer.include({
    
    getUrlParameter : function(url) {
        var result = {};
        var searchIndex = url.indexOf("?");
        
        var sURLVariables = url.split('&');
        for (var i = 0; i < sURLVariables.length; i++)
        {       
            var sParameterName = sURLVariables[i].split('=');      
            result[sParameterName[0]] = sParameterName[1];
        }
        return result;
    },
    
    _onSelectRecord: function (event) {
        this._super.apply(this, arguments);
        
        event.stopPropagation();
        var model = this.getUrlParameter(event.currentTarget.baseURI);
        
        //event.preventDefault();
        if (model['model'] == 'stock.move'){


            if (!$(event.currentTarget).find('input').is('checked')) {
            total_count = total_count + 1
            }
            if (total_count ==2){
                total_count = 0
                var unqid = $(event.currentTarget).context.parentNode.childNodes[4].innerHTML;

                this._rpc({
                    model: 'stock.move',
                    method: 'search_select',
                    args: [{shippable: true,'tel_unique_no':unqid,'count':count}],
                    
                })
                .then(function (result) {
                    
                });
                /*alert(total_count)*/

            }
        }





            /*var unqid = $(event.currentTarget).context.parentNode.childNodes[4].innerHTML;
            if (!$(event.currentTarget).find('input').is('checked')) {
                
                this._rpc({
                    model: 'stock.move',
                    method: 'search_select',
                    args: [{shippable: true,'tel_unique_no':unqid,'count':count}],
                    
                })
                .then(function (result) {
                    
                });
            }else{
                
                this._rpc({
                    model: 'stock.move',
                    method: 'search_select',
                    args: [{shippable: false,'tel_unique_no':unqid,'count':count}],
                    
                })
                .then(function (result) {
                    
                });
            }
        }*/
        
        
        
        
        
    },
});

ListController.include({
    init: function () {
        this._super.apply(this, arguments);
        
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Extends the renderButtons function of ListView by adding an event listener
     * on the import button.
     *
     * @override
     */
    _onCreateRecord: function (event) {
        this._super.apply(this, arguments);
        // we prevent the event propagation because we don't want this event to
        // trigger a click on the main bus, which would be then caught by the
        // list editable renderer and would unselect the newly created row
        if (event) {
            event.stopPropagation();
        }
        var state = this.model.get(this.handle, {raw: true});
        if (this.editable && !state.groupedBy.length) {
            this._addRecord();
        } else {
            //this.reload();
            this.trigger_up('switch_view', {view_type: 'form', res_id: undefined, context:{}});
        }
    },
    
    renderButtons: function () {
        this._super.apply(this, arguments); // Sets this.$buttons
        this.$buttons.on('click', '.o_button_import_ship', function () {
            
            var data = [];
            new shippExport(this, data).open();
        });
        this.$buttons.on('click', '.o_button_scrap', this._onScrapRecord.bind(this));
    },
    _onScrapRecord: function (event) {
        var self = this;
        this._rpc({
            model: 'stock.move',
            method: 'get_scrapview_action',
            args: [{'ids':this.getSelectedIds()}],
            context: {},
        })
        .then(function (action) {
            self.do_action(action);
        });
            
    }
});


});
