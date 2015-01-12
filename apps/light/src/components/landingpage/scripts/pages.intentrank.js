'use strict';

/**
 * @module intentRank
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {
    var resultsAlreadyRequested = []; // list of product IDs

    module.options = {
        'IRSource': '/intentrank',
        'urlTemplate': '<%=IRSource%>/page/<%=campaign%>/getresults',
        'add': true,
        'merge': true,
        'remove': false,
        'categories': {},
        'IRResultsCount': 10,
        'IRAlgo': 'generic',
        'IRTileSet': '',
        'IRReqNum': 0,
        'store': {},
        'content': []
    };

    /**
     * Initializes intentRank.
     *
     * @param options {Object}    overrides.
     * @returns this
     */
    module.initialize = function (options) {
        // Any additional init declarations go here
        var page = options.page || {};

        _.extend(module.options, {
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

        module._category = category || App.option('categoryHome') || undefined;
        module.changeCategory(module._category);

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
        return _.template(module.options.urlTemplate, module.options);
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

        if (resultsAlreadyRequested.length) {
            data.shown = resultsAlreadyRequested.sort().join(',');
        }
        data.algorithm = module.options.IRAlgo;
        data.reqNum = module.options.IRReqNum;
        data.offset = collection.offset || 0;
        data['tile-set'] = module.options.IRTileSet;

        if (module.options.IRReset) {
            data['session-reset'] = true;
            module.options.IRReset = false;
        }

        // normally undefined, unless a category is selected on the page
        data.category = module._category || module.options.category || undefined;

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

                collection[method](results, opts);
                collection.trigger('sync', collection, results, opts);

                resultsAlreadyRequested = _.compact(module.getTileIds(results));

                // restrict shown list to last 10 items max
                // (it was specified before?)
                resultsAlreadyRequested = resultsAlreadyRequested.slice(
                    -module.options.IRResultsCount);
            }).fail(function () {
                // request FAILED
                if (collection.ajaxFailCount) {
                    collection.ajaxFailCount++;
                } else {
                    collection.ajaxFailCount = 1;
                }
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
     * @param {Array} results
     * @return this
     */
    this.set = function (results) {
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
     * Changes the intentRank category
     *
     * @param {String} category
     * @return this
     */
    module.changeCategory = function (category) {
        // If category doesn't exist
        if (!(category && App.categories.categoryExists(category))) {
            // '' is valid; it means load home
            if (!(category === '') && App.option('debug', false)) {
                console.error("Invalid category '"+category+"', attempting to load home category");
            }
            // try the categoryHome
            if (App.option("page:categoryHome")) {
                category = App.option("page:categoryHome");
            } else {
                // categoryHome is no beuno, lets go with empty string
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
                console.warn("Could not change category to '"+category+"'': category already selected");
            }
        } else {
            // Change to valid category
            $(".loading").show();

            module._category = category;
            module.options.IRReset = true;
            App.tracker.changeCategory(category);
            App.vent.trigger('change:category', category, category);

            // We create a new feed each time to ensure the previous
            // feed & tiles are completely unbinded
            App.discovery = new App.core.MasonryFeedView(App.options);
            App.discoveryArea.show(App.discovery);
        }
        
        return module;
    };
};
