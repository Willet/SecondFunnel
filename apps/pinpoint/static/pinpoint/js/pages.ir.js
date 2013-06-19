var PAGES = PAGES || {};

PAGES.intentRank = (function (me, details, mediator) {
    // PAGES.intentRank depends on PAGES.
    "use strict";

    var userClicks = 0,
        clickThreshold = 3;

    me.init = function () {
        // load data (if any)
    };

    me.updateClickStream = function (t, event) {
        /* Loads more content if user clicks has exceeded threshold.  On each click, loads related content below
           a block that the user has clicked. */
        var $target = $(event.currentTarget),
            data      = $target.data(),
            id        = data['product-id'] || data.id,
            exceededThreshold;

        if (details.page.offline) {
            return;
        }

        userClicks += 1;
        exceededThreshold = ((userClicks % clickThreshold) === 0);

        $.ajax({
            url: details.base_url + '/intentrank/update-clickstream/?callback=?',
            data: {
                'store': details.store.id,
                'campaign': details.page.id,
                'product_id': id
            },
            dataType: 'jsonp',
            success: function () {
                if (exceededThreshold) {
                    PAGES.loadMoreResults(true);
                }
            }
        });
    };

    me.updateContentStream = function (product) {
        /* @return: none */
        PAGES.loadMoreResults(false, product);
    };

    me.getInitialResults = function (callback, seed) {
        // callback function will receive a list of results as first param.
        PAGES.setLoadingBlocks(true);
        if (!_.isEmpty(details.backupResults) &&
                !('error' in details.backupResults)) {  // saved IR proxy error
            callback(details.backupResults);

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
                    success: function(results) {
                        callback(results);
                    },
                    error: function () {
                        callback(details.backupResults);
                    }
                });
            } else {
                callback(details.content);
            }
        }
        PAGES.setLoadingBlocks(false);
    };

    me.getMoreResults = function (callback, belowFold, related) {
        // callback function will receive a list of results as first param.
        PAGES.setLoadingBlocks(true);
        if (!details.page.offline) {
            $.ajax({
                url: details.base_url + '/intentrank/get-results/?callback=?',
                data: {
                    'store': details.store.id,
                    'campaign': details.page.id,

                    // TODO: Probably should be some calculated value
                    'results': 10,

                    // normally ignored, unless IR call fails and we'll resort to getseeds
                    'seeds': details.featured.id
                },
                dataType: 'jsonp',
                success: function(results) {
                    callback(results, belowFold, related);
                },
                error: function () {
                    callback(details.backupResults, belowFold, related);
                }
            });
        } else {
            callback(details.content, undefined, related);
        }
        PAGES.setLoadingBlocks(false);
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
        mediator.on('IR.updateClickStream', me.updateClickStream);
        mediator.on('IR.getMoreResults', me.getMoreResults);
        mediator.on('IR.invalidateIRSession', me.invalidateIRSession);
        mediator.on('IR.changeSeed', me.changeSeed);
        mediator.on('IR.changeCategory', me.changeCategory);
    } else {
        window.console && window.console.error && window.console.error(
            'Could not add pages.ir.js hooks to mediator'
        );
    }

    return me;
}(PAGES.intentRank || {}, PAGES.details || {}, Willet.mediator));