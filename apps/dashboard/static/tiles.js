"use strict";

Backbone.View.prototype.unwrapEl = function () {
    this.$el = this.$el.children();
    this.$el.unwrap();
    this.setElement(this.$el);
}

var App = Marionette.Application.extend({
    regions: {
        tiles: "#tiles",
        modal: "#modal",
        feedback: "#feedback",
    },

    initialize: function () {
        var tiles = new App.core.TileCollection();    //Collection of all tiles
        this.tiles.show(new App.core.TileCollectionView({ collection: tiles })); //View of all tiles
    },
});

App.core = {};

App.core.apiURL = "http://" + window.location.host + "/api2/";

App.core.Tile = Backbone.Model;

App.core.TileCollection = Backbone.Collection.extend({
    defaults: {},

    url: App.core.apiURL + 'tile?page=' + pageID,

    model: App.core.Tile,

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
                return App.core.apiURL + 'tile';
            case 'moveTile':
                return App.core.apiURL + 'tile';
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
            tiles = this.models,
            tileInd = this.findIndexWhere({'id': parseInt(tileID)});

        // First clone the tiles:
        _.each(tiles, function(val, i){ tiles[i] = val.clone(); });

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

        //Change tiles's models to have new priorities by looping through batch
        _.each(batch, function(val){
            var index = App.tiles.findIndexWhere({'id': parseInt(val['id'])});
            App.tiles.models[index].set({priority: val['priority']});
        });

        batch = JSON.stringify(batch);
        options = {
            'url': this.getCustomURL('moveTile'),
        };

        moveTileCollection = new App.core.TileCollection();
        moveTileCollection.set({data: batch});

        result = Backbone.sync.call(this, 'patch', moveTileCollection, options);
        result.always(function () {
            App.tiles.sort();
            if (result.responseJSON.length !== 0) {
                status = "The tile with ID: " + tileID + " has been moved to index: "
                         + index + ". Refreshing tiles.";
            } else {
                status = "Move failed due to an error.";
            }
            $('#tilesResult').html(status);
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

App.core.FeedbackView = Marionette.ItemView.extend({
    template: _.template($('#feedback-template').html()),

    initialize: function (options) {
        /* Wait 10s before removing the alert */
        setTimeout(function () { app.feedback.empty(); }, 10000);
    },

    templateHelpers: function () {
        return this.options;
    },
});

App.core.EditModalView = Marionette.ItemView.extend({
    template: _.template($('#edit-modal-template').html()),

    ui: {
        "close": "button#closeButton",
        "change": "button#editTile",
    },

    events: {
        "click @ui.close": "closeModal",
        "click @ui.change": "changePriority",
    },

    closeModal: function () {
        this.$el.modal('toggle');
    },

    changePriority: function () {
        var result, status, alertType, feedbackModel,
            currModel = this.model,
            newPriority = document.getElementById('new_priority').value;

        try {
            if (newPriority === '' || newPriority === null) {
                throw "Error. New priority input is empty."
            }
            if (!(Math.floor(newPriority) == newPriority && $.isNumeric(newPriority))) {
                throw "Error. A valid integer is required."
            }
            this.$el.modal('toggle');

            alertType = 'info';
            status = 'Processing... Please wait.';

            app.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));

            result = currModel.save({priority: newPriority}, {
                patch: true,
                url: App.core.apiURL + 'tile/' + currModel.id + '/',
            });

            result.always(function () {
                result = JSON.parse(result.responseText);
                if (_.has(result,"id")) {
                    alertType = 'success';
                    status = "The priority of tile with ID: " + currModel.id + 
                             " has been changed to " + currModel.get('priority') + ".";
                } else {
                    alertType = 'danger';
                    status = result.priority;
                }
                app.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));
            });
        }
        catch(err) {
            $('#editError').html(err);
        }
    },

    onRender: function () {
        this.unwrapEl();
        this.$el.modal('toggle');
    },
});

App.core.RemoveModalView = Marionette.ItemView.extend({
    template: _.template($('#remove-modal-template').html()),

    ui: {
        "close": "button#closeButton",
        "delete": "button#removeTile",
    },

    events: {
        "click @ui.close": "closeModal",
        "click @ui.delete": "deleteTile",
    },

    closeModal: function () {
        this.$el.modal('toggle');
    },

    deleteTile: function () {
        /** 
        Remove the tile from the page
        **/
        var result, status, alertType, feedbackModel,
            currModel = this.model,
            modelID = currModel.id;
        this.$el.modal('toggle');

        alertType = 'info';
        status = 'Processing... Please wait.';

        app.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));

        result = currModel.destroy({
            url: App.core.apiURL + 'tile/' + modelID + '/',
        });
        result.always(function () {
            if (result.status == 200) {
                alertType = 'success';
                status = "The tile with ID: " + currModel.id + 
                             " has been deleted.";
            }
            else {
                alertType = 'danger';
                status = JSON.parse(result.responseText);
            }
            app.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));
        })
    },

    onRender: function () {
        this.unwrapEl();
        this.$el.modal('toggle');
    },
});

App.core.TileView = Marionette.ItemView.extend({
    template: _.template($('#tile-template').html()),

    tagName: 'li',

    className: 'tile sortable',

    ui: {
        "remove": "button.remove",
        "content": ".content",
    },

    events: {
        "click @ui.remove": "removeModal",
        "click @ui.content": "editModal",
        "click @ui.contentClose": "closeModal",
    },

    removeModal: function () {
        app.modal.show(new App.core.RemoveModalView({ model: this.model }));
    },

    editModal: function () {
        app.modal.show(new App.core.EditModalView({ model: this.model }));
    },

    /* Need to make click remove open up modal */

    removeTile: function() {
    },
});

// App.core.PageCompositeView = Marionette.CompositeView.extend({
//     template: "#page-template",


// });

App.core.TileCollectionView = Marionette.CollectionView.extend({
    el: "#backbone-tiles",

    childView: App.core.TileView,

    initialize: function () {
        this.collection.fetch();
        this.listenTo(this.collection, 'add', _.debounce(function () { 
            $('#loading-spinner').hide(); 
            $('#add-remove').show(); 
        }, 100));
        this.listenTo(this.collection, 'change destroy', _.debounce(function () {this.collection.sort();}, 100));
        this.listenTo(this.collection, 'sort', _.debounce(this.render, 100));
    },

    onShow: function () {
        $('#backbone-tiles').sortable({
            start: function (event, ui) {
                var startPos = ui.item.index();
                app.feedback.empty();
                ui.item.data('startPos', startPos);
            },

            update: function (event, ui) {
                console.log(this);
                var alertType, status,
                    startPos = ui.item.data('startPos'),
                    endPos = ui.item.index(),
                    movedTileID = app.tiles.currentView.collection.models[startPos].get('id');
                console.log(startPos);
                console.log(endPos);
                console.log(movedTileID);

                alertType = 'info';
                status = 'Processing... Please wait.';
                app.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));

                App.tiles.moveTileToPosition(movedTileID, endPos);
            },
        });
    },
});

var app = new App();
app.start();
