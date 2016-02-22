"use strict";

var api_URL = "http://localhost:8000/api2/";

var result;

var Tile = Backbone.Model.extend({
    defaults: {},

    urlRoot: api_URL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        switch (method) {
            case 'edit_priority':
                return api_URL + 'tile/edit_single_priority/';
            case 'swap_tile':
                return api_URL + 'tile/swap_tile_location/';
            case 'move_tile':
                return api_URL + 'tile/move_tile_to_position/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    changePriority: function(input) {
        var options = {
            'url': this.getCustomURL('edit_priority')
        };
        return Backbone.sync.call(this, 'create', input, options);
    },

    swapTile: function(input) {
    	var options = {
    		'url': this.getCustomURL('swap_tile')
    	}
    	return Backbone.sync.call(this, 'create', input, options)
    },

    moveTile: function(input) {
    	var options = {
    		'url': this.getCustomURL('move_tile')
    	}
    	return Backbone.sync.call(this, 'create', input, options)
    },

});

function editTile(tile_id, prio){
    var tile = new Tile({
        tile_id: tile_id,
        priority: prio
    })
    result = tile.changePriority(tile);
    result.always(function() {
        $('#result_' + tile_id).html(JSON.parse(result.responseText).status);
    })
}

function checkPrio(tile_id){
    if (document.getElementById('result_' + tile_id).value != "")
    	window.location.reload();
}

function swap_tile_positions(tile1, tile2){
	var tile = new Tile({
		tile_id1: tile1,
		tile_id2: tile2,
		page_id: url_slug,
	})
	result = tile.swapTile(tile);
	result.always(function(){
		$('#swap_result').html(JSON.parse(result.responseText).status + "Press Refresh to see the changes.");
	})
}

$(function(){
	$('#all-tiles').sortable({
		start: function(event, ui){
			$('#move_tiles_result').html("");
			var start_pos = ui.item.index();
			ui.item.data('start_pos', start_pos);
		},
		update: function(event, ui){
			$('#move_tiles_result').html("Loading...");
			var start_pos = ui.item.data('start_pos');
			var end_pos = ui.item.index();
			var tile = new Tile({
				index: end_pos,
				tile_id: tileIDs[start_pos],
				page_id: url_slug
			});
			result = tile.moveTile(tile);
			result.always(function(){
				$('#move_tiles_result').html(JSON.parse(result.responseText).status);
			});
		},
	});
})