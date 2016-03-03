"use strict";

var apiURL = "http://localhost:8000/api2/";

var result, ordered, tiles;
var batch = [];
var tileCollection;

var Tile = Backbone.Model.extend({
    defaults: {},

    initialize: function () {
    },

    sync: function(method, model, options){
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.Model.sync.apply(arguments);
    },

    changePriority: function(input) {
        var options = {
            'url': apiURL + 'tile/' + input.id + '/',
        };
        return Backbone.sync.call(this, 'patch', input, options);
    },
});

var TileCollection = Backbone.Collection.extend({
    defaults: {},

    url: apiURL + 'page/' + pageID + '/retrieve_tiles/',

    model: Tile,

    initialize: function () {

    },

    parse: function(response) {
        return response;
    },

    getCustomURL: function(method){
        switch (method) {
            case 'swapTile':
                return apiURL + 'tile/';
            case 'moveTile':
                return apiURL + 'tile/';
        }
    },

    sync: function(method, model, options){
        options || (options = {});
        return Backbone.sync.apply(this, arguments);
    },

    setIncreasingPriority: function(ind){
        for (var i = ind; i >= 0; i--) {
            tiles[i]['priority'] = tiles[i+1]['priority'] + 1;
            batch.push(tiles[i]);
        }
    },

    swapOrderedPriorities: function(tile1Ind, tile2Ind){
        // Swap the priority of the tiles
        var temp = tiles[tile1Ind]['priority'];
        tiles[tile1Ind]['priority'] = tiles[tile2Ind]['priority'];
        tiles[tile2Ind]['priority'] = temp;

        // Swap the tiles in tileIDs
        temp = tiles[tile1Ind]['priority'];
        tiles[tile1Ind]['priority'] = tiles[tile2Ind]['priority'];
        tiles[tile2Ind]['priority'] = temp;

        //Save tile1 & tile2 priority
        batch.push(tiles[tile1Ind]);
        batch.push(tiles[tile2Ind]);
    },

    swapUnorderedPriorities: function(tile1Ind, tile2Ind){
        var temp;

        // Make sure that tile1Ind is the tile on the left, tile1Ind is the tile on the right
        if (tile1Ind > tile2Ind) {
            temp = tile1Ind;
            tile1Ind = tile2Ind;
            tile2Ind = temp;
        }

        // Swap Tile1 and Tile2 in list
        temp = tiles[tile1Ind];
        tiles[tile1Ind] = tiles[tile2Ind];
        tiles[tile2Ind] = temp;

        temp = tile1Ind;
        tile1Ind = tile2Ind;
        tile2Ind = temp;

        // Tile1 is now swapped with Tile2, so just need to set priorities. Tile1 is now on the right, Tile2 is on left

        // Set tile1's priority to the one 1 to the right's +1
        if (tile1Ind == tiles.length - 1) {
            // This means tile1 is now at the end of the list so just set priority = 1
            tiles[tile1Ind]['priority'] = 1;
        }
        else {
            // This means tile1 is not at the end of the list so there are still things on the right of it
            tiles[tile1Ind]['priority'] = tiles[tile1Ind + 1]['priority'] + 1;
        }

        // save tiles(tile1Ind) priority
        batch.push(tiles[tile1Ind]);
        
        // Now just loop from tile1 to tile with ind of 0 in list, while setting priority + 1 the next one
        this.setIncreasingPriority(tile1Ind-1);
    },

    swapTile: function(tileCollection, tile1ID, tile2ID){
        batch = [];

        var tile1Ind = tileIDs.indexOf(parseInt(tile1ID));
        var tile2Ind = tileIDs.indexOf(parseInt(tile2ID));

        if ((tile1Ind == -1) || (tile2Ind == -1)){
            throw "Tile 1 or Tile 2 is not a tile on this page";
        }

        if (ordered)
            this.swapOrderedPriorities(tile1Ind, tile2Ind);
        else
            this.swapUnorderedPriorities(tile1Ind, tile2Ind);

        batch = JSON.stringify(batch);

        var options = {
            'url': apiURL + 'tile/',
        };

        tileCollection.set({data: batch});

        return Backbone.sync.call(this, 'patch', tileCollection, options);
    },

    moveTileToPosition: function(tileCollection, index, tileID){
        batch = [];

        // First check if the index we're moving to is on the left or right of original tile index
        // Then insert/delete appropriately
        var tileInd = tileIDs.indexOf(parseInt(tileID));

        if (index < tileInd){
            tiles.splice(index, 0, tiles[tileInd]);
            tiles.splice(tileInd + 1, 1);
        }
        else{
            tiles.splice(index + 1, 0, tiles[tileInd]);
            tiles.splice(tileInd, 1);
        }
        // Set the starting point for re-numbering the priority to be the one on the right most
        var startPoint = 0;

        if (index > tileInd) {
            startPoint = index;
        }
        else {
            startPoint = tileInd;
        }

        if (startPoint == tiles.length - 1){
            // This means the starting point is now at the end of the list so just set priority = 1
            tiles[startPoint] = 1;
        }
        else {
            // This means the starting point is not at the end of the list so just set priority = element on the right + 1
            // This makes sure that the starting point will always be at this spot
            tiles[startPoint]['priority'] = tiles[startPoint + 1]['priority'] + 1;
        }

        batch.push(tiles[startPoint]);

        // Go from starting point to the beginning of the list, while setting the priorities for each tile
        this.setIncreasingPriority(startPoint-1);

        batch = JSON.stringify(batch);

        var options = {
            'url': apiURL + 'tile/',
        };

        tileCollection.set({data: batch});

        return Backbone.sync.call(this, 'patch', tileCollection, options);
    },
});

var TileView = Backbone.View.extend({

});

function editTile(tileID, prio){
    var tile = new Tile({
        id: tileID,
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
        $('#result_' + tileID).html(status);
    })
}

function checkPrio(tileID){
    if (document.getElementById('result_' + tileID).innerHTML != "")
    	window.location.reload();
}

function swapTilePositions(tile1, tile2){
    $('#swapResult').html("Loading...");
    var tileColl = new TileCollection();
    try {
        result = tileColl.swapTile(tileColl, tile1, tile2);
        result.always(function() {
            if (result.responseJSON.length != 0){
                status = "The tile with ID: " + tile1 + " has been swapped with tile with ID: "
                        + tile2 + ". Press Refresh to see the changes.";
            }
            else {
                status = "Swapping failed due to an error.";
            }
            $('#swapResult').html(status);
        })
    }
    catch (e){
        $('#swapResult').html(e);
    }
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
			$('#moveTilesResult').html("");
			var startPos = ui.item.index();
			ui.item.data('startPos', startPos);
		},
		update: function(event, ui){
			$('#moveTilesResult').html("Loading...");
			var startPos = ui.item.data('startPos');
			var endPos = ui.item.index();
            var tileCollection = new TileCollection();

            result = tileCollection.moveTileToPosition(tileCollection, endPos, tileIDs[startPos]);
			result.always(function(){
                if (result.responseJSON.length != 0){
                    status = "The tile with ID: " + tileIDs[startPos] + " has been moved to index: "
                            + endPos + ". Press Refresh to see the new tile priorities.";
                }
                else {
                    status = "Moving failed due to an error.";
                }
				$('#moveTilesResult').html(status);
			});
		},
	});
    ordered = checkOrdered();
    tileCollection = new TileCollection();
    tileCollection.fetch().done(function(){
        console.log(tileCollection);
    });
})
