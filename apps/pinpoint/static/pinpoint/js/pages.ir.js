/*global App, Backbone, Marionette, imagesLoaded, console, _, setTimeout, clearTimeout, $ */
/**
 * @module intentRank
 */
App.module("intentRank", function (intentRank, App) {
    "use strict";

    var consecutiveFailures = 0,
        cachedResults = [],
        fetching = null,
        resultsAlreadyRequested = [], // list of product IDs
        urlTemplate;

    this.options = {
        'baseUrl': "/intentrank",  // or an absolute base url, e.g. http://tng-test.secondfunnel.com/intentrank
        'urlTemplates': {
            'campaign': "<%=baseUrl%>/page/<%=campaign%>/getresults?results=<%=IRCacheResultCount%>",
            'category': "<%=baseUrl%>/page/<%=campaign%>/getresults?results=<%=IRCacheResultCount%>&category=<%=category%>"
        },
        'add': true,
        'merge': true,
        'remove': false,
        'categories': {},
        'backupResults': [],
        'IRResultsCount': 10,
        'IRAlgo': 'generic',
        'IRReqNum': 0,
        'IRTimeout': 5000,
        'IROffset': 0,  // specific to some deterministic algorithms
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
            'baseUrl': options.IRSource || this.baseUrl,
            'store': options.store || {},
            'campaign': options.campaign,
            // @deprecated: options.categories will be page.categories
            'categories': page.categories || options.categories || {},
            'backupResults': options.backupResults || [],
            'IRResultsCount': options.IRResultsCount || 10,
            'IRAlgo': options.IRAlgo || 'generic',
            'IRReqNum': options.IRReqNum || 0,
            'IRTimeout': options.IRTimeout || 5000,
            'content': options.content || [],
            'filters': options.filters || [],
            // Use this to intelligently guess what our cache calls should
            // request
            'IRCacheResultCount': options.IRResultsCount || 10,
            'IROffset': options.IROffset || 0
        });

        // set the base url
        urlTemplate = intentRank.options.urlTemplates.campaign;

        App.vent.trigger('intentRankInitialized', intentRank);
        return this;
    };

    /**
     * This function simply returns the base url for intentRank
     *
     * @returns {String}
     */
    this.url = function () {
        return _.template(urlTemplate, intentRank.options);
    };

    /**
     * This function is a smart alias to fetch, which essentially checks for
     * and stores a promise object that others can latch onto when they call for
     * results.
     *
     * @returns this
     */
    this.prefetch = _.debounce(function () {
        var diff = cachedResults.length - intentRank.options.IRCacheResultCount;
        // Only prefetch if cached count is low and we're not already
        // fetching.
        if (!fetching && diff < 0) {
            console.debug("Prefetching from IR.");
            fetching = intentRank.fetch({ // Fetch only the difference
                'IRCacheResultCount': Math.abs(diff)
            }).done(function () { // Clear fetching when done
                fetching = null;
            });
        }
        return this;
    }, 6000);

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
            deferred = new $.Deferred(),
            online = !App.option('page:offline', false),
            data = {},
            opts,
            prepopulatedResults = [],
            backupResults = _.chain(intentRank.options.backupResults)
                .filter(intentRank.filter)
                .shuffle()
                .first(intentRank.options.IRResultsCount)
                .value();

        if (resultsAlreadyRequested.length) {
            data.shown = resultsAlreadyRequested.join(',');
        }
        data.algorithm = intentRank.options.IRAlgo;
        data.reqNum = intentRank.options.IRReqNum;
        data.offset = intentRank.options.IROffset;

        if (intentRank.options.IRReset) {
            data['session-reset'] = true;
            intentRank.options.IRReset = false;
            cachedResults = [];
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
            parse: true,
            'data': data
        }, this.config, intentRank.options, options);

        // if offline, return a backup list
        if (!online || collection.ajaxFailCount > 5) {
            return $.when(backupResults);
        }

        // check if cached results, and options is undefined
        // don't do this if we are actually the intentRank module
        if (!options && this !== intentRank) {
            var len = cachedResults.length,
                method = opts.reset ? 'reset' : 'set';
            prepopulatedResults = cachedResults.splice(0, len);

            if (fetching) { // return fetching object if we're fetching
                console.debug("Holding off for IR to finish.");
                return fetching.done(function (results) {
                    collection[method](results, opts);
                    collection.trigger('sync', collection, results, opts);
                });
            }

            if (len >= opts.results) {
                // Use a dummy deferred object
                console.debug("Using existing results.");
                return $.when(prepopulatedResults).done(function(results) {
                    collection[method](results, opts);
                    collection.trigger('sync', collection, results, opts);
                    intentRank.prefetch();
                });
            }
            // for now, it seems that intentRank has an upperbound of 20, so
            // just set that as the limit
            intentRank.updateCache(opts.results - len);
        }

        // attach respective success and error functions to the options object
        // use backup list if request fails
        _.extend(opts, {
            success: function (results) {
                var method = opts.reset ? 'reset' : 'set';
                results = prepopulatedResults.concat(results);
                App.options.IRResultsReturned = results.length;

                // reset fail counter
                collection.ajaxFailCount = 0;
                collection[method](results, opts);
                collection.trigger('sync', collection, results, opts);
                deferred.resolve(results);
                resultsAlreadyRequested = _.compact(intentRank.getTileIds(results));

                // restrict shown list to last 10 items max
                // (it was specified before?)
                if (resultsAlreadyRequested.length > intentRank.options.IRResultsCount) {
                    resultsAlreadyRequested = resultsAlreadyRequested.slice(-10);
                }

                // Only prefetch if this isn't intentRank; prevents infinite
                // calls.
                if (collection !== intentRank) {
                    intentRank.prefetch();
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                // reset fail counter
                if (collection.ajaxFailCount) {
                    collection.ajaxFailCount++;
                } else {
                    collection.ajaxFailCount = 1;
                }

                deferred.resolve(backupResults);
                resultsAlreadyRequested = intentRank.getTileIds(backupResults);
            }
        });

        // Make the request to Backbone collection and return deferred
        Backbone.Collection.prototype.sync('read', collection, opts);
        deferred.done(function () {
            App.options.IRReqNum++;
            intentRank.options.IRReqNum++;
            intentRank.options.IROffset += opts.results;
        });
        return deferred.promise();
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
     * A unique list of all tiles shown on the page.
     * @returns {array}
     */
    this.getAllResultsShown = function () {
        try {
            return App.discovery.collection.models;
        } catch (err) {
            // first call, App.discovery is not a var yet
            return App.option('initialResults') || [];
        }
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
     * @return {Array} unique list of tile ids
     */
    this.getTileIds = function (tiles) {
        return _.uniq(_.map(tiles, function (model) {
            try {  // Tile
                return model.get('tile-id');
            } catch (err) {  // object
                return model['tile-id'];
            }
        }));
    };

    /**
     * @param {Integer} diff
     * @return thsi
     */
    this.updateCache = function (diff) {
        // right now it seems as if IR has a hard limit of 20
        this.options.IRCacheResultCount = Math.min(10,
            this.options.IRCacheResultCount + diff);
        return this;
    };

    /**
     * @param {Array} results
     * @return this
     */
    this.set = function (results) {
        // Simply add to our cached results list
        cachedResults = cachedResults.concat(results);
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
        // Change the category, category is a string passed
        // to data
        intentRank.options.category = category;
        intentRank.options.IRReset = true;

        if (!category) { // clear the category
            urlTemplate = intentRank.options.urlTemplates.campaign;
            console.debug("No category passed, clearing.");
            delete intentRank.options.category;
        } else { // Swap default url
            urlTemplate = intentRank.options.urlTemplates.category;
        }

        App.vent.trigger('change:category', category, intentRank);

        return intentRank;
    };
});
