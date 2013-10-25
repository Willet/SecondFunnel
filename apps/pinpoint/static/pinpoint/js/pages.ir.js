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
            return [];
        }
    };

    /**
     * @oaram {Tile} tiles
     * @return {array} unique list of tile ids
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
     * @param overrides (unused)
     * @returns something $.when() accepts
     */
    this.getResultsOffline = function (overrides) {
        // instantly mark the deferral as complete.
        return $.when(
            _.chain(intentRank.options.backupResults)
            .filter(intentRank.filter)
            .shuffle()
            .first(intentRank.options.IRResultsCount)
            .value());
    };

    /**
     * @param overrides
     * @returns $.Deferred()
     */
    this.getResultsOnline = function (overrides) {
        var self = this,
            ajax, deferred, opts, uri, backupResults,
            irFailuresAllowed = SecondFunnel.option('IRFailuresAllowed', 5);

        // build a one-off options object for the request.
        opts = $.extend(true, {}, intentRank.options, {
            'url': intentRank.options.baseUrl
        });
        $.extend(opts, overrides);

        uri = _.template(opts.urlTemplates[opts.type || 'campaign'], opts);
        backupResults = _.chain(opts.backupResults)
            .filter(intentRank.filter)
            .shuffle()
            .first(opts.IRResultsCount)
            .value();

        // http://stackoverflow.com/a/18986305/1558430
        deferred = new $.Deferred();

        if (consecutiveFailures > irFailuresAllowed) {
            // API is dead. serve backup results instantly
            deferred.resolve([]);  // deferred.resolve([backupResults]); // TODO: remove
        } else {
            ajax = $.ajax({
                'url': uri,
                'data': {
                    'results': opts.IRResultsCount,
                    'shown': resultsAlreadyRequested.join(',')
                },
                'timeout': opts.IRTimeout
            });
            ajax.done(function (results) {
                consecutiveFailures = 0;  // reset

                resultsAlreadyRequested = self.getTileIds(results);

                return deferred.resolve(
                    // => list of n qualifying products
                    _.chain(results || opts.backupResults)
                        .filter(intentRank.filter)
                        .shuffle()
                        // trim the number of results if IR returns too many
                        .first(opts.IRResultsCount)
                        .value()
                );
            });
            ajax.fail(function (jqXHR, textStatus, errorThrown) {
                // $.jsonp calls this func as function (jqXHR, textStatus)
                console.error('AJAX / JSONP ' + textStatus + ': ' +
                    (errorThrown || jqXHR.url));

                consecutiveFailures++;

                if (consecutiveFailures > irFailuresAllowed) {
                    console.error(
                        'Too many consecutive endpoint failures. ' +
                        'All subsequent results will be backup results.');
                }

                return deferred.resolve(backupResults);
            });
        }

        // promises are shared w/ other objects, while deferred should be
        // kept private, says the internet
        return deferred.promise();
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
