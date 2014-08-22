/*global console, App */
'use strict';

// show new products every so often
module.exports = function (module, App) {

    this.timer = undefined;

    this.initialize = function () {
        this.timer = setInterval(this.refreshFeed, 8000);
    };

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
            if (!tile.$el.is(':visible')) {
                return;
            }
            tilesToRemove.push(tile);

            if (tile.model.get('orientation') !== 'landscape') {
                cellsRemoved++;
            } else if (tile.model.get('orientation') === 'landscape') {
                cellsRemoved += 2;
            }
        });

        feed.removeTiles(tilesToRemove);

        // if there is some chance that there won't be enough tiles
        // in the ad, then get some more.
        if (feed.children.length < 20) {
            feed.pageScroll();
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
};
