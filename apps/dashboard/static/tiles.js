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
        var tiles = new App.core.TileCollection();    //Collection of all tiles

        tiles.fetch().done(function () {
            $('#loading-spinner').hide();

            App.controlBar.show(new App.core.ControlBarView());

            App.categories = new App.core.Categories();
            _.each(tiles.models, function (val) {
                _.each(val.attributes.categories, function (cat) {
                    var exist = false;
                    for (var i = 0; i < App.categories.length; i++) {
                        if (App.categories.models[i].id === cat.id) {
                            exist = true;
                            break;
                        }
                    }
                    if (!exist) {
                        var category = new App.core.Category();
                        category.set(cat);
                        App.categories.add(category);
                    }
                })
            });
            App.categoriesView = new App.core.CategoriesView({ collection: App.categories });
            App.categoriesView.render();
        });
        var test = new App.core.TileCollectionView({ collection: tiles });
        this.tiles.show(test); //View of all tiles
    },
});

App.core = {};

//App.core.apiURL = "http://production.secondfunnel.com/api2/";
App.core.apiURL = "http://localhost:8000/api2/";

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
        var diff, prioDiff, options, moveTileCollection, result, alertType,
            batch = [],
            tileCollection = this,
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

App.core.TileView = Marionette.ItemView.extend({
    template: _.template($('#tile-template').html()),

    tagName: 'li',

    className: 'tile sortable',

    events: {
        "click button.remove": "removeModal",
        "click .content": "editModal",
    },

    removeModal: function () {
        App.modal.show(new App.core.RemoveModalView({ model: this.model }));
    },

    editModal: function () {
        App.modal.show(new App.core.EditModalView({ model: this.model }));
    },
});

App.core.TileCollectionView = Marionette.CollectionView.extend({
    el: "#backbone-tiles",

    childView: App.core.TileView,

    initialize: function () {
        this.listenTo(this.collection, 'change destroy', _.debounce(function () {this.collection.sort();}, 100));
        this.listenTo(this.collection, 'sort', _.debounce(this.render, 100));
    },

    onShow: function () {
        $('#backbone-tiles').sortable({
            start: function (event, ui) {
                var startPos = ui.item.index() - 1;
                App.feedback.empty();
                ui.item.data('startPos', startPos);
            },

            update: function (event, ui) {
                var alertType, status,
                    startPos = ui.item.data('startPos'),
                    endPos = ui.item.index() - 1,
                    movedTileID = App.tiles.currentView.collection.models[startPos].get('id');

                alertType = 'info';
                status = 'Processing... Please wait.';
                App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));

                App.tiles.currentView.collection.moveTileToPosition(movedTileID, endPos);
            },
        });
    },
});

App.core.FeedbackView = Marionette.ItemView.extend({
    template: _.template($('#feedback-template').html()),

    initialize: function (options) {
        /* Wait 10s before removing the alert */
        setTimeout(function () { App.feedback.empty(); }, 10000);
    },

    templateHelpers: function () {
        return this.options;
    },
});

App.core.EditModalView = Marionette.ItemView.extend({
    template: _.template($('#edit-modal-template').html()),

    events: {
        "click button#close": "closeModal",
        "click button#change": "changePriority",
    },

    closeModal: function () {
        this.$el.modal('toggle');
    },

    changePriority: function () {
        var result, status, alertType,
            currModel = this.model,
            newPriority = document.getElementById('new_priority').value;

        try {
            if (newPriority === '' || newPriority === null) {
                throw "Error. New priority input is empty."
            }
            if (!(Math.floor(newPriority) === newPriority && $.isNumeric(newPriority))) {
                throw "Error. A valid integer is required."
            }
            this.$el.modal('toggle');

            alertType = 'info';
            status = 'Processing... Please wait.';

            App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));

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
                App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));
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

    events: {
        "click button#closeButton": "closeModal",
        "click button#removeTile": "deleteTile",
    },

    closeModal: function () {
        this.$el.modal('toggle');
    },

    deleteTile: function () {
        /**
        Remove the tile from the page
        **/
        var result, status, alertType,
            currModel = this.model,
            modelID = currModel.id;
        this.$el.modal('toggle');

        alertType = 'info';
        status = 'Processing... Please wait.';

        App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));

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
                status = JSON.parse(result.responseText);
            }
            App.feedback.show(new App.core.FeedbackView({'alertType': alertType, 'status': status}));
        })
    },

    onRender: function () {
        this.unwrapEl();
        this.$el.modal('toggle');
    },
});

App.core.Category = Backbone.Model;

App.core.Categories = Backbone.Collection.extend({
    defaults: {},

    model: App.core.Category,
});

App.core.Product = Backbone.Model.extend({
    defaults: {},

    urlRoot: App.core.apiURL,

    getCustomURL: function (method) {
        switch (method) {
            case 'read':
                return App.core.apiURL + 'page/' + pageID + '/';
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
        var options = {
            'url': this.getCustomURL('search'),
        };
        return Backbone.sync.call(this, 'create', searchString, options);
    },

    scrape: function (URL) {
        var options = {
            'url': this.getCustomURL('scrape'),
        };
        return Backbone.sync.call(this, 'create', URL, options);
    }
});

App.core.Content = Backbone.Model.extend({
    defaults: {},

    urlRoot: App.core.apiURL,

    initialize: function () {

    },

    getCustomURL: function (method) {
        switch (method) {
            case 'read':
                return App.core.apiURL + 'page/' + pageID + '/';
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
        var options = {
            'url': this.getCustomURL('search')
        };
        return Backbone.sync.call(this, 'create', searchString, options);
    },

    scrape: function (URL) {
        var options = {
            'url': this.getCustomURL('scrape')
        };
        return Backbone.sync.call(this, 'create', URL, options);
    }
});

App.core.Page = Backbone.Model.extend({
    defaults: {
        selection: '' ,
        num: ''
    },

    urlRoot: App.core.apiURL,

    initialize: function () {

    },

    getCustomURL: function (method) {
        switch (method) {
            case 'read':
                return App.core.apiURL + 'page/' + pageID + '/';
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
        var options = {
            'url': this.getCustomURL('add')
        };
        return Backbone.sync.call(this, 'create', product , options);
    },

    remove: function (product) {
        var options = {
            'url': this.getCustomURL('remove')
        };
        return Backbone.sync.call(this, 'create', product , options);
    }
});

App.core.AddObjectModalView = Marionette.ItemView.extend({
    template: _.template($('#add-object-template').html()),

    events: {
        "click button#add": "addObject",
        "click button#close": "closeModal",
    },

    closeModal: function () {
        this.$el.modal('toggle');
    },

    addObject: function () {
        var result, idLength, responseText, alertType, status, selection,
            num, page, searchString, priority, category,
            thisBackUp  = this,
            objectType = this.options.objectType;

        if (objectType === "Product") {
            App.addProductForm.commit();
            selection   = App.addProduct.attributes.selection;
            num         = App.addProduct.attributes.num;
            priority    = App.addProduct.attributes.priority;
            category    = App.addProduct.attributes.category;
            page        = new App.core.Page({
                type: "product",
                selection: selection,
                num: num,
                priority: priority,
                category: category
            });
            searchString = new App.core.Product();
        } else {
            App.addContentForm.commit();
            selection   = App.addContent.attributes.selection;
            num         = App.addContent.attributes.num;
            category    = App.addContent.attributes.category;
            page        = new App.core.Page({
                type: "content",
                selection: selection,
                num: num,
                category: category
            }),
            searchString = new App.core.Content();
        }

        if (selection === 'URL')
            searchString.set({url: num});
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
                        force_create: $('#force-create').is(':checked').toString(),
                    });
                } else {
                    page = new App.core.Page({
                        type: "content",
                        id: responseText.ids[0],
                        force_create: $('#force-create').is(':checked').toString(),
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
                    responseText = JSON.parse(result.responseText);
                    if (result.status === 200) {
                        alertType = 'success';
                    }
                    else {
                        alertType = 'warning';
                    }
                    thisBackUp.$el.modal('toggle');
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': alertType,
                        'status': responseText.status
                    }));
                })
            } else {
                if (idLength > 1) {
                    alertType = 'danger';
                    status = "Error: " + responseText.status;
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': alertType,
                        'status': status
                    }));
                } else {
                    if ((selection === 'URL') && (responseText.status.indexOf("could not be found") >= 0)) {
                        alertType = 'info';
                        status = responseText.status + " Scraping...";
                        App.feedback.show(new App.core.FeedbackView({
                            'alertType': alertType,
                            'status': status
                        }));
                        if (objectType === "Product") {
                            var scrapeURL = new App.core.Product({
                                url: num,
                                page_id: pageID
                            });
                            result = scrapeURL.scrape(scrapeURL);
                        } else {
                            var uploadURL = new App.core.Content({
                                url: num,
                                page_id: pageID
                            });
                            result = uploadURL.scrape(uploadURL);
                        }
                        result.always(function () {
                            responseText = JSON.parse(result.responseText);
                            alertType = 'success';
                            status = responseText.status;
                            App.feedback.show(new App.core.FeedbackView({
                                'alertType': alertType,
                                'status': status
                            }));
                        })
                    } else {
                        alertType = 'warning';
                        App.feedback.show(new App.core.FeedbackView({
                            'alertType': alertType,
                            'status': responseText.status
                        }));
                    }
                }
            }
        });
    },

    templateHelpers: function () {
        return this.options;
    },

    onRender: function () {
        this.unwrapEl();
        this.$el.modal('toggle');
    },
});

App.core.RemoveObjectModalView = Marionette.ItemView.extend({
    template: _.template($('#remove-object-template').html()),

    events: {
        "click button#remove": "removeObject",
        "click button#close": "closeModal",
    },

    closeModal: function () {
        this.$el.modal('toggle');
    },

    removeObject: function () {
        var result, idLength, responseText, alertType, status,
            selection, num, page, searchString,
            thisBackUp  = this,
            objectType = this.options.objectType;

        if (objectType === "Product") {
            App.removeProductForm.commit();
            selection = App.removeProduct.attributes.selection;
            num = App.removeProduct.attributes.num;
            page = new App.core.Page({
                type: "product",
                selection: selection,
                num: num,
            })
            searchString = new App.core.Product();
        } else {
            App.removeContentForm.commit();
            selection = App.removeContent.attributes.selection,
            num = App.removeContent.attributes.num,
            page = new App.core.Page({
                type: "content",
                selection: selection,
                num: num,
            }),
            searchString = new App.core.Content();
        }

        if (selection === 'URL')
            searchString.set({url: num});
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
                    thisBackUp.$el.modal('toggle');
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': alertType,
                        'status': responseText.status
                    }));
                });
            } else {
                if (idLength > 1) {
                    alertType = 'danger';
                    status = "Error: " + responseText.status;
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': alertType,
                        'status': status
                    }));
                } else {
                    alertType = 'warning';
                    status = responseText.status;
                    App.feedback.show(new App.core.FeedbackView({
                        'alertType': alertType,
                        'status': status
                    }));
                }
            }
        });
    },

    templateHelpers: function () {
        return this.options;
    },

    onRender: function () {
        this.unwrapEl();
        this.$el.modal('toggle');
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

    initialize: function () {
    },

    events: {
        "click a": "filterClicked",
        "click button#add-product": "addProduct",
        "click button#remove-product": "removeProduct",
        "click button#add-content": "addContent",
        "click button#remove-content": "removeContent",
    },

    filterClicked: function (e) {
        var filterID = e.currentTarget.id;
        
        console.log(filterID);
        var a = new App.core.TileCollectionView({ 
            collection: App.tiles.currentView.collection,

            filter: function (child, index, collection) {
                _.each(child.get('categories'), function (val) {
                    if (val['name'] === filterID) {
                        return true;
                    }
                });
                return false;
            }
        });
        App.tiles.show(a);
    },

    addProduct: function () {
        App.modal.show(new App.core.AddObjectModalView({'objectType': "Product"}));

        App.core.addProductModel = Backbone.Model.extend({
            schema: {
                selection: { title: 'Selection', type: 'Select', options: ['URL', 'SKU', 'ID'] },
                num:       { title: 'Number', type: 'Text' },
                priority:  { title: 'Priority', type: 'Text' },
                category:  { title: 'Category', type: 'Text' },
            },
            defaults: {
                selection: 'ID',
            },
        });
        App.addProduct = new App.core.addProductModel();

        App.addProductForm = new Backbone.Form({
            model: App.addProduct,
        }).render();

        $('.add-form').html(App.addProductForm.el);
    },

    removeProduct: function () {
        App.modal.show(new App.core.RemoveObjectModalView({'objectType': "Product"}));

        App.core.removeProductModel = Backbone.Model.extend({
            schema: {
                selection: { title: 'Selection', type: 'Select', options: ['URL', 'SKU', 'ID'] },
                num:       { title: 'Number', type: 'Text' },
            },
            defaults: {
                selection: 'ID',
            },
        });
        App.removeProduct = new App.core.removeProductModel();

        App.removeProductForm = new Backbone.Form({
            model: App.removeProduct,
        }).render();

        $('.remove-form').html(App.removeProductForm.el);
    },

    addContent: function () {
        App.modal.show(new App.core.AddObjectModalView({'objectType': "Content"}));

        App.core.addContentModel = Backbone.Model.extend({
            schema: {
                selection: { title: 'Selection', type: 'Select', options: ['URL', 'ID'] },
                num:       { title: 'Number', type: 'Text' },
                category:  { title: 'Category', type: 'Text' },
            },
            defaults: {
                selection: 'ID',
            },
        });
        App.addContent = new App.core.addContentModel();

        App.addContentForm = new Backbone.Form({
            model: App.addContent,
        }).render();

        $('.add-form').html(App.addContentForm.el);
    },

    removeContent: function () {
        App.modal.show(new App.core.RemoveObjectModalView({'objectType': "Content"}));

        App.core.removeContentModel = Backbone.Model.extend({
            schema: {
                selection: { title: 'Selection', type: 'Select', options: ['URL', 'ID'] },
                num:       { title: 'Number', type: 'Text' },
            },
            defaults: {
                selection: 'ID',
            },
        });
        App.removeContent = new App.core.removeContentModel();

        App.removeContentForm = new Backbone.Form({
            model: App.removeContent,
        }).render();

        $('.remove-form').html(App.removeContentForm.el);
    },
});

var core   = App.core,
    App = new App();
App.core = core;
App.start();
