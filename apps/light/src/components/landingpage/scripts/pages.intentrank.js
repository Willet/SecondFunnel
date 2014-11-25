'use strict';

/**
 * @module intentRank
 */
module.exports = function (intentRank, App, Backbone, Marionette, $, _) {
    var resultsAlreadyRequested = []; // list of product IDs

    this.options = {
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

    this.on('start', function () {
        return this.initialize(App.options);
    });

    /**
     * Initializes intentRank.
     *
     * @param options {Object}    overrides.
     * @returns this
     */
    this.initialize = function (options) {
        // Any additional init declarations go here
        var page = options.page || {};

        _.extend(intentRank.options, {
            'IRSource': options.IRSource || this.IRSource,
            'store': options.store || {},
            'campaign': options.campaign,
            // @deprecated: options.categories will be page.categories
            'categories': page.categories || options.categories || {},
            'IRResultsCount': options.IRResultsCount || 10,
            'IRAlgo': options.IRAlgo || 'magic',
            'IRReqNum': options.IRReqNum || 0,
            'IRTileSet': options.IRTileSet || '',
            'content': options.content || [],
            'filters': options.filters || [],
            // Use this to intelligently guess what our cache calls should
            // request
            'IRCacheResultCount': options.IRResultsCount || 10
        });

        App.vent.trigger('intentRankInitialized', intentRank);
        return this;
    };

    /**
     * This function simply returns the base url for intentRank
     *
     * @returns {String}
     */
    this.url = function () {
        return _.template(this.options.urlTemplate, intentRank.options);
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
    this.fetch = function (options) {
        // 'this' can be whatever you want it to be
        var collection = this,
            data = {},
            opts;

        if (resultsAlreadyRequested.length) {
            data.shown = resultsAlreadyRequested.sort().join(',');
        }
        data.algorithm = intentRank.options.IRAlgo;
        data.reqNum = intentRank.options.IRReqNum;
        data.offset = collection.offset || 0;
        data['tile-set'] = intentRank.options.IRTileSet;

        if (intentRank.options.IRReset) {
            data['session-reset'] = true;
            intentRank.options.IRReset = false;
        }

        // normally undefined, unless a category is selected on the page
        if (intentRank.options.category) {
            data.category = intentRank.options.category;
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
        }, this.config, intentRank.options, options);

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

                resultsAlreadyRequested = _.compact(intentRank.getTileIds(results));

                // restrict shown list to last 10 items max
                // (it was specified before?)
                resultsAlreadyRequested = resultsAlreadyRequested.slice(
                    -intentRank.options.IRResultsCount);
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
            intentRank.options.IRReqNum++;
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
    this.filter = function (content, selector) {
        var i, filter,
            filters = intentRank.options.filters || [];

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
    this.addResultsShown = function (results) {
        resultsAlreadyRequested = resultsAlreadyRequested.concat(
            intentRank.getTileIds(results));
    };

    /**
     * @param {Tile} tiles
     *               if not given, all tiles on the page
     * @return {Array} unique list of tile ids
     */
    this.getTileIds = function (tiles) {
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
        return this;
    };

    /**
     * Dummy method
     *
     * @return this
     */
    this.sync = function () {
        return this;
    };

    /**
     * Changes the intentRank category, consequently changing the url
     * that is used as well.
     *
     * @param {String} category
     * @return this
     */
    this.changeCategory = function (category) {
        if ($('.category-area span').length < 1) {
            return intentRank;
        }
        if (category === '') {
            category = $('.category-area span:first').attr('data-name');
        }

        if (intentRank.options.category === category) {
            return intentRank;
        }

        // Change the category, category is a string passed to data
        intentRank.options.category = category;
        intentRank.options.IRReset = true;
        App.tracker.changeCategory(category);

        App.vent.trigger('change:category', category, category);

        App.discovery = new App.feed.MasonryFeedView({
            options: App.options
        });
        $(".loading").show();
        App.discoveryArea.show(App.discovery);

        var categoryHierarchy = category.split("|");
        var categorySpan = $('.category-area span[data-name="' + categoryHierarchy[0] + '"]:not(.sub-category)');
        if (categoryHierarchy.length > 1) {
            // sub-categories
            categorySpan = $('.sub-category[data-name="' + categoryHierarchy[1] + '"]', categorySpan.parent());
        }
        categorySpan.trigger("click");
        
        return intentRank;
    };
};
