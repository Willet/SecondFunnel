(function (app) {
    "use strict";
    app.module('viewport', function (viewport, SecondFunnel) {
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
         * returns an array containing viewport analysis
         *
         * @param {int} desiredWidth
         * @return {Array} enabled[, width, scale, meta], some of which can
         *                 be undefined if not applicable.
         */
        viewport.determine = function (desiredWidth) {
            var enabled = app.option('lockWidth', function () {
                    return $.browser.mobile;
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

            desiredWidth = desiredWidth || app.option('desiredWidth') || function () {
                // 767 is the last width to show as mobile.
                // screen.height is screen.width prior to rotation.
                // 48: android UI bar overestimation
                var w = Math.min(screen.width + 48, screen.height + 48,
                                 $window.width(), 767);
                return w;
            };

            if (typeof desiredWidth === 'function') {
                desiredWidth = desiredWidth();
            }

            if (typeof desiredWidth !== 'number') {
                console.warn('viewport agent not called with number.');
                return [false, undefined, undefined, 'width NaN'];
            }

            if (!desiredWidth || desiredWidth <= 0 || desiredWidth > 2048) {
                console.warn('viewport agent called with invalid width.');
                return [false, undefined, undefined, 'width invalid'];
            }

            // http://stackoverflow.com/a/6134070/1558430
            var adjustedScale = parseFloat(Math.round(Math.min(
                    10,  // viewport scale > 10 is not allowed.
                    ($window.width() / desiredWidth).toFixed(2)
                ) * 100) / 100).toFixed(2),
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
        viewport.scale = function (desiredWidth) {
            var analysis = viewport.determine(desiredWidth),
                metaTag = getMeta(),
                proposedMeta = '';
            if (analysis[0] === true && metaTag.length >= 1) {
                // if both tag and condition exist
                proposedMeta = analysis[3];
                if (metaTag.prop('content') !== proposedMeta) {
                    // avoid re-rendering: edit tag only if it needs to change
                    metaTag.prop('content', proposedMeta);
                    broadcast('viewportResized', desiredWidth);
                }
            } else {
                broadcast('viewportNotResized', analysis[3]);
            }
        };
    });

    app.vent.on('beforeInit', function () {
        // single call func removes args
        app.viewport.scale();
    });
    app.vent.on('finished', function () {
        // single call func removes args
        app.viewport.scale();
    });
    app.vent.on('rotate', app.viewport.scale);
}(SecondFunnel));