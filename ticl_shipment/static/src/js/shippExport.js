odoo.define('ticl_receiving.shippExport', function (require) {
"use strict";

var core = require('web.core');
var crash_manager = require('web.crash_manager');
var data = require('web.data');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var pyUtils = require('web.py_utils');
var rpc = require("web.rpc");
var ActionManager = require('web.ActionManager');

var QWeb = core.qweb;
var _t = core._t;

var DataExport = Dialog.extend({
    template: 'ShipDialog',
    events: {
        'click .s_delete': function(e) {
        	e.currentTarget.parentNode.parentNode.parentNode.removeChild(e.currentTarget.parentNode.parentNode);
        	rpc.query({
                model: 'stock.move',
                method: 'remove_selected_shipment',
                args: [{'move_id':e.currentTarget.id}],
            })
            .then(function (results) {
            	
            })
            var rows= $('#shiplog tbody tr.rmv').length;
        	if(rows == 0){
        		$(".new_ship").removeAttr("disabled");
    			$(".selected_ship").removeAttr("disabled");
        	}
        },
        'click .o_button_ship_continue': function(e) {
        	var ship_id = $( "#ship_selected" ).val();
        	rpc.query({
                model: 'ticl.shipment.log',
                method: 'redirect_shipment',
                args: [{'ship_id':ship_id}],
            })
            .then(function (results) {
            	$('.modal').modal('hide');
            	self.location = results;
            	//window.location.reload();
            })
        },
        'click #remove_ship': function(e){
        	rpc.query({
                model: 'stock.move',
                method: 'remove_shipment',
            })
            .then(function (results) {
            	
            })
            $('table#shiplog tr.rmv').remove();
        	$('#ship_message').html('');
        	$('#ship_data').hide();
        	
        	
        },
    },
    init: function(parent, defaultExportFields) {
        var options = {
            title: _t("Ship Data"),
            buttons: [
                {text: _t("Select Shipment"), click: this.select_shipment, classes: "btn-primary selected_ship"},
                {text: _t("New Shipment"), click: this.new_shipment, classes: "btn-primary new_ship"},
                {text: _t("Close"), click: this.reload_shipment},
            ],
        };
        this._super(parent, options);
        
    },
    start: function() {
        var self = this;
        var ship_sts = false;
        var msg = ' items are already shipped please remove those items to proceed further.';
		var msg_s = [];
        this.$modal.find(".modal-content").css("height", "100%");
        var shtml;
        rpc.query({
            model: 'stock.move',
            method: 'search_select_preview',
            
        })
        .then(function (results) {
        	$.each(results, function (index, obj) {
        		//console.log(obj);
        		    		
        		if(obj.status != 'inventory'  || obj.condition == 'Quarantine'){
        			shtml += '<tr class="rmv" style="background:#f56e6e;">';
        			msg_s.push(obj.model);
        			ship_sts = true;
        			$(".new_ship").attr("disabled", true);
        			$(".selected_ship").attr("disabled", true);
        		}else{
        			shtml += '<tr>';
        		}
        		
        		shtml += '<td>'+obj.type+'</td>';
        		shtml += '<td>'+obj.model+'</td>';
        		shtml += '<td>'+obj.manufacturer+'</td>';
        		shtml += '<td>'+obj.serial+'</td>';
        		shtml += '<td>'+obj.condition+'</td>';
        		shtml += '<td>'+obj.xl+'</td>';
        		shtml += '<td>'+obj.unique_no+'</td>';
        		shtml += '<td><img src="/ticl_shipment/static/src/img/delete.png" id="'+obj.id+'" class="s_delete" /></td>';
        		shtml += '</tr>';
        	});
        	$("#shiplog tbody").append(shtml);
        	/*if (ship_sts){
        		var msg1 = msg_s.join();
        		var msg2 = msg1 + msg + ' <button id="remove_ship">Remove All</button>';
        		$('#ship_message').html(msg2);
        	}*/
        })
        
    },
    new_shipment: function(event) {
    	var self = this;
    	var value = $('#ship_message').text();
    	/*if (!value) {*/
    		//alert('fff');
    	rpc.query({
            model: 'ticl.shipment.log',
            method: 'redirect_shipment',
            args: [{'ship_id':false}],
        })
        .then(function (results) {
        	window.location.replace(results);
        	$('.modal').modal('hide');
        	window.location.reload(true);
        	
        })
    	/*}else{
    		$('#ship_data').show();
    		$('#tbl').hide();
    	}*/
    },
    reload_shipment: function(){
        $('.modal').modal('hide');
        window.location.reload(true);
    },
    select_shipment: function() {
    	var shiphtml;
    	rpc.query({
            model: 'ticl.shipment.log',
            method: 'get_shipment',
            
        })
        .then(function (results) {
        	
        	$('#select_ss').empty();
        	var sel = $('<select id="ship_selected">').appendTo('#select_ss');
        	$.each(results, function (index, obj) {
        		sel.append($("<option>").attr('value',obj.id).text(obj.shipment));
        		
        	});
        	$('#ship_selected').select2({width: "100%"});
        });
    	$('#ship_data').show();
    	//var value = $('#ship_message').text();
    	$(".o_export").animate({ scrollTop: $(document).height() }, "slow");
        /*if (!value) {
        	$('#ship_message').hide();
        	$('#tbl').show();
        } else {
        	$('#tbl').hide();
        	
        }*/
    },
  });
//core.action_registry.add('shipment_action', DataExport);
return DataExport;

});