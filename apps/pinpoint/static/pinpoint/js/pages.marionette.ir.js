/*global SecondFunnel, Backbone, Marionette, imagesLoaded, console, broadcast */
SecondFunnel.module("intentRank", function (intentRank, SecondFunnel) {
    "use strict";

    var consecutiveFailures = 0;

    intentRank.options = {
        'baseUrl': "http://intentrank-test.elasticbeanstalk.com/intentrank",
        'urlTemplates': {
            'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
            'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
        },
        'categories': {},
        'backupResults': [],
        'IRResultsCount': 10,
        'IRTimeout': 5000,
        'store': {},
        'content': []
    };

    intentRank.initialize = function (options) {
        // Any additional init declarations go here
        var page = options.page || {},
            online = !page.offline;

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

        if (online) {
            intentRank.getResults = intentRank.getResultsOnline;
        } else {
            intentRank.getResults = intentRank.getResultsOffline;
        }

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
    intentRank.filter = function (content, selector) {
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
     * @param overrides (unused)
     * @returns something $.when() accepts
     */
    intentRank.getResultsOffline = function (overrides) {
        console.error('getResultsOffline');
        // instantly mark the deferral as complete.
        return _.chain(intentRank.options.backupResults)
            .filter(intentRank.filter)
            .shuffle()
            .first(intentRank.options.IRResultsCount)
            .value();
    };

    /**
     * @param overrides
     * @returns $.Deferred()
     */
    intentRank.getResultsOnline = function (overrides) {
        var ajax, deferred, opts, uri, backupResults;

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

        if (consecutiveFailures > 5) {
            // API is dead. serve backup results instantly
            deferred.resolve(backupResults);
        } else {
            ajax = ($.jsonp || $.ajax)({
                'url': uri,
                'data': {
                    'results': opts.IRResultsCount
                },
                'contentType': "application/javascript",
                'dataType': 'jsonp',
                'callbackParameter': 'callback',  // $.jsonp only; $.ajax uses 'jsonpCallback'
                'timeout': opts.IRTimeout
            });
            ajax.done(function (results) {
                consecutiveFailures = 0;  // reset

                deferred.resolve(
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

                if (consecutiveFailures > 5) {
                    console.error(
                        'Too many consecutive endpoint failures. ' +
                        'All subsequent results will be backup results.');
                }

                deferred.resolve(backupResults);
            });
        }

        // promises are shared w/ other objects, while deferred should be
        // kept private, says the internet
        return deferred.promise();
    };

    intentRank.changeCategory = function (category) {
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
