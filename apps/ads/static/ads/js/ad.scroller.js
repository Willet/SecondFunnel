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
        var feed, tilesToRemove = [], cellsRemoved = 0;

        if (!(App.discoveryArea && App.discoveryArea.currentView)) {
            // app hasn't run yet.
            return;
        }

        feed = App.discoveryArea.currentView;

        // remove "rows" (two cells worth of tiles)
        feed.children.each(function (tile, idx) {
            var columnCount = App.option('columnCount', 2),  // how many columns the layout has (currently guaranteed to be 2)
                removeRows = 2,  // magic number
                removeCells = removeRows * columnCount;
            if (cellsRemoved >= removeCells && cellsRemoved % columnCount === 0) {
                return;
            }
            tile.close();
            feed.children.remove(tile);
            tilesToRemove.push(tile);

            if (tile.model.get('orientation') !== 'landscape') {
                cellsRemoved++;
            } else if (tile.model.get('orientation') === 'landscape') {
                cellsRemoved += 2;
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
