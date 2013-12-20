/*global App, Backbone, Marionette, imagesLoaded, console */
/**
 * @module intentRank
 */
App.module("intentRank", function (intentRank, App) {
    "use strict";

    var consecutiveFailures = 0,
        resultsAlreadyRequested = [];  // list of product IDs

    this.options = {
        'baseUrl': "http://intentrank-test.elasticbeanstalk.com/intentrank",
        'urlTemplates': {
            'campaign': "<%=url%>/page/<%=campaign%>/getresults",
            'content': "<%=url%>/page/<%=campaign%>/content/<%=id%>/getresults"
        },
        'add': true,
        'merge': true,
        'remove': false,
        'categories': {},
        'backupResults': [],
        'IRResultsCount': 10,
        'IRTimeout': 5000,
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
            'IRTimeout': options.IRTimeout || 5000,
            'content': options.content || [],
            'filters': options.filters || []
        });

        App.vent.trigger('intentRankInitialized', intentRank);
        return this;
    };

    /**
     * This function is a bridge between our IntentRank module and our
     * Discovery area.
     * It must be executed with a Backbone.Collection as context.
     *
     * @param options
     * @returns {promise}
     */
    this.fetch = function (options) {
        // 'this' IS NOT INTENTRANK
        var collection = this,
            deferred = new $.Deferred(),
            online = !App.option('page:offline', false),
            data = (resultsAlreadyRequested.length ? {
                'shown': resultsAlreadyRequested.join(',')
            } : undefined),
            opts = $.extend({}, {
                'results': 10,
                'add': true,
                'merge': true,
                'remove': false,
                'crossDomain': true,
                'xhrFields': {
                    'withCredentials': true
                },
                'data': data
            }, this.config, intentRank.options, options),
            backupResults = _.chain(intentRank.options.backupResults)
                .filter(intentRank.filter)
                .shuffle()
                .first(intentRank.options.IRResultsCount)
                .value();

        // if offline, return a backup list
        if (!online || collection.ajaxFailCount > 5) {
            return $.when(backupResults);
        }

        // if online, return the result, or a backup list if it fails.
        Backbone.Collection.prototype.fetch.call(this, opts)
            .done(function (results) {
                // reset fail counter
                collection.ajaxFailCount = 0;

                // SHUFFLE_RESULTS is always true
                deferred.resolve(_.shuffle(results));
                resultsAlreadyRequested = _.compact(intentRank.getTileIds(results));

                // restrict shown list to last 10 items max
                // (it was specified before?)
                if (resultsAlreadyRequested.length > intentRank.options.IRResultsCount) {
                    resultsAlreadyRequested = resultsAlreadyRequested.slice(-10);
                }
            })
            .fail(function () {
                // reset fail counter
                if (collection.ajaxFailCount) {
                    collection.ajaxFailCount++;
                } else {
                    collection.ajaxFailCount = 1;
                }

                deferred.resolve(backupResults);
                resultsAlreadyRequested = intentRank.getTileIds(backupResults);
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
     * general implementation
     *
     * @deprecated
     */
    this.getResults = function () {
        var args = Array.prototype.slice.apply(arguments);
        return this.fetch.apply(App.discovery.collection, args);
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
     * @oaram {Tile} tiles
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

    this.changeCategory = function (category) {
        // Change the category
        if (!_.findWhere(intentRank.options.categories,
            {'id': Number(category)})) {
            // requested category not configured for this page
            console.warn('Category ' + category + ' not found');
            return intentRank;
        }

        App.vent.trigger('intentRankChangeCategory', category, intentRank);

        intentRank.options.campaign = category;
        return intentRank;
    };
});
