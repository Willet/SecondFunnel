'use strict';

/**
 * @module intentRank
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {
    var resultsAlreadyRequested = [], // list of product IDs
        defaultOptions = {
            'IRSource': '/intentrank',
            'urlTemplate': '<%=IRSource%>/page/<%=campaign%>/getresults?category=<%=category%>',
            'add': true,
            'merge': true,
            'remove': false,
            'categories': {},
            'IRResultsCount': 10,
            'IRAlgo': 'magic',
            'IRTileSet': '',
            'IRReqNum': 0,
            'store': {},
            'content': []
        };

    /**
     * Initializes intentRank.
     *
     * @param opts {Object}:
     *     {String} category - record current category as this
     *     {Boolean} trigger - trigger category change
     *
     * @returns this
     */
    module.initialize = function (opts) {
        var page = App.option('page') || {},
            options = App.options;

        opts = _.isObject(opts) ? opts : {};


        module.options = _.extend(defaultOptions, {
            'IRSource': options.IRSource || module.IRSource,
            'store': options.store || {},
            'campaign': options.campaign,
            'categories': page.categories || {},
            'IRResultsCount': options.IRResultsCount || 10,
            'IRAlgo': options.IRAlgo || 'magic',
            'IRReqNum': options.IRReqNum || 0,
            'IRTileSet': options.IRTileSet || '',
            'content': options.content || [],
            'filters': options.filters || [],
            // Use this to intelligently guess what our cache calls should request
            'IRCacheResultCount': options.IRResultsCount || 10
        });

        if (opts.trigger) {
            module.changeCategory(opts.category);
        } else {
            module._category = opts.category || '';
        }

        App.vent.trigger('intentRankInitialized', module);
        return module;
    };

    /**
     *  Return the current category
     *
     *  @returns {String}
     */
    module.currentCategory = function () {
        return module._category;
    };

    /**
     * This function simply returns the base url for intentRank
     *
     * @returns {String}
     */
    module.url = function () {
        compiledTemplate = _.template(module.options.urlTemplate);
        data = _.extend({}, module.options,
                        { 'category': encodeURIComponent(module._category || module.options.category) });
        return compiledTemplate(data);
    };

    /**
     * This function is a bridge between our IntentRank module and our
     * Discovery area.  This function can be called by intentRank itself,
     * or a Collection as context.  Benefits of calling this with intentRank
     * as context, is that you can cache results.
     *
     * @param options
     * @returns {promise}
     */
    module.fetch = function (options) {
        // 'this' can be whatever you want it to be
        var collection = this,
            data = {},
            opts;

        if (module.options.IRReset) {
            data['session-reset'] = true;
            module.options.IRReset = false;
            resultsAlreadyRequested = [];
        }

        if (resultsAlreadyRequested.length) {
            data.shown = resultsAlreadyRequested.sort().join(',');
        }

        data.algorithm = module.options.IRAlgo;
        data.offset = collection.offset || 0;
        data['tile-set'] = module._IRTileSet || module.options.IRTileSet;
        if (App.option('debug')) {
            data.time = Date.now();
        }

        opts = $.extend({}, {
            'results': 10,
            'add': true,
            'merge': true,
            'remove': false,
            'crossDomain': true,
            'xhrFields': {
                'withCredentials': true
            },
            'parse': true,
            'data': data
        }, this.config, module.options, options);

        if (collection.ajaxFailCount > 5) {
            console.error("IR failed " + collection.ajaxFailCount +
                " times consecutively!");
            return this.deferred;
        }

        // Only do a request if it is the current view
        if (collection !== App.discovery.collection) {
            return (new $.Deferred()).promise();
        }

        // Make the request to Backbone collection and return deferred
        this.deferred = Backbone.Collection.prototype
            .sync('read', collection, opts)
            .done(function (results) {
                // request SUCCEEDED
                var method = opts.reset ? 'reset' : 'set',
                    allArraysAlike = function (arrays) {
                        return _.all(arrays, function (array) {
                            return array.length === arrays[0].length &&
                                _.difference(array, arrays[0]).length === 0;
                        });
                    };

                App.options.IRResultsReturned = results.length;

                // reset fail counter
                collection.ajaxFailCount = 0;
                collection.offset += opts.results;
                // update collection
                collection[method](results, opts);
                // manually fire event for any listeners
                collection.trigger('sync', collection, results, opts);

                resultsAlreadyRequested = _.compact(module.getTileIds(results));

                // restrict shown list to last 10 items max
                // (it was specified before?)
                resultsAlreadyRequested = resultsAlreadyRequested.slice(
                    -module.options.IRResultsCount);
            }).fail(function (e) {
                // request FAILED
                if (collection.ajaxFailCount) {
                    collection.ajaxFailCount++;
                } else {
                    collection.ajaxFailCount = 1;
                }
                // For category does not exist errors, attempt recovery
                if (e.status === 404 && _.contains(e.responseText, 'Category') && _.contains(e.responseText, 'does not exist')) {
                    if (App.option('debug', false)) {
                        console.error(e.responseText);
                    }
                    if (module._category === App.option("page:home:category")) {
                        // Home category is failing, go directly to unfiltered feed
                        module._changeCategory('', true);
                    } else {
                        // Navigate home
                        App.router.navigate("", { trigger: true });
                    }
                }
                // Stop propogation
                return false;
            });

        collection.isLoading = true;

        this.deferred.done(function () {
            App.options.IRReqNum++;
            module.options.IRReqNum++;
        });

        return this.deferred;
    };

    /**
     * Filter the content based on the selector
     * passed and the criteria/filters defined in the App options.
     *
     * @param {Array} content
     * @param selector {string}: (optional) no idea what this is.
     *                           I think it stands for additional filters.
     * @returns {Array} filtered content
     */
    module.filter = function (content, selector) {
        var i, filter,
            filters = module.options.filters || [];

        filters.push(selector);
        filters = _.flatten(filters);

        for (i = 0; i < filters.length; ++i) {
            filter = filters[i];
            if (content.length === 0) {
                break;
            }
            switch (typeof filter) {
            case 'function':
                content = _.filter(content, filter);
                break;
            case 'object':
                content = _.where(content, filter);
                break;
            }
        }
        return content;
    };

    /**
     * append a list of json results shown.
     */
    module.addResultsShown = function (results) {
        resultsAlreadyRequested = resultsAlreadyRequested.concat(
            module.getTileIds(results));
        return module;
    };

    /**
     * @param {Tile} tiles
     *               if not given, all tiles on the page
     * @return {Array} unique list of tile ids
     */
    module.getTileIds = function (tiles) {
        if (tiles === undefined) {
            if (App.discoveryArea && App.discoveryArea.$el) {
                tiles = _.map(App.discoveryArea.$el.find('.tile'), function (el) {
                    return $(el).tile().model;
                });
            }
        }
        if (!tiles) {
            tiles = [];
        }

        return _.uniq(_.map(_.compact(tiles), function (model) {
            try {  // Tile
                return model.get('tile-id');
            } catch (err) {  // object
                return model['tile-id'];
            }
        }));
    };

    /**
     * Dummy method
     *
     * @return this
     */
    module.set = function (results) {
        return module;
    };

    /**
     * Dummy method
     *
     * @return this
     */
    module.sync = function () {
        return module;
    };

    /**
     * Changes the intentRank category and updates the discovery area
     * and fire 'change:category' event
     *
     * @param {String} category
     * @param {Boolean} silent (optional) - supresses 'change:category' event
     *
     * @return this
     */
    module.changeCategory = function (category, silent) {
        silent = silent || false;

        // If category doesn't exist or '' - load home 
        if (!_.isString(category) || _.isEmpty(category)) {
            if (!_.isString(category) && App.option('debug', false)) {
                console.error("Invalid category '"+category+"', attempting to load home category");
            }
            // try the home category
            if (App.option("page:home:category")) {
                category = App.option("page:home:category");
            } else {
                // home category is no beuno, lets go with empty string
                if (App.option('debug', false)) {
                    console.warn("No home category, loading feed without category");
                }
                // load feed without a category
                category = '';
            }
        }
         
        // Check the category differs from the current category
        if (module._category === category) {
            if (App.option('debug', false)) {
                console.warn("Could not change category to '"+category+"': category already selected");
            }
        } else {
            module._changeCategory(category, silent);
        }
        
        return module;
    };

    /**
     * Executes change category command on category with no protections
     *
     * @param {String} category
     * @param {Boolean} silent (optional) - supresses 'change:category' event
     *
     * Note: currently IntentRank does not know what valid categories are.  The server should
     *       return 404 Bad Request for invalid category(s) and the page will try to load the
     *       home category then no category.
     *
     * @return this
     */
    module._changeCategory = function (category, silent) {
        var catObj;

        // Change to valid category
        $(".loading").show();

        catObj = App.categories ? App.categories.findModelByName(category) || {} : {};

        module._category = category;
        // tileSet is an optional paramter which can force a category to be
        // content-only "content" or product-only "products"
        // generally this should be undefined
        module._IRTileSet = catObj['tileSet'] || undefined;
        module.options.IRReset = true;
        
        App.vent.trigger('tracking:changeCategory', category);
        if (!silent) {
            App.vent.trigger('change:category', category, category);
        }

        // We create a new feed each time to ensure the previous
        // feed & tiles are completely unbinded
        // This is a hack because of memory leaks and should be undone
        // and the leaks fixed
        App.discovery = new App.core.MasonryFeedView(App.options);
        App.discoveryArea.show(App.discovery);
    };
};
