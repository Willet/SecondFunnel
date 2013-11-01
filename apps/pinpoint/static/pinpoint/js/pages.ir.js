/*global SecondFunnel, Backbone, Marionette, imagesLoaded, console, broadcast */
/**
 * @module intentRank
 */
SecondFunnel.module("intentRank", function (intentRank, SecondFunnel) {
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
        return this.initialize(SecondFunnel.options);
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

        broadcast('intentRankInitialized', intentRank);
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
        var deferred = new $.Deferred(),
            online = !SecondFunnel.option('page:offline', false),
            opts = $.extend({}, {
                'results': 10,
                'add': true,
                'merge': true,
                'remove': false,
                'crossDomain': true,
                'data': {
                    'shown': resultsAlreadyRequested.join(',')
                }
            }, this.config, intentRank.options, options),
            backupResults = _.chain(intentRank.options.backupResults)
                .filter(intentRank.filter)
                .shuffle()
                .first(intentRank.options.IRResultsCount)
                .value();

        // if offline, return a backup list
        if (!online) {
            return $.when(backupResults);
        }

        // if online, return the result, or a backup list if it fails.
        Backbone.Collection.prototype.fetch.call(this, opts)
            .done(function (results) {
                deferred.resolve(_.shuffle(results));
                resultsAlreadyRequested = intentRank.getTileIds(results);
            })
            .fail(function () {
                deferred.resolve(backupResults);
                resultsAlreadyRequested = intentRank.getTileIds(backupResults);
            });

        return deferred.promise();
    };

    /**
     * Filter the content based on the selector
     * passed and the criteria/filters defined in the SecondFunnel options.
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
     */
    this.getResults = function () {
        try {
            var online = !SecondFunnel.option('page:offline', false);
            if (online) {
                return intentRank.getResultsOnline.apply(intentRank, arguments);
            }
        } catch (e) {}
        return intentRank.getResultsOffline.apply(intentRank, arguments);
    };

    /**
     * A unique list of all tiles shown on the page.
     * @returns {array}
     */
    this.getAllResultsShown = function () {
        try {
            return SecondFunnel.discovery.collection.models;
        } catch (err) {
            // first call, SecondFunnel.discovery is not a var yet
            return SecondFunnel.option('initialResults') || [];
        }
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

        broadcast('intentRankChangeCategory', category, intentRank);

        intentRank.options.campaign = category;
        return intentRank;
    };
});
