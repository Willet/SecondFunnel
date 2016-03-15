"use strict";

var tileCollection,   //Collection of all tiles
    tilesView,        //View of all tiles
    apiURL = "http://" + window.location.host + "/api2/";

var Tile = Backbone.Model.extend({
    defaults: {},

    initialize: function () {

    },
});

var TileCollection = Backbone.Collection.extend({
    defaults: {},

    url: apiURL + 'tile?page=' + pageID,

    model: Tile,

    initialize: function () {

    },

    parse: function (response) {
        return response;
    },

    getCustomURL: function (method) {
        /** 
        Returns the API URL for REST methods for different methods

        inputs:
            method: name of the method

        output:
            URL for REST method
        **/
        switch (method) {
            case 'swapTile':
                return apiURL + 'tile';
            case 'moveTile':
                return apiURL + 'tile';
        }
    },

    moveTileToPosition: function (tileID, index) {
        /**
        Move the tile with ID specified to index location

        inputs:
            tileID: ID of tile to be moved
            index: index to move tile to, with index = 0 indicating 1st item of list of tiles
        **/
        var diff, prioDiff, options, moveTileCollection, result,
            batch = [],
            tiles = tileCollection.models,
            tileInd = tileCollection.findIndexWhere({'id': parseInt(tileID)});
        // First check if the index we're moving to is on the left or right of original tile index
        // Then insert/delete appropriately

        if (index < tileInd) {
            tiles.splice(index, 0, tiles[tileInd]);
            tiles.splice(tileInd + 1, 1);
        } else {
            tiles.splice(index + 1, 0, tiles[tileInd]);
            tiles.splice(tileInd, 1);
        }

        //Check if Tn+1 exists or not
        if (index === tiles.length - 1) {
            //Tn+1 doesn't exist
            tiles[index].set({priority: 1});
            batch.push({
                'id': tiles[index].get('id'), 
                'priority': tiles[index].get('priority')
            });
            //No need to do anything else to Tn+1 till the end
        } else {
            //Tn+1 exists
            tiles[index].set({priority: tiles[index+1].get('priority') + 1});
            batch.push({
                'id': tiles[index].get('id'), 
                'priority': tiles[index].get('priority')
            })
            //Check if Tn+2 exists or not
            if (index + 1 !== tiles.length - 1) {
                //Tn+2 exists
                //The priority of Tn+2 onwards doesn't change

                //Check Tn+1 > Tn+2
                if (tiles[index + 1].get('priority') > tiles[index + 2].get('priority')) {
                    //it's greater so this doesn't need to change
                } else {
                    //Tn+1 = Tn+2, so increase Tn+1 by 1
                    tiles[index + 1].set({priority: tiles[index + 1].get('priority')+ 1});
                    batch.push({
                        'id': tiles[index + 1].get('id'), 
                        'priority': tiles[index + 1].get('priority')
                    });
                }
            }

            //Check Tn > Tn+1
            if (tiles[index].get('priority') <= tiles[index + 1].get('priority')) {
                //Tn <= Tn+1, so set Tn to be Tn+1 + 1
                tiles[index].set({priority: tiles[index + 1].get('priority') + 1});
                batch.push({
                    'id': tiles[index].get('id'), 
                    'priority': tiles[index].get('priority')
                });
            }
        }

        //now Tn to the end is correctly set, need to do from T0 to Tn-1

        //Check Tn-1 exist
        if (index - 1 >= 0) {
            //Tn-1 exists

            //Check Tn-1 > Tn
            if (tiles[index - 1].get('priority') <= tiles[index].get('priority')) {
                //Tn-1 <= Tn
                tiles[index - 1].set({priority: tiles[index].get('priority') + 1});
                batch.push({
                    'id': tiles[index - 1].get('id'), 
                    'priority': tiles[index - 1].get('priority')
                });
            }

            //Check Tn-2 exists
            if (index - 2 >= 0) {
                //Tn-2 exists
                //Check if Tn-2 > Tn-1
                if (tiles[index - 2].get('priority') > tiles[index - 1].get('priority')) {
                    //Tn-2 > Tn-1
                    //Tn-2 to the beginning doesn't need to change as it's already
                    //    at that position
                } else {
                    //Tn-2 <= Tn-1
                    //Increase Tn-2 to T0 by X amount so Tn-2 is on the left of Tn-1

                    //Find the difference between Tn-2 and Tn-1
                    diff = tiles[index - 1].get('priority') - tiles[index - 2].get('priority');
                    //Find how much to increase the priority by, which should be 1 more than
                    //   the difference in priorities so that the final prio will be at least
                    //   1 more than the Tn-1
                    prioDiff = diff + 1;
                    //Now loop through and increase from T0 to Tn-2
                    for (var i = index - 2; i >= 0; i--) {
                        tiles[i].set({priority: tiles[i].get('priority') + prioDiff});
                        batch.push({
                            'id': tiles[i].get('id'), 
                            'priority': tiles[i].get('priority')
                        });
                    }
                }
            }
        }

        batch = JSON.stringify(batch);

        options = {
            'url': this.getCustomURL('moveTile'),
        };

        moveTileCollection = new TileCollection();
        moveTileCollection.set({data: batch});

        result = Backbone.sync.call(this, 'patch', moveTileCollection, options);
        result.always(function () {
            tileCollection.sort();
            if (result.responseJSON.length !== 0) {
                status = "The tile with ID: " + tileID + " has been moved to index: "
                         + index + ". Refreshing tiles.";
            } else {
                status = "Move failed due to an error.";
            }
            $('#moveTilesResult').html(status);
        })
    },

    findIndexWhere: _.compose(Backbone.Collection.prototype.indexOf, Backbone.Collection.prototype.findWhere),

    comparator: function (a, b) {
        if (a.get("priority") > b.get("priority")) {
            return -1;
        }
        if (a.get("priority") < b.get("priority")) {
            return 1;
        }
        if (a.get("priority") === b.get("priority")) {
            return 0;
        }
    },
});

var TileView = Backbone.View.extend({
    template: _.template($('#tile-template').html()),

    tagName: 'li',

    className: 'tile-list sortable',

    initialize: function (args) {

    },

    render: function () {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },

    events: {
        "click #editTile": "editTile",
    },

    editTile: function () {
        /**
        Change the tile's priority to the value specified inside the input box
        **/
        var result,
            currModel = this.model,
            newPriority = document.getElementById('new_priority_' + currModel.id).value;

        try {
            if (newPriority === '' || newPriority === null) {
                throw "Error. New priority input is empty."
            }
            if (isNaN(parseInt(newPriority))) {
                throw "Error. A valid integer is required."
            }
            $('#modal_' + currModel.id).modal('toggle');
            $('#moveTilesResult').html("Processing... Please wait.");

            result = currModel.save({priority: newPriority}, {
                patch: true,
                url: apiURL + 'tile/' + currModel.id + '/',
            });
            result.always(function () {
                tileCollection.sort();
                result = JSON.parse(result.responseText);
                if (_.has(result,"id")) {
                    status = "The priority of tile with ID: " + currModel.id + 
                             " has been changed to " + currModel.get('priority') + ".";
                } else {
                    status = result.priority;
                }
                $('#moveTilesResult').html(status);
            });
        }
        catch(err) {
            $('#error_' + currModel.id).html(err);
        }
    },
});

var TileCollectionView = Backbone.View.extend({
    el: "#backbone-tiles",

    initialize: function () {
        this.render();
        this.listenTo(this.collection, 'change add sort', _.debounce(this.render, 100));
    },

    render: function () {
        this.$el.html('');

        this.collection.each(function (model) {
            var tileView = new TileView({
                model: model,
            });
            this.$el.append(tileView.render().el);
        }.bind(this));
        
        $('#backbone-tiles').sortable({
            handle: ".handle",

            start: function (event, ui) {
                var startPos = ui.item.index();
                $('#moveTilesResult').html("");
                ui.item.data('startPos', startPos);
            },

            update: function (event, ui) {
                var startPos = ui.item.data('startPos'),
                    endPos = ui.item.index(),
                    movedTileID = tileCollection.models[startPos].get('id');
                $('#moveTilesResult').html("Processing... Please wait.");
                tileCollection.moveTileToPosition(movedTileID, endPos);
            },
        });
        // $('#backbone-tiles').selectable({
        //     filter: "li",
        //     cancel: ".handle"
        // });
        return this;
    },
});

$(function () {
    tileCollection = new TileCollection();
    tileCollection.fetch();
    tilesView = new TileCollectionView({ collection: tileCollection });
    tilesView.render();
})
