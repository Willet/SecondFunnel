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

    /**
     * @param overrides (not used)
     * @returns $.Deferred() (blank, with deferred methods)
     */
    intentRank.getResultsOffline = function (overrides) {
        console.error('getResultsOffline');
        // instantly mark the deferral as complete.
        return intentRank.options.backupResults;
    };

    /**
     * @param overrides
     * @returns $.Deferred()
     */
    intentRank.getResultsOnline = function (overrides) {
        console.error('getResultsOnline');
        var deferred, opts, uri, args, backupResults;

        // build a one-off options object for the request.
        opts = $.extend(true, {}, intentRank.options, {
            'url': intentRank.options.baseUrl
        });
        $.extend(opts, overrides);

        backupResults = _.first(
                _.shuffle(opts.backupResults),
                opts.IRResultsCount);

        uri = _.template(opts.urlTemplates[opts.type || 'campaign'], opts);
        args = _.toArray(arguments).slice(2);

        // http://stackoverflow.com/a/18986305/1558430
        deferred = new $.Deferred();

        ($.jsonp || $.ajax)({
                'url': uri,
                'data': {
                    'results': opts.IRResultsCount
                },
                'contentType': "application/javascript",
                'dataType': 'jsonp',
                'callbackParameter': 'callback',  // $.jsonp only; $.ajax uses 'jsonpCallback'
                'timeout': opts.IRTimeout
            })
            .always(function (results) {
                // NOTE: in the case of .fail, results will be a jqXHR
                // instead of the results array.
                if (!(results && results.length)) {
                    // "results.length <= 0" is still false if it is undefined
                    results = opts.backupResults;
                }
                // trim the number of results if IR returns too many
                results = _.first(_.shuffle(results), opts.IRResultsCount);

                deferred.resolve(results);
            })
            .fail(function (jqXHR, textStatus, errorThrown) {
                // $.jsonp calls this func as function (jqXHR, textStatus)
                console.error('AJAX / JSONP call ' + textStatus + ': ' +
                    (errorThrown || jqXHR.url));
                deferred.resolve(backupResults);
            });

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
            return;
        }

        broadcast('intentRankChangeCategory', category, intentRank);

        intentRank.options.campaign = category;
        return intentRank;
    };
});
