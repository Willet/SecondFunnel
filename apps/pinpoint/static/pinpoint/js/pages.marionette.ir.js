SecondFunnel.module("intentRank", function (intentRank) {
    "use strict";

    var $document = $(document),
        $window = $(window);

    intentRank.base = "http://intentrank-test.elasticbeanstalk.com/intentrank";
    intentRank.templates = {
        'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
        'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
    };

    intentRank.initialize = function (options) {
        // Any additional init declarations go here
        var page = options.page || {},
            online = !page.offline;

        _.extend(intentRank, {
            'base': options.IRSource || this.base,
            'store': options.store,
            'campaign': options.campaign,
            // @deprecated: options.categories will be page.categories
            'categories': page.categories || options.categories || {},
            'backupResults': options.backupResults || [],
            'IRResultsCount': options.IRResultsCount || 10,
            'IRTimeout': options.IRTimeout || 5000,
            'content': options.content || [],
            'getResults': online ?
                          intentRank.getResultsOnline :
                          intentRank.getResultsOffline
        });

        broadcast('intentRankInitialized', intentRank);
    };

    intentRank.getResultsOffline = function (options, callback) {
        broadcast('beforeIntentRankGetResultsOffline', options,
            callback, intentRank);
        var args = _.toArray(arguments).slice(2);
        args.unshift(intentRank.content);

        broadcast('intentRankGetResultsOffline', options, callback,
            intentRank);
        return callback.apply(callback, args);
    };

    intentRank.getResultsOnline = function (options, callback) {
        broadcast('beforeIntentRankGetResultsOnline', options,
            callback, intentRank);

        var uri = _.template(intentRank.templates[options.type],
                _.extend({}, options, intentRank, {
                    'url': intentRank.base
                })),
            args = _.toArray(arguments).slice(2);

        ($.jsonp || $.ajax)({
            'url': uri,
            'data': {
                'results': intentRank.IRResultsCount
            },
            'contentType': "json",
            'dataType': 'jsonp',
            'callbackParameter': 'callback',  // $.jsonp only
            'timeout': intentRank.IRTimeout,
            'success': function (results) {
                // Check for non-empty results.
                results = results.length ?
                          results :
                    // If no results, fetch from backup
                          _.shuffle(intentRank.backupResults);
                results = _.first(results, intentRank.IRResultsCount);
                args.unshift(results);
                return callback.apply(callback, args);
            },
            'error': function (jqXHR, textStatus, errorThrown) {
                // $.jsonp calls this func as function (xOptions, textStatus)
                console.error('AJAX / JSONP call ' + textStatus + ': ' +
                    (errorThrown || jqXHR.url));
                // On error, fall back to backup results
                var results = _.shuffle(intentRank.backupResults);
                results = _.first(results, intentRank.IRResultsCount);
                args.unshift(results);
                return callback.apply(callback, args);
            }
        });

        broadcast('intentRankgetResultsOffline', options, callback,
            intentRank);
    };

    intentRank.changeCategory = function (category) {
        // Change the category; category has been validated
        // by the CategoryView, so a check isn't necessary
        broadcast('intentRankChangeCategory', category, intentRank);

        intentRank.campaign = category;
        return intentRank;
    };
});
