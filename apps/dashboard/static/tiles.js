"use strict";

var apiURL = "http://localhost:8000/api2/";

var tileCollection,   //Collection of all tiles
    tilesView,        //View of all tiles
    tiles,            //Array of all tile as models
    result, ordered,
    batch = [];

var Tile = Backbone.Model.extend({
    defaults: {},

    initialize: function () {

    },

    changePriority: function(input) {
        var model = this;
        result = model.save({priority: input}, {
            patch: true,
            url: apiURL + 'tile/' + model.id + '/',
        });
        result.always(function() {
            result = JSON.parse(result.responseText);
            if ("id" in result)
                status = "The priority of tile with ID: " + model.id + 
                         " has been changed to " + model.attributes.priority + ". Press Close to see the changes.";
            else
                status = result.priority;
            $('#result_' + model.id).html(status);
        });
    },
});

var TileCollection = Backbone.Collection.extend({
    defaults: {},

    url: apiURL + 'tile?page=' + pageID,

    model: Tile,

    initialize: function () {

    },

    parse: function(response) {
        return response;
    },

    getCustomURL: function(method){
        switch (method) {
            case 'swapTile':
                return apiURL + 'tile';
            case 'moveTile':
                return apiURL + 'tile';
        }
    },

    setIncreasingPriority: function(ind){
        for (var i = ind; i >= 0; i--) {
            tiles[i].attributes.priority = tiles[i+1].attributes.priority + 1;
            batch.push({
                'id': tiles[i].attributes.id, 
                'priority': tiles[i].attributes.priority
            });
            tileCollection.models[i].set({priority: tiles[i].attributes.priority});
        }
    },

    swapOrderedPriorities: function(tile1Ind, tile2Ind){
        // Since we're re-fetching and re-rendering the tiles after swapping
        // Just need to add the tile id and new priorities to batch array
        batch.push({
            'id': tiles[tile1Ind].attributes.id, 
            'priority': tiles[tile2Ind].attributes.priority
        });
        tileCollection.models[tile1Ind].set({priority: tiles[tile2Ind].attributes.priority});
        batch.push({
            'id': tiles[tile2Ind].attributes.id, 
            'priority': tiles[tile1Ind].attributes.priority
        });
        tileCollection.models[tile2Ind].set({priority: tiles[tile1Ind].attributes.priority});
    },

    swapUnorderedPriorities: function(tile1Ind, tile2Ind){
        var temp;

        // Make sure that tile1Ind is the tile on the left, tile2Ind is the tile on the right
        if (tile1Ind > tile2Ind) {
            temp = tile1Ind;
            tile1Ind = tile2Ind;
            tile2Ind = temp;
        }

        // Swap Tile1 and Tile2 in tileCollection
        temp = tiles[tile1Ind];
        tiles[tile1Ind] = tiles[tile2Ind];
        tiles[tile2Ind] = temp;

        temp = tileCollection.models[tile1Ind];
        tileCollection.models[tile1Ind] = tileCollection.models[tile2Ind];
        tileCollection.models[tile2Ind] = temp;

        temp = tileImagesNames[tile1Ind];
        tileImagesNames[tile1Ind] = tileImagesNames[tile2Ind];
        tileImagesNames[tile2Ind] = temp;

        temp = tile1Ind;
        tile1Ind = tile2Ind;
        tile2Ind = temp;

        // Tile1 is now swapped with Tile2, so just need to set priorities. Tile1 is now on the right, Tile2 is on left

        // Set tile1's priority to the one 1 to the right's +1
        if (tile1Ind == tiles.length - 1) {
            // This means tile1 is now at the end of the list so just set priority = 1
            tiles[tile1Ind].attributes.priority = 1;
        }
        else {
            // This means tile1 is not at the end of the list so there are still things on the right of it
            tiles[tile1Ind].attributes.priority = tiles[tile1Ind + 1].attributes.priority + 1;
        }

        // save tiles(tile1Ind) id and priority to batch array
        batch.push({
            'id': tiles[tile1Ind].attributes.id, 
            'priority': tiles[tile1Ind].attributes.priority
        });
        tileCollection.models[tile1Ind].set({priority: tiles[tile1Ind].attributes.priority});

        // Now just loop from tile1 to tile with ind of 0 in list, while setting priority + 1 the next one
        this.setIncreasingPriority(tile1Ind-1);
    },

    swapTile: function(swapTile, tile1ID, tile2ID){
        $('#swapResult').html("Swapping tiles...");

        batch = [];

        var tile1Ind = this.objectIndexOf(tileCollection, 'id', parseInt(tile1ID));
        var tile2Ind = this.objectIndexOf(tileCollection, 'id', parseInt(tile2ID));

        try {
            if ( (tile1Ind == -1) || (tile2Ind == -1) )
                throw "Tile 1 or Tile 2 is not a tile on this page";

            if (ordered)
                this.swapOrderedPriorities(tile1Ind, tile2Ind);
            else 
                this.swapUnorderedPriorities(tile1Ind, tile2Ind);

            //Batch now contains the tiles and the tiles' new priorities
            batch = JSON.stringify(batch);

            var options = {
                'url': this.getCustomURL('swapTile'),
            };

            swapTile.set({data: batch});

            result = Backbone.sync.call(this, 'patch', swapTile, options);
            result.always(function() {
                if (result.responseJSON.length != 0){
                    status = "The tile with ID: " + tile1ID + " has been swapped with tile with ID: "
                            + tile2ID + ". Refreshing tiles.";
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
    },

    objectIndexOf: function(list, attribute, value) {
        var model;
        for (var i = 0; i < list.length; i++) {
            model = tiles[i];
            if (model.attributes[attribute] == value)
                return i;
        }
        return -1;
    },

    moveTileToPosition: function(moveTileCollection, index, tileID) {
        batch = [];
        // First check if the index we're moving to is on the left or right of original tile index
        // Then insert/delete appropriately
        var tileInd = this.objectIndexOf(tileCollection, 'id', parseInt(tileID));

        if (index < tileInd){
            tiles.splice(index, 0, tiles[tileInd]);
            tiles.splice(tileInd + 1, 1);
            tileImagesNames.splice(index, 0, tileImagesNames[tileInd]);
            tileImagesNames.splice(tileInd + 1, 1);
        }
        else{
            tiles.splice(index + 1, 0, tiles[tileInd]);
            tiles.splice(tileInd, 1);
            tileImagesNames.splice(index + 1, 0, tileImagesNames[tileInd]);
            tileImagesNames.splice(tileInd, 1);
        }
        // Set the starting point for re-numbering the priority to be the one on the right most
        var startPoint = 0;

        if (index > tileInd)
            startPoint = index;
        else
            startPoint = tileInd;

        if (startPoint == tiles.length - 1)
            // This means the starting point is now at the end of the list so just set priority = 1
            tiles[startPoint].attributes.priority = 1;
        else 
            // This means the starting point is not at the end of the list so just set priority = element on the right + 1
            // This makes sure that the starting point will always be at this spot
            tiles[startPoint].attributes.priority = tiles[startPoint + 1].attributes.priority + 1;

        // save tiles(startPoint) id and priority to batch array
        batch.push({
            'id': tiles[startPoint].attributes.id, 
            'priority': tiles[startPoint].attributes.priority
        });

        // Go from starting point to the beginning of the list, while setting the priorities for each tile
        this.setIncreasingPriority(startPoint-1);

        batch = JSON.stringify(batch);

        var options = {
            'url': apiURL + 'tile',
        };

        moveTileCollection.set({data: batch});

        result = Backbone.sync.call(this, 'patch', moveTileCollection, options);
        result.always(function() {
            if (result.responseJSON.length != 0){
                status = "The tile with ID: " + tileID + " has been moved to index: "
                         + index + ". Refreshing tiles.";
            }
            else {
                status = "Move failed due to an error.";
            }
            $('#moveTilesResult').html(status);
        })
    },

    checkOrdered: function(){
        result = true;
        for (var i = 0; i < tileCollection.length-1; i++){
            if (tiles[i].attributes.priority != tiles[i+1].attributes.priority + 1){
                result = false;
                break;
            }
        }
        return result;
    },
});

var TileView = Backbone.View.extend({
    template: _.template($('#tile-template').html()),

    className: 'tile-list sortable selectable',

    initialize: function(ind){
        _.bindAll(this, "render");
        this.model.bind('change', this.render);
        this.img = tileImagesNames[ind.ind].img;
        this.name = tileImagesNames[ind.ind].name;
    },

    render: function(){
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    events: {
        "click #editTile": "editTile",
        "click #checkPrio": "checkPrio",
    },

    editTile: function(){
        this.model.changePriority(parseInt(document.getElementById('new_priority_' + this.model.id).value));
    },
    
    checkPrio: function(){
        if (document.getElementById('result_' + this.model.id).innerHTML != "")
            window.location.reload();
    },
});

var TileCollectionView = Backbone.View.extend({
    el: "#backbone-tiles",

    initialize: function() {
        this.render();
    },

    render: function(){
        this.$el.html('');

        tileCollection.each(function(model, index){
            var tileView = new TileView({
                model: model,
                ind: index,
            });
            this.$el.append(tileView.render().el);
        }.bind(this));
        
        $('#backbone-tiles').sortable({
            start: function(event, ui){
                $('#moveTilesResult').html("");
                var startPos = ui.item.index();
                ui.item.data('startPos', startPos);
            },
            update: function(event, ui){
                $('#moveTilesResult').html("Loading...");
                var startPos = ui.item.data('startPos');
                var endPos = ui.item.index();
                var tileMover = new TileCollection();
                tileMover.moveTileToPosition(tileMover, endPos, tiles[startPos].attributes.id);
            },
        });
        $('#backbone-tiles').selectable(

        );
        return this;
    },
});

var SwapView = Backbone.View.extend({
    el: $('#swapTiles'),

    events: {
        "click #swapButton": "swapTilePositions",
        "click #refreshButton": "refreshPage",
    },

    swapTilePositions: function(){
        var tile1 = document.getElementById('tile1').value;
        var tile2 = document.getElementById('tile2').value;
        var tileSwapper = new TileCollection();
        try {
            tileSwapper.swapTile(tileSwapper, tile1, tile2);
        }
        catch (e) {
            $('#swapResult').html(e);
        }
    },

    refreshPage: function(){
        window.location.reload();
    },
})

function collectionFetch(){
    tileCollection.fetch().done(function(){
        tiles = tileCollection.models;
        ordered = tileCollection.checkOrdered();
    });
}

$(function(){
    var swapView = new SwapView();
    tileCollection = new TileCollection();
    tileCollection.fetch().done(function(){
        tiles = tileCollection.models;
        ordered = tileCollection.checkOrdered();
        tilesView = new TileCollectionView;
    });
})
