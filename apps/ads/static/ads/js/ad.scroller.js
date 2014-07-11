// show new products every so often
App.module("scroller", function (module, App) {
    "use strict";

    this.timer = undefined;

    this.initialize = function () {
        this.timer = setInterval(this.refreshFeed, 5000);
    };

    // every 5 seconds, remove the top few tiles from the feed... creating
    // the illusion that the feed is scrolling.
    this.refreshFeed = function () {
        var i = 0, feed, tilesToRemove = [];

        if (!(App.discoveryArea && App.discoveryArea.currentView)) {
            // app hasn't run yet.
            return;
        }

        feed = App.discoveryArea.currentView;

        // remove the first 4 tiles.
        feed.children.each(function (tile) {
            i++;
            if (i < 5) {
                tile.close();
                feed.children.remove(tile);
                tilesToRemove.push(tile);
            }
        });

        feed.on('loadingFinished', function () {
            feed.children.each(function (tile) {
                i++;
                if (i < 5) {
                    tile.close();
                    feed.children.remove(tile);
                    tilesToRemove.push(tile);
                }
            });
            App.layoutEngine.layout(feed);
        });

        App.layoutEngine.remove(feed, tilesToRemove);

        // um, if there is some chance that there won't be enough tiles
        // in the ad, then get some more.
        if (i < 10) {
            feed.getTiles();
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
