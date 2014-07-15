// show new products every so often
App.module("scroller", function (module, App) {
    "use strict";

    this.timer = undefined;

    this.initialize = function () {
        this.timer = setInterval(this.refreshFeed, 1000);
    };

    // every 5 seconds, remove the top few tiles from the feed... creating
    // the illusion that the feed is scrolling.
    this.refreshFeed = function () {
        var feed, tilesToRemove = [];

        if (!(App.discoveryArea && App.discoveryArea.currentView)) {
            // app hasn't run yet.
            return;
        }

        feed = App.discoveryArea.currentView;

        // remove the first 4 tiles (or 3 tiles, if the last one is a landscape).
        feed.children.each(function (tile, idx) {
            if (idx < 3 || (
                    idx === 3 &&
                    tilesToRemove.length % 2 === 0 &&
                    tile.model.get('orientation') !== 'landscape'
                )) {
                tile.close();
                feed.children.remove(tile);
                tilesToRemove.push(tile);
            }
        });

        App.layoutEngine.remove(feed, tilesToRemove);

        // if there is some chance that there won't be enough tiles
        // in the ad, then get some more.
        if (feed.children.length < 20) {
            feed.toggleLoading(false).getTiles();
        }

        setTimeout(function () {
            // remove noscroll after scroll is set
            App.vent.trigger('scrollStopped');
        }, 100);
    };

    this.on('start', function () {
        return this.initialize(App.options);
    });

    this.on('close', function () {
        clearInterval(this.timer);
    });
});
