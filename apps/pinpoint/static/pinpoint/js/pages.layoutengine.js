/*global App, Backbone, Marionette, imagesLoaded, console, _, $*/
/**
 * Masonry wrapper
 *
 * TODO: stage two refactor (change into layoutEngine instances or
 * integrate with Feed)
 *
 * @module layoutEngine
 */
App.module("layoutEngine", function (layoutEngine, App) {
    "use strict";

    var $document = $(document),
        $window = $(window),
        currentWidth = 0,
        defaults = {
            'columnWidth': 255,
            'isAnimated': App.support.transform3d() &&  // only if it is fast
                          !App.support.mobile(),  // & "phones don't animate"
            'transitionDuration': '0.4s',
            'isInitLayout': true,
            'isResizeBound': false,  // we are handling it ourselves
            'visibleStyle': {
                'opacity': 1,
                'transform': 'translate3d(0, 0, 0)',
                '-webkit-transform': 'translate3d(0, 0, 0)',
                '-moz-transform': 'translate3d(0, 0, 0)'
            },
            'hiddenStyle': {
                'opacity': 0,
                'transform': 'scale(1)',
                '-webkit-transform': 'scale(1)',
                '-moz-transform': 'none'
            },
            'minDesktopColumns': 2, // minimum number of columns (default: 2)
            'minMobileColumns': 2
        },
        frags = [],  // common fragment storage
        opts;  // last-used options (used by clear())

    this.on('start', function () {  // this = layoutEngine
        if (App.discovery) {
            this.initialize(App.discovery, App.options);
        }
    });

    /**
     * Initializes the underlying masonry instance onto the discovery target.
     *
     * @param {View} view         a Feed object.
     * @param options {Object}    overrides.
     * @returns this
     */
    this.initialize = function (view, options) {
        var self = this;
        opts = $.extend({}, defaults, options, _.get(options, 'masonry'));

        this.layout(view);

        App.vent.on('windowResize', function () {
            self.layout(view);
        });

        App.vent.trigger('layoutEngineInitialized', this, opts);
        return this;
    };

    /**
     * Recalculates the width needed to configure
     * the Masonry instance.
     *
     * @param {View} view          a Feed object
     * @returns Double
     */
    this.recalculateWidth = function (view) {
        var selector = opts.itemSelector + ':not(.wide, .full)',
            columnWidth = opts.columnWidth || defaults.columnWidth || 1,
            minColumns = App.support.mobile() ?
                opts.minMobileColumns || defaults.minMobileColumns :
                opts.minDesktopColumns || defaults.minDesktopColumns,
            width = view.$el.outerWidth() || 1024;

        if (width >= (minColumns + 1) * columnWidth) {
            // columnWidth or dynamicWidth apply as we've passed the threshold
            // where the layoutEngine is responsible for sizing
            width = Math.max($(selector).outerWidth() - 0.5, columnWidth);
        } else {
            // size based on the minimum number of columns to show
            width = width / minColumns;
        }

        return width;
    };

    /**
     * Perform a partial reload of the masonry object.
     * Less computationally expensive than reload().
     *
     * @returns this
     */
    this.layout = function (view) {
        var _opts = _.extend({}, opts);
        // Dynamic columnWidth recalculation
        _opts.columnWidth = this.recalculateWidth(view);
        currentWidth = _opts.columnWidth;
        view.$el.masonry(_opts);

        return this;
    };

    /**
     * Returns the current column width.
     *
     * @returns this
     */
    this.width = function () {
        return currentWidth;
    };

    /**
     * Perform a complete reload of the masonry object.
     *
     * @returns this
     */
    this.reload = function (view) {
        view.$el.masonry('reloadItems');
        this.layout(view);
        return this;
    };

    /**
     * Given one or many TileViews, remove the element from the page.
     * @param view   the discovery area view
     * @param tiles  array of tileViews.
     */
    this.remove = function (view, tiles) {
        var i, self = this, views = tiles;
        if (!views instanceof Array) {
            views = [views];
        }
        for (i = 0; i < views.length; i++) {
            if (views[i].el) {
                views[i] = views[i].el;
            }
        }
        view.$el.masonry('remove', views);
        this.layout(view);
    };

    /**
     * Returns the options with which the layout engine is running.
     * Used mainly for testing.
     *
     * @returns {Object}
     */
    this._opts = function () {
        return opts;
    };

    /**
     * Mix of append() and insert()
     *
     * @param {View} view       a Feed object.
     * @param fragment {array}: a array of elements.
     * @param $target {jQuery}: if given, fragment is inserted after the target,
     *                          if not, fragment is appended at the bottom.
     * @returns {Deferred}
     */
    this.add = function (view, fragment, $target) {
        var self = this,
            initialBottom,
            threshold = App.option('IRResultsReturned', 10),
            callback = function () {
                view.trigger('after:item:appended', view, fragment);
                return true;
            };

        if (!(fragment && fragment.length)) {
            callback();
            return this;  // nothing to add
        }

        // collect fragments, append in batch
        frags = frags.concat(fragment);
        if (frags.length >= threshold) {
            fragment = frags;
            frags = [];
        } else {
            return this;  // save for later
        }

        // Attach the callback
        view.$el.masonry('on', 'layoutComplete', callback);

        // inserting around a given tile
        if ($target && $target.length) {
            initialBottom = $target.position().top + $target.height();
            // Find a target that is low enough on the screen to insert after
            while ($target.position().top <= initialBottom &&
                   $target.next().length > 0) {
                $target = $target.next();
            }
            $target.after(fragment);
            return self.reload(view);
        }

        // inserting at the bottom
        view.$el.append(fragment).masonry('appended', fragment);
        return this;
    };

    /**
     * Resets the LayoutEngine's instance so that it is empty.
     * Conventional $el.empty() doesn't work because the container height
     * is set by masonry.
     */
    this.empty = function (view) {
        view.$el
            .masonry('destroy')
            .html("")
            .css('position', 'relative')
            .masonry(opts);
    };
});
