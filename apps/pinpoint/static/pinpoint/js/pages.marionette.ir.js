SecondFunnel.module("intentRank", function (intentRank, SecondFunnel) {
    "use strict";

    var $document = $(document),
        $window = $(window);

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
            'content': options.content || []
        });

        if (online) {
            intentRank.getResults = intentRank.getResultsOnline;
        } else {
            intentRank.getResults = intentRank.getResultsOffline;
        }

        broadcast('intentRankInitialized', intentRank);
        return this;
    };

    intentRank.getResultsOffline = function (options, callback) {
        broadcast('beforeIntentRankGetResultsOffline', options, callback, intentRank);
        var args = _.toArray(arguments).slice(2);
        args.unshift(intentRank.options.content);

        broadcast('intentRankGetResultsOffline', options, callback, intentRank);
        return callback.apply(callback, args);
    };

    intentRank.getResultsOnline = function (overrides, callback) {
        var opts, uri, args;

        // build a one-off options object for the request.
        opts = $.extend(true, {}, intentRank.options, {
            'url': intentRank.options.baseUrl
        });
        $.extend(opts, overrides);

        uri = _.template(opts.urlTemplates[opts.type || 'campaign'], opts);
        args = _.toArray(arguments).slice(2);

        broadcast('beforeIntentRankGetResultsOnline', opts, callback, intentRank);
        ($.jsonp || $.ajax)({
            'url': uri,
            'data': {
                'results': opts.IRResultsCount
            },
            'contentType': "json",
            'dataType': 'jsonp',
            'callbackParameter': 'callback',  // $.jsonp only
            'timeout': opts.IRTimeout,
            'success': function (results) {
                // Check for non-empty results.
                results = (results && results.length)?
                          results:
                    // If no results, fetch from backup
                          _.shuffle(opts.backupResults);
                results = _.first(results, opts.IRResultsCount);
                args.unshift(results);
                return callback.apply(callback, args);
            },
            'error': function (jqXHR, textStatus, errorThrown) {
                // $.jsonp calls this func as function (xOptions, textStatus)
                console.error('AJAX / JSONP call ' + textStatus + ': ' +
                    (errorThrown || jqXHR.url));
                // On error, fall back to backup results
                var results = _.shuffle(opts.backupResults);
                results = _.first(results, opts.IRResultsCount);
                args.unshift(results);
                return callback.apply(callback, args);
            }
        });

        broadcast('intentRankgetResultsOnline', opts, callback,
            intentRank);
    };

    intentRank.changeCategory = function (category) {
        // Change the category
        if (!_.findWhere(intentRank.options.categories,
            {'id': Number(category)})) {
            // requested category not configured for this page
            if (SecondFunnel.option('debug', SecondFunnel.QUIET) >=
                SecondFunnel.WARNING) {
                console.warn('Category ' + category + ' not found');
            }
            return;
        }

        broadcast('intentRankChangeCategory', category, intentRank);

        intentRank.options.campaign = category;
        return intentRank;
    };
});
