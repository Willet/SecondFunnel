/*global SecondFunnel, Backbone, Marionette, imagesLoaded, console, broadcast */
/**
 * Masonry wrapper
 *
 * TODO: stage two refactor (change into layoutEngine instances or
 * integrate with Feed)
 *
 * @module layoutEngine
 */
SecondFunnel.module("layoutEngine", function (layoutEngine, SecondFunnel) {
    "use strict";

    var $document = $(document),
        $window = $(window),
        defaults = {
            'columnWidth': 255,
            'isAnimated': !SecondFunnel.support.mobile(),
            'transitionDuration': '0.4s',
            'isInitLayout': true,
            'isResizeBound': false,  // we are handling it ourselves
            'visibleStyle': {
                'opacity': 1,
                'transform': 'none',
                '-webkit-transform': 'none',
                '-moz-transform': 'none'
            },
            'hiddenStyle': {
                'opacity': 0,
                'transform': 'scale(1)',
                '-webkit-transform': 'scale(1)',
                '-moz-transform': 'none'
            }
        },
        opts;  // last-used options (used by clear())

    this.on('start', function () {  // this = layoutEngine
        if (SecondFunnel.discovery) {
            return this.initialize(SecondFunnel.discovery, SecondFunnel.options);
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

        SecondFunnel.vent.on('windowResize', function () {
            self.layout(view);
        });

        broadcast('layoutEngineInitialized', this, opts);
        return this;
    };

    /**
     * Perform a partial reload of the masonry object.
     * Less computationally expensive than reload().
     *
     * @returns this
     */
    this.layout = function (view) {
        setTimeout(function () {
            view.$el.masonry('layout');
        }, 100);
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
        var self = this;
        if ($target && $target.length) {
            var initialBottom = $target.position().top +
                $target.height();
            if (frag.length) {
                // Find a target that is low enough on the screen to insert after
                while ($target.position().top <= initialBottom &&
                    $target.next().length > 0) {
                    $target = $target.next();
                }
                $target.after(frag);
                self.reload(view);
            }
        } else if (fragment.length) {
            setTimeout(function () {
                view.$el
                    .append(fragment)
                    .masonry('appended', fragment);
            }, 100);
        }
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
