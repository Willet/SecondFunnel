var PAGES = PAGES || {};

PAGES.intentRank = (function (me, details, mediator) {
    // PAGES.intentRank depends on PAGES.
    "use strict";

    var userClicks = 0,
        clickThreshold = 3;

    me.init = function () {
        // load data (if any)
    };

    me.updateContentStream = function (product) {
        /* @return: none */
        PAGES.loadResults(false, product);
    };

    me.getInitialResults = function (callback, seed) {
        // callback function will receive a list of results as first param.
        if (PAGES.getLoadingBlocks()) {
            return;
        }

        PAGES.setLoadingBlocks(true);
        if (!_.isEmpty(details.backupResults) &&
                !('error' in details.backupResults)) {  // saved IR proxy error
            callback(details.backupResults);
            PAGES.setLoadingBlocks(false);

            details.backupResults = [];
        } else {
            if (!details.page.offline) {
                $.ajax({
                    url: details.base_url + '/intentrank/get-seeds/?callback=?',
                    data: {
                        'store': details.store.id,
                        'campaign': details.page.id,
                        'seeds': details.product['product-id']
                    },
                    dataType: 'jsonp',
                    timeout: 5000,  // 5000 ~ 10000
                    success: function(results) {
                        callback(results);
                        PAGES.setLoadingBlocks(false);
                    },
                    error: function () {
                        callback(details.backupResults);
                        PAGES.setLoadingBlocks(false);
                    }
                });
            } else {
                callback(details.content);
                PAGES.setLoadingBlocks(false);
            }
        }
    };

    me.getResults = function (callback, belowFold, related) {
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

        if (!details.page.offline) {
            $.ajax({
                url: details.base_url + '/intentrank/get-results/?callback=?',
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
                    callback(results, belowFold, related);
                    PAGES.setLoadingBlocks(false);
                },
                error: function () {
                    callback(details.backupResults, belowFold, related);
                    PAGES.setLoadingBlocks(false);
                }
            });
        } else {
            callback(details.content, undefined, related);
            PAGES.setLoadingBlocks(false);
        }
    };

    me.invalidateIRSession = function () {
        $.ajax({
            url: details.base_url + '/intentrank/invalidate-session/?callback=?',
            dataType: 'jsonp'
        });
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
        mediator.on('IR.updateContentStream', me.updateContentStream);
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