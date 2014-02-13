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
            }
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

        view.$el.masonry(opts);

        App.vent.on('windowResize', function () {
            self.layout(view);
        });

        App.vent.trigger('layoutEngineInitialized', this, opts);
        return this;
    };

    /**
     * Perform a partial reload of the masonry object.
     * Less computationally expensive than reload().
     *
     * @returns this
     */
    this.layout = function (view) {
        view.$el.masonry('layout');
        return this;
    };

    /**
     * Perform a complete reload of the masonry object.
     *
     * @returns this
     */
    this.reload = function (view) {
        view.$el.masonry('reloadItems');
        view.$el.masonry();
        return this;
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
            initialBottom;

        if (!(fragment && fragment.length)) {
            return this;  // nothing to add
        }

        // collect fragments, append in batch
        frags = frags.concat(fragment);
        if (frags.length >= App.option('IRResultsCount', 10)) {
            fragment = frags;
            frags = [];
        } else {
            return this;  // save for later
        }

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
