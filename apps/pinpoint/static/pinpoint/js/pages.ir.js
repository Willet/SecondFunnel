var PAGES = PAGES || {};

PAGES.intentRank = (function (me, details, mediator) {
    // PAGES.intentRank depends on PAGES.
    "use strict";

    var userClicks = 0,
        clickThreshold = 3,
        campaignResultsUrl = "<%=url%>/store/<%=store%>/campaign/<%=campaign%>/getresults",
        contentResultsUrl = "<%=url%>/store/<%=store%>/campaign/<%=campaign%>/content/<%=id%>/getresults";

    me.init = function () {
        // load data (if any)
    };

    me.getResults = function (callback, args, related) {
        var relatedData = $(related).data() || {},
            urlParams = {
                'url': details.base_url,
                'store': details.store.id,
                'campaign': details.page.id,
                'id': relatedData['db-id']
            },
            url;

        // callback function will receive a list of results as first param.
        if (PAGES.getLoadingBlocks()) {
            return;
        }

        PAGES.setLoadingBlocks(true);

        /* TODO: If there are pre-loaded results, start with those?
            if (!_.isEmpty(details.backupResults) &&
                !('error' in details.backupResults)) {  // saved IR proxy error
                callback(details.backupResults);
                PAGES.setLoadingBlocks(false);

                details.backupResults = [];
            } else {
        */

        // Not sure what this element will be called
        if (relatedData['db-id']) {
            url = _.template(contentResultsUrl, urlParams);
        } else {
            url = _.template(campaignResultsUrl, urlParams);
        }

        if (!details.page.offline) {
            $.ajax({
                url: url,
                data: {
                    'store': details.store.id,
                    'campaign': details.page.id,

                    // TODO: Probably should be some calculated value
                    'results': 10,

                    // normally ignored, unless IR call fails and we'll resort to getseeds
                    // Previously, `details.product['product-id']` was used... why?
                    'seeds': details.featured.id
                },
                dataType: 'jsonp',
                timeout: 5000,  // 5000 ~ 10000
                success: function(results) {
                    callback.apply(this, [results].concat(args));
                    PAGES.setLoadingBlocks(false);
                },
                error: function () {
                    callback.apply(this, [details.backupResults].concat(args))
                    PAGES.setLoadingBlocks(false);
                }
            });
        } else {
            callback.apply(this, [details.content].concat(args));
            PAGES.setLoadingBlocks(false);
        }
    };

    me.changeSeed = function (seed) {
        // If you're calling this function, you probably know what
        // you're doing...

        // Usually called in conjunction with `changeCategory`...

        if (!seed) {
            return;
        }

        details.product['product-id'] = seed;
    };

    me.changeCategory = function (category) {
        var categories = details.page.categories;
        if (!categories || !_.findWhere(categories, {'id': '' + category})) {
            return;
        }

        // If there are categories, and a valid category is supplied
        // change the category
        details.page.id = category;
        mediator.fire('tracking.changeCampaign', [category]);
    };

    // register (most) PAGES.intentRank events.
    if (mediator) {
        mediator.on('IR.init', me.init);
        mediator.on('IR.getInitialResults', me.getResults);
        mediator.on('IR.getResults', me.getResults);
        mediator.on('IR.changeSeed', me.changeSeed);
        mediator.on('IR.changeCategory', me.changeCategory);
    } else {
        window.console && window.console.error && window.console.error(
            'Could not add pages.ir.js hooks to mediator'
        );
    }

    return me;
}(PAGES.intentRank || {}, PAGES.details || {}, Willet.mediator));