/*global $, _, App, Marionette, console */
/**
 * @module viewport
 */
App.module('viewport', function (viewport, App) {
    "use strict";
    var $window = $(window),
        $document = $(document),
        getMeta = function () {
            var tag = $('meta[name="viewport"]', 'head');

            if (!tag.length && window.devicePixelRatio) {
                // if no viewport is found of it, it will be made.
                // (assuming the device supports it)
                tag = $('<meta />', {
                    'name': 'viewport'
                });
                $('head').append(tag);
            }
            return tag;
        };

    /**
     * Returns an array containing viewport analysis.
     * Used by .scale().
     *
     * @param {int} desiredWidth
     * @return {Array} [enabled, width, scale, meta], some of which can
     *                 be undefined if not applicable.
     */
    this.determine = function (desiredWidth) {
        var adjustedScale,
            proposedMeta,
            maxMobileWidth = 511,
            maxTabletWidth = 767,
            enabled;

        enabled = App.option('lockWidth', function () {
            return true;
        });

        if (typeof enabled === 'function') {
            enabled = enabled();
        }

        if (enabled !== true) {
            console.warn('viewport agent disabled.');
            return [false, undefined, undefined, 'disabled'];
        }

        if (!window.devicePixelRatio || window.devicePixelRatio <= 1) {
            console.warn('viewport agent called on device with unsupported ppi.');
            return [false, undefined, undefined, 'unsupported ppi'];
        }

        if (typeof desiredWidth === 'function') {
            desiredWidth = desiredWidth();
        }

        if (typeof desiredWidth !== 'number') {
            console.warn('viewport agent not called with number.');
            return [false, undefined, undefined, 'width NaN'];
        }

        if (!desiredWidth || desiredWidth <= 100 || desiredWidth > 2048) {
            console.warn('viewport agent called with invalid width.');
            return [false, undefined, undefined, 'width invalid'];
        }

        // pick the lowest of: - window width
        //                     - desired width
        //                     - max mobile width (if mobile)
        //                     - max tablet width (if tablet)
        if ($.browser.mobile && !$.browser.tablet) {
            desiredWidth = Math.min($window.width(), maxMobileWidth,
                desiredWidth, window.outerWidth);
        } else if (App.support.isAniPad()) {
            desiredWidth = 1024;
        } else if ($.browser.tablet) {
            desiredWidth = Math.min($window.width(), maxTabletWidth,
                desiredWidth, window.outerWidth);
        } else {
            desiredWidth = Math.min($window.width(), desiredWidth,
                window.outerWidth);
        }

        // http://stackoverflow.com/a/6134070/1558430
        adjustedScale = parseFloat(Math.round(Math.min(
            10,  // viewport scale > 10 is not allowed.
            ($window.width() / desiredWidth).toFixed(2)
        ) * 100) / 100).toFixed(2);
        proposedMeta = "user-scalable=no," +
                       "width=" + desiredWidth + "," +
                       "initial-scale=" + adjustedScale + "," +
                       "minimum-scale=" + adjustedScale + "," +
                       "maximum-scale=" + adjustedScale;

        // it's enabled
        return [true, desiredWidth, adjustedScale, proposedMeta];
    };

    /**
     * attempt to lock the viewport to appear as wide as desiredWidth
     * by scaling the entire viewport.
     *
     * the meta viewport tag is NOT standard, and does NOT work on all devices.
     * (this concerns mostly IE10 on Windows Phone)
     *
     * @param {int} desiredWidth
     * @returns undefined
     */
    this.scale = function (desiredWidth) {
        desiredWidth = desiredWidth || 1024;  // screen defaults to full width.
        var analysis = viewport.determine(desiredWidth),
            metaTag = getMeta(),
            proposedMeta = '';
        //  allowed to scale,       found a meta tag
        if (analysis[0] === true && metaTag.length >= 1) {
            // if both tag and condition exist
            proposedMeta = analysis[3];
            if (metaTag.prop('content') !== proposedMeta) {
                // avoid re-rendering: edit tag only if it needs to change
                metaTag.prop('content', proposedMeta);
                App.vent.trigger('viewportResized', desiredWidth);
            }
        } else {
            App.vent.trigger('viewportNotResized', analysis[3]);
        }
    };

    App.vent.on('beforeInit', function () {
        // single call func removes args
        viewport.scale();
    });
    App.vent.on('finished', function () {
        // single call func removes args
        viewport.scale();
    });
    App.vent.on('rotate', viewport.scale);
});
