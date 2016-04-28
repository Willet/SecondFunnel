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
        controlBar: "#controlBar",
    },

    initialize: function () {
        /**
        Initialize the App. Create a tile collection, call a fetch on it,
        and set up the categories collection then draw all tiles
        **/
        var tiles = new App.core.TileCollection();    //Collection of all tiles

        tiles.fetch().done(function () {
            $('#loading-spinner').hide();

            App.controlBar.show(new App.core.ControlBarView());
            App.categories = new App.core.Categories();
            App.categories.fetch();
            App.categoriesView = new App.core.CategoriesView({ collection: App.categories });
            App.categoriesView.render();
        });
        this.tiles.show(new App.core.TileCollectionView({ collection: tiles })); //View of all tiles
    },
});

App.core = {};

App.core.apiURL = "http://" + window.location.host + "/api2/";

App.core.ObjectCollection = Backbone.Collection.extend({
    defaults: {},

    parse: function (response) {
        return response;
    },

    comparator: function (a, b) {
        /**
        Comparator used when sorting products, sort from highest product ID at top
        to lowest product ID at bottom
        **/
        if (a.get("id") > b.get("id")) {
            return -1;
        }
        if (a.get("id") < b.get("id")) {
            return 1;
        }
        if (a.get("id") === b.get("id")) {
            return 0;
        }
    },
});

App.core.ProductCollection = App.core.ObjectCollection.extend({
    url: App.core.apiURL + 'page/' + pageID + '/products/',
});

App.core.ContentCollection = App.core.ObjectCollection.extend({
    url: App.core.apiURL + 'page/' + pageID + '/contents/',
});

App.core.TileContentCollection = App.core.ObjectCollection.extend({
    url: App.core.apiURL + 'content/search/',
});

App.core.TileProductCollection = App.core.ObjectCollection.extend({
    url: App.core.apiURL + 'product/search/',
});

App.core.TileProductImageCollection = App.core.ObjectCollection.extend({
    url: App.core.apiURL + 'productimage/search/',
});

App.core.TileCollection = Backbone.Collection.extend({
    defaults: {},

    url: App.core.apiURL + 'tile?page=' + pageID,

    model: Backbone.Model,

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
        var diff, prioDiff, options, moveTileCollection, result, alertType,
            batch           = [],
            tileCollection  = this,
            tiles           = this.models,
            tileInd         = this.findIndexWhere({'id': parseInt(tileID)});

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
            var index = tileCollection.findIndexWhere({'id': parseInt(val['id'])});
            tileCollection.models[index].set({priority: val['priority']});
        });

        batch = JSON.stringify(batch);
        options = {
            'url': this.getCustomURL('moveTile'),
        };

        moveTileCollection = new App.core.TileCollection();
        moveTileCollection.set({data: batch});

        result = Backbone.sync.call(this, 'patch', moveTileCollection, options);
        result.always(function () {
            tileCollection.sort();
            if (result.responseJSON.length !== 0) {
                alertType = 'success';
                status = "The tile with ID: " + tileID + " has been moved to index: "
                         + index + ". Refreshing tiles.";
            } else {
                alertType = 'danger';
                status = "Move failed due to an error.";
            }
            App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));
        })
    },

    findIndexWhere: _.compose(Backbone.Collection.prototype.indexOf, Backbone.Collection.prototype.findWhere),

    comparator: function (a, b) {
        /**
        Comparator used when sorting tiles, sort by decreasing priority.
        If priority is the same, sort by placeholder status.
        **/
        if (a.get("priority") > b.get("priority")) {
            return -1;
        }
        if (a.get("priority") < b.get("priority")) {
            return 1;
        }
        if (a.get("priority") === b.get("priority")) {
            if ( (a.get("placeholder") === true) && (b.get("placeholder") === false) ) { 
                return 1;
            } else {
                if ( (a.get("placeholder") === false) && (b.get("placeholder") === true) ) {
                    return -1;
                } else {
                    return 0;
                }
            }
        }
    },
});

App.core.Tile = Backbone.Model.extend({
    defaults: {},

    urlRoot: App.core.apiURL,

    getCustomURL: function (method, tileID) {
        /**
        Returns the API URL for REST methods for different methods

        inputs:
            method: name of the method

        output:
            URL for REST method
        **/
        switch (method) {
            case 'tag':
                return App.core.apiURL + 'tile/' + tileID + '/' + method;
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    tag: function (tagObject, tileID) {
        /**
        Calls for a tag of the tile by doing a Backbone.sync to API server

        inputs:
            tagObject: containing the tag information (Products/Content IDs)

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('tag', tileID),
        };
        return Backbone.sync.call(this, 'create', tagObject, options);
    },   
});

App.core.TileView = Marionette.ItemView.extend({
    template: _.template($('#tile-template').html()),

    tagName: 'li',

    className: 'tile sortable',

    events: {
        "click button.remove": "removeModal",
        "click button.add-side-buttons-left": "addLeft",
        "click button.add-side-buttons-right": "addRight",
        "click .content": "editModal",
    },

    addLeft: function () {
        // If we're adding to the left, we need to check then shift all tiles to the left up by 1
        //   if its current priority can't fit an extra tile
        // New tile priority will always be the current tile+1 so that it'll be on the left
        // Once the batch file and new priority is determined, draw the modal displayed when the 
        //   add tile to left button is clicked
        var diff,
            batch = [],
            tileCollection = this._parent.collection,
            tiles = tileCollection.models,
            tilePriority = this.model.get('priority'),
            tileInd = tileCollection.findIndexWhere({'id': parseInt(this.model.get('id'))}),
            newTilePriority = tilePriority + 1;

        if ( (tileInd !== 0) && (tiles[tileInd - 1].get('priority') <= tilePriority + 1) ){
            // This means the tiles on the left is either same priority or has prio = ind + 1
            // So need to +1 to priority of everything to the beginning 

            // First clone the tiles:
            _.each(tiles, function(val, i){ tiles[i] = val.clone(); });

            // Find the amount that the tiles' priority need to be incremented by
            diff = 2 - (tiles[tileInd-1].get('priority') - tilePriority);
            // Now shift prio of everything with ind-1 up by 2
            for (var i = tileInd-1; i >= 0; i--) {
                tiles[i].set({priority: tiles[i].get('priority') + diff});
                batch.push({
                    'id': tiles[i].get('id'),
                    'priority': tiles[i].get('priority')
                });
            }
        }

        App.modal.show(new App.core.AddObjectModalView({
            newTilePriority: newTilePriority,
            batch: batch,
        }));
    },

    addRight: function () {
        // Draw the modal displayed when the add tile to left is clicked
        // If we're adding to the right, need to check then shift all tiles from tile ind to beginning by 1
        //   if its current priority can't fit an extra tile
        // New tile priority will always be the tileInd+1's priority+1 so it'll be on the right
        // Once the batch file and new priority is determined, draw the modal displayed when the 
        //   add tile to left button is clicked
        var diff, newTilePriority,
            batch = [],
            tileCollection = this._parent.collection,
            tiles = tileCollection.models,
            tilePriority = this.model.get('priority'),
            tileInd = tileCollection.findIndexWhere({'id': parseInt(this.model.get('id'))});

        if (tileInd !== tiles.length - 1) {
            newTilePriority = tiles[tileInd+1].get('priority') + 1;

            if ((tilePriority === tiles[tileInd+1].get('priority')) || (tilePriority === tiles[tileInd+1].get('priority') + 1)) {
                // This means the tiles from curr ind to 0 has either same priority as ind+1 or +1 of ind+1
                // So need to + the difference from tileInd to beginning so tileInd is +2 of ind+1's priority

                // First clone the tiles:
                _.each(tiles, function(val, i){ tiles[i] = val.clone(); });

                // Find the amount that the tiles' priority need to be incremented by
                diff = 2 - (tilePriority - tiles[tileInd+1].get('priority'));
                // Now shift prio of everything from tileInd up by the difference
                for (var i = tileInd; i >= 0; i--) {
                    tiles[i].set({priority: tiles[i].get('priority') + diff});
                    batch.push({
                        'id': tiles[i].get('id'),
                        'priority': tiles[i].get('priority')
                    });
                }
            }
        } else {
            // If tile is at the end, just set newTilePriority to be tileInd - 1 so it's on the right
            newTilePriority = tilePriority - 1;
        }

        App.modal.show(new App.core.AddObjectModalView({
            newTilePriority: newTilePriority,
            batch: batch,
        }));
    },

    removeModal: function () {
        //Draw the modal displayed when the Remove button is clicked
        App.modal.show(new App.core.RemoveModalView({ model: this.model }));
    },

    editModal: function () {
        // Draw the modal displayed when the tile is clicked on
        App.modal.show(new App.core.EditModalView({ model: this.model }));
    },
});

App.core.TileCollectionView = Marionette.CollectionView.extend({
    el: "#backbone-tiles",

    childView: App.core.TileView,

    initialize: function () {
        // Initialize the tile collection by setting the listenTo's
        this.listenTo(this.collection, 'change destroy', _.debounce(function () {this.collection.sort();}, 100));
        this.listenTo(this.collection, 'sort', _.debounce(this.render, 100));
    },

    onShow: function () {
        // Make the tiles in the collection sortable.
        $('#backbone-tiles').sortable({
            start: function (event, ui) {
                var startPos = ui.item.index() - 1;
                App.feedback.empty();
                ui.item.data('startPos', startPos);
            },

            update: function (event, ui) {
                var startPos = ui.item.data('startPos'),
                    endPos = ui.item.index() - 1,
                    movedTileID = App.tiles.currentView.collection.models[startPos].get('id');

                App.feedback.show(new App.core.FeedbackView({
                    'alertType': 'info',
                    'status': 'Processing... Please wait.'
                }));

                App.tiles.currentView.collection.moveTileToPosition(movedTileID, endPos);
            },
        });
    },
});

App.core.FeedbackView = Marionette.ItemView.extend({
    template: _.template($('#feedback-template').html()),

    initialize: function (options) {
        // Wait 10s before removing the alert
        setTimeout(function () { App.feedback.empty(); }, 10000);
    },

    templateHelpers: function () {
        return this.options;
    },
});

App.core.FeedbackNoTimeoutView = App.core.FeedbackView.extend({
    // Identical to FeedbackView except there are no timeouts after 10s
    initialize: function (options) {

    },
});

App.core.BaseModalView = Marionette.ItemView.extend({
    // BaseModalView: Contains the shared modal functions.

    closeModal: function () {
        // Close the modal by hiding it
        this.$el.modal('hide'); // Toggle Bootstrap modal to hide
    },

    onRender: function () {
        /**
        Unwrap the modal from backbone's default wrapper (div).
        Show the modal by toggling its status to show.
        **/
        this.unwrapEl();
        this.$el.modal('show'); // Toggle Bootstrap modal to show
    },

    templateHelpers: function () {
        return this.options;
    },
});

App.core.EditModalView = App.core.BaseModalView.extend({
    template: _.template($('#edit-modal-template').html()),

    onRender: function () {
        var products, tileProducts, productImages, tileProductImages, contents, tileContents, result,
            productIDs = [],
            productImageIDs = [],
            contentIDs = [],
            that = this;

        App.feedback.show(new App.core.FeedbackNoTimeoutView({
            'alertType': 'info',
            'status': "Fetching product and content info..."
        }));
        App.productsList = new App.core.ProductCollection();
        App.productsList.fetch().done(function () {
            App.productsList.sort();

            App.contentsList = new App.core.ContentCollection();
            App.contentsList.fetch().done(function () {
                App.contentsList.sort();
                
                // Fetch tile content pictures
                if (that.options.model.get('template') === 'product') {
                    products = that.options.model.get('products');
                    _.each(products, function(val) {
                        productIDs.push(val.id);
                    });
                    tileProducts = new App.core.TileProductCollection();
                    result = tileProducts.fetch({
                        traditional: true,
                        data: {
                            store: storeID, 
                            ids: JSON.stringify(productIDs),
                        }
                    }).done(function () {
                        if (result.status === 200) {
                            result = JSON.parse(result.responseText);
                            // Products take images from productImages, so we need to grab the images now
                            var productImages = [];

                            _.each(result.products, function (val) {
                                productImages.push(val.default_image);
                            });

                            tileProductImages = new App.core.TileProductImageCollection();
                            result = tileProductImages.fetch({
                                tradition: true,
                                data: {
                                    ids: JSON.stringify(productImages),
                                }
                            }).done(function () {
                                if (result.status === 200) {
                                    result = JSON.parse(result.responseText);

                                    that.processImageSlider(result.productImages);

                                    App.feedback.empty();
                                    that.unwrapEl();
                                    that.$el.modal('show'); // Toggle Bootstrap modal to show
                                    that.populateMultiSelectProduct('#object-selector-product');
                                    that.populateMultiSelectContent('#object-selector-content'); 
                                } else {
                                    that.hideAndShowFeedback('warning', result.responseText);
                                }
                            });
                        } else {
                            that.hideAndShowFeedback('warning', result.responseText);
                        }
                    });
                } else {
                    contents = that.options.model.get('content'),
                    _.each(contents, function(val) {
                        contentIDs.push(val.id);
                    });
                    tileContents = new App.core.TileContentCollection(),
                    result = tileContents.fetch({
                        traditional: true,
                        data: {
                            store: storeID, 
                            ids: JSON.stringify(contentIDs),
                        },
                    }).done(function () {
                        if (result.status === 200) {
                            result = JSON.parse(result.responseText);

                            that.processImageSlider(result.contents);

                            App.feedback.empty();
                            that.unwrapEl();
                            that.$el.modal('show'); // Toggle Bootstrap modal to show
                            that.populateMultiSelectProduct('#object-selector-product');
                            that.populateMultiSelectContent('#object-selector-content');
                        } else {
                            that.hideAndShowFeedback('warning', result.responseText);       
                        }
                    });
                }
            })
        });
    },

    processImageSlider: function (result) {
        var that = this,
            tileDefaultImage = that.options.model.get('defaultImage');

        if (result.length > 1) {
            _.each(result, function (val, i) {
                var tileID;
                if (that.options.model.get('template') === 'product') {
                    tileID = that.options.model.get('products')[i].id;
                } else {
                    tileID = val.id;
                }
                that.$el.find('#edit-slider ul').append(
                    '<li id="' + val.id + ' "><div class="image-label">' + tileID +'</div><img class="edit-modal-image" src="' + val.url + '" alt="' + tileID + '"></li>'
                );
            });
        } else {
            if (result.length === 0) {
                that.$el.find('#edit-slider ul').append('<li></li>');
                that.$el.find('#edit-slider ul').append('<li></li>');
            } else {
                var tileID;
                if (that.options.model.get('template') === 'product') {
                    tileID = that.options.model.get('products')[0].id;
                } else {
                    tileID = result[0].id;
                }
                that.$el.find('#edit-slider ul').append(
                    '<li id="' + result[0].id + ' "><div class="image-label">' + tileID + '</div><img class="edit-modal-image" src="' + result[0].url + '" alt="' + tileID + '"></li>'
                );
                that.$el.find('#edit-slider ul').append(
                    '<li id="' + result[0].id + ' "><div class="image-label">' + tileID + '</div><img class="edit-modal-image" src="' + result[0].url + '" alt="' + tileID + '"></li>'
                );
            }
        }

        var slider = that.$el.find('#edit-slider'),
            sliderUl = that.$el.find('#edit-slider ul'),
            sliderUlLi = that.$el.find('#edit-slider ul li'),
            sliderLastChild = that.$el.find('#edit-slider ul li:last-child'),
            sliderFirstChild = that.$el.find('#edit-slider ul li:first-child'),

            slideCount = sliderUlLi.length,
            slideWidth = sliderUlLi.width(),
            slideHeight = sliderUlLi.height(),
            sliderUlWidth = slideCount * slideWidth;

        slider.css({ width: slideWidth, height: slideHeight });
        sliderUl.css({ width: sliderUlWidth, marginLeft: - slideWidth });
        sliderLastChild.prependTo(sliderUl);

        function moveLeft () {
            sliderUl.animate({
                left: + slideWidth
            }, 200, function () {
                that.$el.find('#edit-slider ul li:last-child').prependTo(sliderUl);
                sliderUl.css('left', '');
            });
        };
        function moveRight () {
            $('#edit-slider ul').animate({
                left: - slideWidth
            }, 200, function () {
                that.$el.find('#edit-slider ul li:first-child').appendTo(sliderUl);
                sliderUl.css('left', '');
            });
        };

        $('a.control_prev').click(function () {
            moveLeft();
        });
        $('a.control_next').click(function () {
            moveRight();
        });
    },

    populateMultiSelectProduct: function (divName) {
        var selection, num,
            currentModel = this.model,
            that = this;

        that.$el.find(divName).multiSelect({
            selectableHeader:   "<div class='custom-header'>List of Products</div>",

            selectionHeader:    "<div class='custom-header'>Products to be Tagged</div>",

            afterInit: function(ms){
                var typingTimer, data, result, productsList,
                    those = this,
                    selectableSearch = that.$el.find('input[name=num]');

                _.each(App.productsList.models, function (val) {
                    var modelID = val.get('id'),
                        modelName = val.get('name');
                    that.$el.find(divName).multiSelect('addOption', { 
                        value: modelID, 
                        text: modelID + ' - ' + modelName,
                    });
                });

                selectableSearch.keyup(function(){
                    clearTimeout(typingTimer);
                    typingTimer = setTimeout(function () {
                        var selectedItems = [];

                        _.each(that.$el.find('#object-selector')[0].options, function (val) {
                            if (val.selected) {
                                selectedItems.push(val.value);
                            }
                        });

                        App.feedback.show(new App.core.FeedbackNoTimeoutView({
                            'alertType': 'info',
                            'status': "Fetching product info..."
                        }));
                        // Refresh products list by doing API call and refresh multiselect
                        selection = that.$el.find('.edit-modal-selection-field')[0].value;
                        num = that.$el.find('.edit-modal-num-field')[0].value;

                        data = {};
                        data[selection] = num;

                        productsList = new App.core.ProductCollection();
                        result = productsList.fetch({
                            data: data,
                        });
                        result.always(function () {
                            App.feedback.empty();
                            if (result.status === 200) {
                                App.productsList = productsList;
                                that.$el.find(divName).empty();
                                that.$el.find(divName).multiSelect('refresh');
                            } else {
                                App.feedback.show(new App.core.FeedbackNoTimeoutView({
                                    'alertType': 'warning',
                                    'status': JSON.parse(result.responseText).status,
                                }));
                            }
                        });
                    }, 2000);
                });
            },
        }); // Must run this before we can access
            //    multiSelect's options
    },

    populateMultiSelectContent: function(divName) {
        var selection, num,
            currentModel = this.model,
            that = this;

        that.$el.find(divName).multiSelect({
            selectableHeader:   "<div class='custom-header'>List of Contents</div>",

            selectionHeader:    "<div class='custom-header'>Contents to be Tagged</div>",

            afterInit: function(ms){
                var typingTimer, data, result, productsList,
                    those = this,
                    selectableSearch = that.$el.find('input[name=num]');

                _.each(App.contentsList.models, function (val) {
                    var modelID = val.get('id'),
                        modelName = val.get('name');
                    that.$el.find(divName).multiSelect('addOption', { 
                        value: modelID, 
                        text: "Content " + modelID,
                    });
                });

                selectableSearch.keyup(function(){
                    clearTimeout(typingTimer);
                    typingTimer = setTimeout(function () {
                        var selectedItems = [];

                        _.each(that.$el.find('#object-selector')[0].options, function (val) {
                            if (val.selected) {
                                selectedItems.push(val.value);
                            }
                        });

                        App.feedback.show(new App.core.FeedbackNoTimeoutView({
                            'alertType': 'info',
                            'status': "Fetching contents info..."
                        }));
                        // Refresh products list by doing API call and refresh multiselect
                        selection = that.$el.find('.edit-modal-selection-field')[0].value;
                        num = that.$el.find('.edit-modal-num-field')[0].value;

                        data = {};
                        data[selection] = num;

                        contentsList = new App.core.ContentCollection();
                        result = contentsList.fetch({
                            data: data,
                        });
                        result.always(function () {
                            App.feedback.empty();
                            if (result.status === 200) {
                                App.contentsList = contentsList;
                                that.$el.find(divName).empty();
                                that.$el.find(divName).multiSelect('refresh');
                            } else {
                                App.feedback.show(new App.core.FeedbackNoTimeoutView({
                                    'alertType': 'warning',
                                    'status': JSON.parse(result.responseText).status,
                                }));
                            }
                        });
                    }, 2000);
                });
            },
        }); // Must run this before we can access
            //    multiSelect's options
    },

    events: {
        "click button#saveChanges": "saveChanges",
        "click button.make-default-image": "makeDefaultImage",
        "click button#close": "closeModal",
    },

    makeDefaultImage: function () {
        console.log(this);
    },

    saveChanges: function () {
        var result, alertType, status, tile, 
            data = {},
            currModel = this.model,
            tileID = this.model.get('id'),
            newPriority = this.$el.find('#new-priority').val(),
            newTemplate = this.$el.find('#new-template').val(),
            newAttributes = this.$el.find('#attributes-textarea').val(),
            selectedProducts = [],
            selectedContents = [],
            that = this;

        App.feedback.show(new App.core.FeedbackNoTimeoutView({
            'alertType': 'info',
            'status': 'Processing... Please wait.'
        }));

        try {
            // Change priorities {priority: newPriority}
            if (newPriority !== this.model.get('priority')) {
                data['priority'] = newPriority;
            }
            // Change template
            if (newTemplate !== this.model.get('template')) {
                data['template'] = newTemplate;
            }
            // Change attributes
            JSON.parse(newAttributes);
            if (newAttributes !== this.model.get('attributes')) {
                data['attributes'] = newAttributes;
            }
            // Tag tiles
            _.each(this.$el.find('#object-selector-product')[0].options, function (val) {
                if (val.selected) {
                    selectedProducts.push(val.value);
                }
            });
            _.each(this.$el.find('#object-selector-content')[0].options, function (val) {
                if (val.selected) {
                    selectedContents.push(val.value);
                }
            });
            // Save attributes
            result = currModel.save(data, {
                patch: true,
                url: App.core.apiURL + 'tile/' + tileID + '/',
            });
            result.always(function () {
                result = JSON.parse(result.responseText);
                if (_.has(result,"id")) {
                    alertType = 'success';
                    status = "The attributes of the tile with ID " + tileID + " has been updated.";
                } else {
                    alertType = 'danger';
                    status = result.priority;
                }
                // tile attributes saving is done, now tag tiles
                tile = new App.core.Tile();
                tile.set({data: {
                    'pageID': pageID,
                    'products': selectedProducts,
                    'contents': selectedContents,
                }});

                result = tile.tag(tile, tileID);
                result.always(function () {
                    status = status + " " + JSON.parse(result.responseText)['detail'];
                    if (result.status === 200) {
                        location.reload();
                    } else {
                        alertType = 'warning';
                        that.hideAndShowFeedback(alertType, status);
                    }
                });
            });
        }
        catch (e) {
            App.feedback.empty();
            this.$el.find('#editError').html(e.message);
        }
    },

    hideAndShowFeedback: function (alertType, status) {
        App.feedback.empty();
        App.feedback.show(new App.core.FeedbackView({
            'alertType': alertType,
            'status': status
        }));
    },


});

App.core.RemoveModalView = App.core.BaseModalView.extend({
    template: _.template($('#remove-modal-template').html()),

    events: {
        "click button#closeButton": "closeModal",
        "click button#removeTile": "deleteTile",
    },

    deleteTile: function () {
        // Remove the tile from the page
        var result, status, alertType,
            currModel   = this.model,
            modelID     = currModel.id;
        this.$el.modal('hide'); // Toggle Bootstrap modal to hide

        App.feedback.show(new App.core.FeedbackNoTimeoutView({
            'alertType': 'info',
            'status': 'Processing... Please wait.'
        }));

        result = currModel.destroy({
            url: App.core.apiURL + 'tile/' + modelID + '/',
        });
        result.always(function () {
            if (result.status === 200) {
                alertType = 'success';
                status = "The tile with ID: " + currModel.id +
                             " has been deleted.";
            } else {
                alertType = 'danger';
                if (result.status === 404) {
                    status = "The tile with ID: " + currModel.id +
                                 " has already been deleted."
                } else {
                    var responseText = JSON.parse(result.responseText);
                    if ("detail" in responseText) {
                        status = responseText.detail;
                    } else {
                        status = responseText;
                    }
                }
            }
            App.feedback.empty();
            App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));
        })
    },
});

App.core.Categories = Backbone.Collection.extend({
    defaults: {},

    model: Backbone.Model,

    url: App.core.apiURL + 'page/' + pageID + '/',

    parse: function (response) {
        response.categories.unshift({'id': 0, name: 'View all tiles'});
        return response.categories;
    },
});

App.core.Product = Backbone.Model.extend({
    defaults: {},

    urlRoot: App.core.apiURL,

    getCustomURL: function (method) {
        /**
        Returns the API URL for REST methods for different methods

        inputs:
            method: name of the method

        output:
            URL for REST method
        **/
        switch (method) {
            case 'search':
                return App.core.apiURL + 'product/' + method + '/';
            case 'scrape':
                return App.core.apiURL + 'product/' + method + '/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    search: function (searchString) {
        /**
        Calls for a search of the object by doing a Backbone.sync to API server

        inputs:
            searchString: containing the search options (id/num/etc)

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('search'),
        };
        return Backbone.sync.call(this, 'create', searchString, options);
    },

    scrape: function (URL) {
        /**
        Calls for a scrape of the product by doing a Backbone.sync to API server

        inputs:
            URL: containing the URL to be scraped

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('scrape'),
        };
        return Backbone.sync.call(this, 'create', URL, options);
    }
});

App.core.Content = Backbone.Model.extend({
    defaults: {},

    urlRoot: App.core.apiURL,

    getCustomURL: function (method) {
        /**
        Returns the API URL for REST methods for different methods

        inputs:
            method: name of the method

        output:
            URL for REST method
        **/
        switch (method) {
            case 'search':
                return App.core.apiURL + 'content/' + method + '/';
            case 'scrape':
                return App.core.apiURL + 'content/' + method + '/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    search: function (searchString) {
        /**
        Calls for a search of the object by doing a Backbone.sync to API server

        inputs:
            searchString: containing the search options (id/num/etc)

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('search')
        };
        return Backbone.sync.call(this, 'create', searchString, options);
    },

    scrape: function (URL) {
        /**
        Calls for a scrape of the product by doing a Backbone.sync to API server

        inputs:
            URL: containing the URL to be scraped

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('scrape')
        };
        return Backbone.sync.call(this, 'create', URL, options);
    }
});

App.core.Page = Backbone.Model.extend({
    defaults: {
        selection: '',
        num: ''
    },

    urlRoot: App.core.apiURL,

    getCustomURL: function (method) {
        /**
        Returns the API URL for REST methods for different methods

        inputs:
            method: name of the method

        output:
            URL for REST method
        **/
        switch (method) {
            case 'add':
                return App.core.apiURL + 'page/' + pageID + '/' + method + '/';
            case 'remove':
                return App.core.apiURL + 'page/' + pageID + '/' + method + '/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    add: function (product) {
        /**
        Calls for a addition of the product by doing a Backbone.sync to API server

        inputs:
            product: containing the product to be added

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('add')
        };
        return Backbone.sync.call(this, 'create', product , options);
    },

    remove: function (product) {
        /**
        Calls for a removal of the product by doing a Backbone.sync to API server

        inputs:
            product: containing the product to be removed

        output:
            API server response
        **/
        var options = {
            'url': this.getCustomURL('remove')
        };
        return Backbone.sync.call(this, 'create', product , options);
    }
});

App.core.AddObjectModalView = App.core.BaseModalView.extend({
    template: _.template($('#add-object-template').html()),

    onRender: function () {
        // Once the add modal has been rendered, generate the form and add to the body of the modal.
        this.unwrapEl();

        var addObjectModel,
            objectType = this.options.objectType,
            newPriority = this.options.newTilePriority,
            that = this,
            selectionOptions = {
                'Product': ['URL', 'ID', 'SKU', 'Name'],
                'Content': ['URL', 'ID']
            };

        if ( (objectType == null) || (objectType == undefined) ){
            objectType = 'Product';
        }

        if (newPriority == null) {
            newPriority = 0;
        }

        addObjectModel = Backbone.Model.extend({
            schema: {
                selection:  { title: '', type: 'Select', options: selectionOptions[objectType] },
                num:        { title: '', type: 'Text' },
                category:   { title: 'Category', type: 'Text' },
                priority:   { title: 'Priority', type: 'Text' },
            },
            defaults: {
                selection: 'ID',
                priority: newPriority,
            },
        });

        this.addObjectInstance = new addObjectModel();

        this.addObjectForm = new Backbone.Form({
            template: _.template($('#add-form-template').html()),

            model: this.addObjectInstance,
        }).render();

        this.$el.find('.add-form').html(this.addObjectForm.el);
        
        this.$el.find('.modal-title').html("Add " + objectType);

        if (objectType === "Product") {
            App.feedback.show(new App.core.FeedbackNoTimeoutView({
                'alertType': 'info',
                'status': "Fetching all product info..."
            }));
            App.productsList = new App.core.ProductCollection();
            App.productsList.fetch().done(function () {
                App.productsList.sort();
                App.feedback.empty();

                that.populateMultiSelect('#object-selector', objectType + "s");
                that.$el.modal('show'); // Toggle Bootstrap modal to show
            });
        } else {
            App.feedback.show(new App.core.FeedbackNoTimeoutView({
                'alertType': 'info',
                'status': "Fetching all content info..."
            }));
            App.contentsList = new App.core.ContentCollection();
            App.contentsList.fetch().done(function () {
                App.contentsList.sort();
                App.feedback.empty();

                that.populateMultiSelect('#object-selector', objectType + "s");
                that.$el.modal('show'); // Toggle Bootstrap modal to show
            });
        }
    },

    events: {
        "click button#add": "addObject",
        "click button#close": "closeModal",
    },

    addObject: function () {
        // Add the object to the page.
        var result, idLength, responseText, alertType, status, selection, num, page, 
            searchString, priority, category, options, setTilePriorities, objectType,
            force_create,
            selected    = [],
            that        = this,
            batch       = this.options.batch;

        if ( (batch == null) || (batch == undefined) ){
            batch = [];
        }

        this.addObjectForm.commit();
        objectType      = this.options.objectType;
        priority        = this.addObjectInstance.get('priority');
        category        = this.addObjectInstance.get('category');
        selection       = this.addObjectInstance.get('selection');
        force_create    = $('#force-create').is(':checked').toString()

        _.each(that.$el.find('#object-selector')[0].options, function (val) {
            if (val.selected) {
                selected.push(val.value);
            }
        });

        if ( selected.length > 1 ) {
            App.feedback.show(new App.core.FeedbackView({
                'alertType': 'warning',
                'status': 'Choose only 1 object to add.'
            }));
        } else {
            App.feedback.show(new App.core.FeedbackNoTimeoutView({
                'alertType': 'info',
                'status': 'Processing... Please wait.'
            }));
            if ( ( selection === 'Name' ) && ( selected.length < 1 ) ){
                App.feedback.show(new App.core.FeedbackView({
                    'alertType': 'warning',
                    'status': 'Cannot add using Name.'
                }));
            } else {
                if ( selected.length < 1) {
                    num = this.addObjectInstance.get('num');
                } else {
                    selection = "ID";
                    num = selected[0];
                }

                if (num === '') {
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': 'warning',
                        'status': 'No ' + objectType.toLowerCase() + ' was selected or ID/SKU entered'
                    }));
                } else {
                    page = new App.core.Page({
                        selection: selection,
                        num: num,
                        priority: priority,
                        category: category
                    });
                    if (objectType === "Content") {
                        page.attributes.type = "content";
                        searchString = new App.core.Content();
                    } else {
                        page.attributes.type = "product";
                        searchString = new App.core.Product();
                    }

                    if (selection === 'URL') {
                        if (num.search('http') === -1) {
                            num = 'http://' + num;
                        }
                        searchString.set({url: num});
                    } else {
                        if (selection === 'ID') {
                            searchString.set({id: num});
                        } else {
                            if (selection === 'SKU') {
                                searchString.set({sku: num});
                            }
                        }
                    }

                    result = searchString.search(searchString);
                    result.always(function () {
                        responseText = JSON.parse(result.responseText);
                        idLength = responseText.ids.length;
                        if (idLength === 1) {
                            // object with that selection has been found

                            // Add the tile to the page with specified priority
                            if (objectType === "Product") {
                                page = new App.core.Page({
                                    type: "product",
                                    id: responseText.ids[0],
                                    force_create_tile: force_create,
                                });
                            } else {
                                page = new App.core.Page({
                                    type: "content",
                                    id: responseText.ids[0],
                                    force_create_tile: force_create,
                                });
                            }
                            if (priority !== "") {
                                page.set({priority: priority});
                            }
                            if (category !== "") {
                                page.set({category: category});
                            }
                            result = page.add(page);
                            result.always(function () {
                                App.feedback.empty();
                                responseText = JSON.parse(result.responseText);
                                status = responseText.status;
                                if (result.status === 200) {
                                    // Use batch to update the other tiles' priorities ONLY if adding
                                    //     was successful
                                    if (batch.length !== 0) {
                                        // Only do an API call if batch contains items to be updated
                                        batch = JSON.stringify(batch);
                                        options = {
                                            'url': App.tiles.currentView.collection.getCustomURL('moveTile'),
                                        };

                                        setTilePriorities = new App.core.TileCollection();
                                        setTilePriorities.set({data: batch});

                                        result = Backbone.sync.call(this, 'patch', setTilePriorities, options);
                                        result.always(function () {
                                            if (result.responseJSON.length !== 0) {
                                                // Patch of new tile priority successful
                                                location.reload();
                                            } else {
                                                alertType = 'danger';
                                                status = "Tile priority patching failed due to an error.";
                                                that.hideAndShowModal(that, alertType, status);
                                            }
                                        });
                                    } else {
                                        location.reload();
                                    }
                                } else {
                                    that.hideAndShowModal(that, 'warning', status);
                                }
                            });
                        } else {
                            if (idLength > 1) {
                                // Multiple objects found
                                App.feedback.show(new App.core.FeedbackView({
                                    'alertType': 'danger',
                                    'status': "Error: " + responseText.status
                                }));
                            } else {
                                // No object found
                                if ((selection === 'URL') && (responseText.status.indexOf("could not be found") >= 0)) {
                                    App.feedback.show(new App.core.FeedbackNoTimeoutView({
                                        'alertType': 'info',
                                        'status': "Object could not be found. Scraping..."
                                    }));
                                    if (objectType === "Product") {
                                        var processURL = new App.core.Product({
                                            url: num,
                                            page_id: pageID
                                        });
                                    } else {
                                        var processURL = new App.core.Content({
                                            url: num,
                                            page_id: pageID
                                        });
                                    }
                                    result = processURL.scrape(processURL);
                                    result.always(function () {
                                        App.feedback.empty();
                                        responseText = JSON.parse(result.responseText);
                                        if (result.status !== 200) {
                                            App.feedback.show(new App.core.FeedbackView({
                                                'alertType': 'danger',
                                                'status': responseText.status,
                                            }));
                                        } else {
                                            alertType = 'success';
                                            status = responseText.status + ". Creating tile.";
                                            App.feedback.show(new App.core.FeedbackNoTimeoutView({
                                                'alertType': alertType,
                                                'status': status,
                                            }));
                                            // Now add tile
                                            if (objectType === "Product") {
                                                page = new App.core.Page({
                                                    type: "product",
                                                    id: responseText.id,
                                                    force_create_tile: $('#force-create').is(':checked').toString(),
                                                });
                                            } else {
                                                page = new App.core.Page({
                                                    type: "content",
                                                    id: responseText.id,
                                                    force_create_tile: $('#force-create').is(':checked').toString(),
                                                });
                                            }
                                            if (priority !== "") {
                                                page.set({priority: priority});
                                            }
                                            if (category !== "") {
                                                page.set({category: category});
                                            }

                                            result = page.add(page);
                                            result.always(function () {
                                                App.feedback.empty();
                                                responseText = JSON.parse(result.responseText);
                                                status = responseText.status;
                                                if (result.status === 200) {
                                                    // Use batch to update the other tiles' priorities ONLY if adding
                                                    //     was successful
                                                    if (batch.length !== 0) {
                                                        // Only do an API call if batch contains items to be updated
                                                        batch = JSON.stringify(batch);
                                                        options = {
                                                            'url': App.tiles.currentView.collection.getCustomURL('moveTile'),
                                                        };

                                                        setTilePriorities = new App.core.TileCollection();
                                                        setTilePriorities.set({data: batch});

                                                        result = Backbone.sync.call(this, 'patch', setTilePriorities, options);
                                                        result.always(function () {
                                                            if (result.responseJSON.length !== 0) {
                                                                // Patch of new tile priority successful
                                                                location.reload();
                                                            } else {
                                                                alertType = 'danger';
                                                                status = "Tile priority patching failed due to an error.";
                                                            }
                                                            that.hideAndShowModal(that, alertType, status);
                                                            // Once scrape and add's successful, need to open the modal to edit it
                                                        });
                                                    } else {
                                                        location.reload();
                                                    }
                                                } else {
                                                    that.hideAndShowModal(that, 'warning', status);
                                                }
                                            });
                                        }
                                    })
                                } else {
                                    App.feedback.show(new App.core.FeedbackView({
                                        'alertType': 'warning',
                                        'status': responseText.status
                                    }));
                                }
                            }
                        }
                    });
                }
                
            }
        }
    },

    hideAndShowModal: function (instance, alertType, status) {
        instance.$el.modal('hide'); // Toggle Bootstrap modal to hide
        App.feedback.show(new App.core.FeedbackView({
            'alertType': alertType,
            'status': status
        }));
    },

    populateMultiSelect: function (divName, object) {
        var selection, num,
            objectType = this.options.objectType,
            that = this;

        that.$el.find(divName).multiSelect({
            selectableHeader:   "<div class='custom-header'>List of " + object + "</div>",

            selectionHeader:    "<div class='custom-header'>" + object + " to be Added</div>",

            afterInit: function(ms){
                var typingTimer, data, result, objectsList,
                    those = this,
                    selectableSearch = that.$el.find('input[name=num]');

                if (object === "Products") {
                    if ( (App.productsList == null) || (App.productsList == undefined) ){
                        App.feedback.show(new App.core.FeedbackNoTimeoutView({
                            'alertType': 'info',
                            'status': "Fetching all product info..."
                        }));
                        App.productsList = new App.core.ProductCollection();
                        App.productsList.fetch().done(function () {
                            App.productsList.sort();
                            App.feedback.empty();

                            _.each(App.productsList.models, function (val) {
                                var modelID = val.get('id'),
                                    modelName = val.get('name');
                                that.$el.find(divName).multiSelect('addOption', { 
                                    value: modelID, 
                                    text: modelID + ' - ' + modelName,
                                });
                            });
                        });
                    } else {
                        _.each(App.productsList.models, function (val) {
                            var modelID = val.get('id'),
                                modelName = val.get('name');
                            that.$el.find(divName).multiSelect('addOption', { 
                                value: modelID, 
                                text: modelID + ' - ' + modelName,
                            });
                        });
                    }
                } else {
                    if ( (App.contentsList == null) || (App.contentsList == undefined) ){
                        App.feedback.show(new App.core.FeedbackNoTimeoutView({
                            'alertType': 'info',
                            'status': "Fetching all product info..."
                        }));
                        App.contentsList = new App.core.ContentCollection();
                        App.contentsList.fetch().done(function () {
                            App.contentsList.sort();
                            App.feedback.empty();

                            _.each(App.contentsList.models, function (val) {
                                var modelID = val.get('id');
                                that.$el.find(divName).multiSelect('addOption', { 
                                    value: modelID, 
                                    text: "Content " + modelID,
                                });
                            });
                        });
                    } else {
                        _.each(App.contentsList.models, function (val) {
                            var modelID = val.get('id'),
                                modelName = val.get('name');
                            that.$el.find(divName).multiSelect('addOption', { 
                                value: modelID, 
                                text: "Content " + modelID,
                            });
                        });
                    }
                }

                selectableSearch.keyup(function(){
                    clearTimeout(typingTimer);
                    if (selectableSearch.val()) {
                        typingTimer = setTimeout(function () {
                            App.feedback.show(new App.core.FeedbackNoTimeoutView({
                                'alertType': 'info',
                                'status': "Fetching product info..."
                            }));
                            // Refresh products list by doing API call and refresh multiselect
                            selection = that.$el.find('select[name=selection]').val();
                            num = selectableSearch.val();

                            data = {};
                            data[selection] = num;

                            if (objectType === "Product") {
                                objectsList = new App.core.ProductCollection();
                            } else {
                                objectsList = new App.core.ContentCollection();
                            }
                            result = objectsList.fetch({
                                data: data,
                            });
                            result.always(function () {
                                App.feedback.empty();
                                if (result.status === 200) {
                                    if (objectType === "Product") {
                                        App.productsList = objectsList;
                                    } else {
                                        App.contentsList = objectsList;
                                    }
                                    that.$el.find(divName).empty();
                                    that.$el.find(divName).multiSelect('refresh');
                                } else {
                                    App.feedback.show(new App.core.FeedbackNoTimeoutView({
                                        'alertType': 'warning',
                                        'status': JSON.parse(result.responseText).status,
                                    }));
                                }
                            });
                        }, 1000);
                    }
                });
            },
        });
    },
});

App.core.UploadObjectModalView = App.core.BaseModalView.extend({
    template: _.template($('#upload-object-template').html()),

    onRender: function () {
        var that = this;

        this.unwrapEl();

        this.$el.modal('show'); // Toggle Bootstrap modal to show

        $('input[type=file]').change(function(){
            $(this).simpleUpload(window.location.href + '/upload', {
                allowedExts: ["jpg", "jpeg", "jpe", "jif", "jfif", "jfi", "png", "gif"],
                
                allowedTypes: ["image/pjpeg", "image/jpeg", "image/png", "image/x-png", "image/gif", "image/x-gif"],

                expect: "text",

                start: function(file){
                    this.block = $('<div class="block"></div>');
                    that.$el.find('#uploads').append(this.block);

                    this.fileName = file.name;
                },

                success: function(data){
                    var status = "File: " + this.fileName + ". " + data,
                        formatDiv = $('<div class="format"></div>').text(status);
                    this.block.append(formatDiv);
                },

                error: function(error){
                    var error = "File: " + this.fileName + ". " + error.message,
                        errorDiv = $('<div class="error"></div>').text(error);
                    this.block.append(errorDiv);
                }
            });
        });
    },

    events: {
        "click button#close": "closeModal",
    },
});

App.core.RemoveObjectModalView = App.core.BaseModalView.extend({
    template: _.template($('#remove-object-template').html()),

    onRender: function () {
        // Once the remove modal has been rendered, generate the form and add to the body of the modal.
        this.unwrapEl();

        var removeObjectModel,
            objectType = this.options.objectType,
            that = this,
            selectionOptions = {
                'Product': ['URL', 'ID', 'SKU'],
                'Content': ['URL', 'ID']
            };

        if ( (objectType == null) || (objectType == undefined) ){
            objectType = 'Product';
        }

        removeObjectModel = Backbone.Model.extend({
            schema: {
                selection: { title: '', type: 'Select', options: selectionOptions[objectType] },
                num:       { title: '', type: 'Text' },
            },
            defaults: {
                selection: 'ID',
            },
        });

        this.removeObjectInstance = new removeObjectModel();
        
        this.removeObjectForm = new Backbone.Form({
            template: _.template($('#remove-form-template').html()),

            model: this.removeObjectInstance,
        }).render();

        this.$el.find('.remove-form').html(this.removeObjectForm.el);
        this.$el.find('.modal-title').html("Remove " + objectType);
        this.$el.modal('show'); // Toggle Bootstrap modal to show
    },

    events: {
        "click button#remove": "removeObject",
        "click button#close": "closeModal",
    },

    removeObject: function () {
        // Remove the object from the page.
        var result, idLength, responseText, alertType, status,
            selection, num, page, searchString,
            that        = this,
            objectType  = this.options.objectType;

        if (objectType === "Product") {
            this.removeObjectForm.commit();
            selection   = this.removeObjectInstance.get('selection');
            num         = this.removeObjectInstance.get('num');
            page        = new App.core.Page({
                type: "product",
                selection: selection,
                num: num,
            })
            searchString = new App.core.Product();
        } else {
            this.removeObjectForm.commit();
            selection   = this.removeObjectInstance.get('selection'),
            num         = this.removeObjectInstance.get('num'),
            page        = new App.core.Page({
                type: "content",
                selection: selection,
                num: num,
            }),
            searchString = new App.core.Content();
        }

        if (selection === 'URL') {
            if (num.search('http') === -1) {
                num = 'http://' + num;
            }
            searchString.set({url: num});
        }
        if (selection === 'ID')
            searchString.set({id: num});
        if (selection === 'SKU')
            searchString.set({sku: num});

        result = searchString.search(searchString);
        result.always(function () {
            responseText = JSON.parse(result.responseText);
            idLength = responseText.ids.length;

            if (idLength === 1) {
                if (objectType === "Product") {
                    page = new App.core.Page({
                        type: "product",
                        id: responseText.ids[0],
                    });
                } else {
                    page = new App.core.Page({
                        type: "content",
                        id: responseText.ids[0],
                    });
                }

                result = page.remove(page);
                result.always(function () {
                    responseText = JSON.parse(result.responseText);
                    if (result.status === 200) {
                        alertType = 'success';
                    }
                    else {
                        alertType = 'warning';
                    }
                    that.$el.modal('hide'); // Toggle Bootstrap modal to hide
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': alertType,
                        'status': responseText.status
                    }));
                });
            } else {
                if (idLength > 1) {
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': 'danger',
                        'status': "Error: " + responseText.status
                    }));
                } else {
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': 'warning',
                        'status': responseText.status
                    }));
                }
            }
        });
    },
});

App.core.CategoryView = Marionette.ItemView.extend({
    template: _.template($('#category-template').html()),

    tagName: 'li',
});

App.core.CategoriesView = Marionette.CollectionView.extend({
    el: "#categories",

    childView: App.core.CategoryView,
});

App.core.ControlBarView = Marionette.ItemView.extend({
    template: _.template($('#control-bar-template').html()),

    events: {
        "click a": "filterClicked",
        "click button#add-product": "addProduct",
        "click button#remove-product": "removeProduct",
        "click button#add-content": "addContent",
        "click button#remove-content": "removeContent",
        "click button#upload-content": "uploadContent",
        "click button#tag-product": "tagProduct",
    },

    className: 'control-bar-wrapper',

    filterClicked: function (e) {
        /**
        Filter the page by the category chosen.

        inputs:
            e: the event triggered when an option is clicked. Contains
                   the target clicked.
        **/
        var filterID = e.currentTarget.id,
            tileCollectionView = new App.core.TileCollectionView({ 
                collection: App.tiles.currentView.collection,
            });
        if (filterID !== "View all tiles") {
            tileCollectionView.filter = function (child, index, collection) {
                return Boolean(_.findWhere(child.get('categories'), {'name': filterID}));
            };
        }
        this.$el.find('#category-dropdown-button').html(filterID + ' <span class="caret"></span>');
        App.tiles.show(tileCollectionView);
    },

    addProduct: function () {
        // Generate and render the add product modal
        App.modal.show(new App.core.AddObjectModalView({'objectType': "Product"}));
    },

    removeProduct: function () {
        // Generate and render the remove product modal
        App.modal.show(new App.core.RemoveObjectModalView({'objectType': "Product"}));
    },

    addContent: function () {
        // Generate and render the add content modal
        App.modal.show(new App.core.AddObjectModalView({'objectType': "Content"}));
    },

    removeContent: function () {
        // Generate and render the remove content modal
        App.modal.show(new App.core.RemoveObjectModalView({'objectType': "Content"}));
    },

    uploadContent: function () {
        // Generate and render the upload content modal
        App.modal.show(new App.core.UploadObjectModalView({'objectType': "Content"}));
    },
});

var core   = App.core,
    App = new App();
App.core = core;
App.start();
