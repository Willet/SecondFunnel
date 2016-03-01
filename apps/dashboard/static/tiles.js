"use strict";

var apiURL = "http://localhost:8000/api2/";

var result, ordered, tiles;
var batch = [];

var TileCollection = Backbone.Collection.extend({
    url: apiURL + 'tile/',

    model: Tile,

    getCustomURL: function(method){
        switch (method) {
            case 'swapTile':
                return apiURL + 'tile/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL('swapTile');
        console.log(options);
        console.log(method);
        return Backbone.sync.call(this, method, model, options);
    },

    swapTile: function(tileCollection, tile1_id, tile2_id){
        var tile1_ind = tileIDs.indexOf(parseInt(tile1_id));
        var tile2_ind = tileIDs.indexOf(parseInt(tile2_id));

        if (ordered)
            this.swapOrderedPriorities(tile1_ind, tile2_ind);
        else
            this.swapUnorderedPriorities(tile1_ind, tile2_ind);

        batch = JSON.stringify(batch);
        var options = {
            'url': this.getCustomURL('swapTile'),
        };

        tileCollection.batch = batch;

        return this.sync('patch', tileCollection, options)
    },

    setIncreasingPriority: function(ind){
        for (var i = ind; i >= 0; i--) {
            tiles[i]['priority'] = tiles[i+1]['priority'] + 1;
            batch.push(tiles[i]);
        }
    },

    swapOrderedPriorities: function(tile1_ind, tile2_ind){
        // Swap the priority of the tiles
        var temp = tiles[tile1_ind]['priority']
        tiles[tile1_ind]['priority'] = tiles[tile2_ind]['priority']
        tiles[tile2_ind]['priority'] = temp

        // Swap the tiles in tileIDs
        temp = tiles[tile1_ind]['priority']
        tiles[tile1_ind]['priority'] = tiles[tile2_ind]['priority']
        tiles[tile2_ind]['priority'] = temp

        //Save tile1 & tile2 priority
        batch.push(tiles[tile1_ind]);
        batch.push(tiles[tile2_ind]);
    },

    swapUnorderedPriorities: function(tile1_ind, tile2_ind){
        var temp;

        // Make sure that tile1_ind is the tile on the left, tile1_ind is the tile on the right
        if (tile1_ind > tile2_ind) {
            temp = tile1_ind;
            tile1_ind = tile2_ind;
            tile2_ind = temp;
        }

        // Swap Tile1 and Tile2 in list
        temp = tiles[tile1_ind];
        tiles[tile1_ind] = tiles[tile2_ind];
        tiles[tile2_ind] = temp;

        temp = tile1_ind;
        tile1_ind = tile2_ind;
        tile2_ind = temp;

        // Tile1 is now swapped with Tile2, so just need to set priorities. Tile1 is now on the right, Tile2 is on left

        // Set tile1's priority to the one 1 to the right's +1
        if (tile1_ind == tiles.length - 1) {
            // This means tile1 is now at the end of the list so just set priority = 1
            tiles[tile1_ind]['priority'] = 1;
        }
        else {
            // This means tile1 is not at the end of the list so there are still things on the right of it
            tiles[tile1_ind]['priority'] = tiles[tile1_ind + 1]['priority'] + 1;
        }

        // save tiles(tile1_ind) priority
        batch.push(tiles[tile1_ind]);
        
        // Now just loop from tile1 to tile with ind of 0 in list, while setting priority + 1 the next one
        this.setIncreasingPriority(tile1_ind-1);
    },
});

var Tile = Backbone.Model.extend({
    defaults: {},

    urlRoot: apiURL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        switch (method) {
            case 'swap_tile':
                return apiURL + 'tile/swap_tile_location/';
            case 'move_tile':
                return apiURL + 'tile/move_tile_to_position/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    changePriority: function(input) {
        var options = {
            'url': apiURL + 'tile/' + input.id + '/',
        };
        return Backbone.sync.call(this, 'patch', input, options);
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
        id: tile_id,
        priority: prio
    })
    result = tile.changePriority(tile);
    result.always(function() {
        result = JSON.parse(result.responseText);
        if ("id" in result)
            status = "The priority of tile with ID: " + tile.attributes.id + 
                     " has been changed to " + tile.attributes.priority + ". Press Close to see the changes";
        else
            status = result.priority;
        $('#result_' + tile_id).html(status);
    })
}

function checkPrio(tile_id){
    if (document.getElementById('result_' + tile_id).innerHTML != "")
    	window.location.reload();
}

function swapTilePositions(tile1, tile2){
    batch = [];
    var tileCollection = new TileCollection();
    tileCollection.swapTile(tileCollection, tile1, tile2);
    // console.log(tiles);
    // console.log(batch);

}

function checkOrdered(){
    var result = true;
    for (var i = 0; i < tiles.length-1; i++){
        if (tiles[i]['priority'] != tiles[i+1]['priority'] + 1){
            result = false;
            break;
        }
    }
    return result;
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
    ordered = checkOrdered();
})
