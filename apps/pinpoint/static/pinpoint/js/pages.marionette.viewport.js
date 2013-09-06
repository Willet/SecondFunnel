(function (app) {
    var scale = function (desiredWidth) {
        // attempt to lock the viewport to appear as wide as desiredWidth
        // by scaling the entire viewport.
        // the meta viewport tag is NOT standard, and does NOT work on all devices.
        // (this concerns mostly IE10 on Windows Phone)
        var $window = $(window),
            $document = $(document),
            enabled = app.option('lockWidth', function () {
            return $.browser.mobile;
        });

        desiredWidth = desiredWidth || app.option('desiredWidth') || function () {
            // 767 is the last width to show as mobile.
            // screen.height is screen.width prior to rotation.
            // 48: android UI bar overestimation
            var w = Math.min(screen.width + 48, screen.height + 48, $window.width(), 767);
            return w;
        };

        if (typeof enabled === 'function') {
            enabled = enabled();
        }

        if (typeof desiredWidth === 'function') {
            desiredWidth = desiredWidth();
        }

        if (enabled !== true) {
            console.warn('viewport agent disabled.');
            return;
        }

        if (!window.devicePixelRatio || window.devicePixelRatio <= 1) {
            console.warn('viewport agent called on device with unsupported ppi.');
            return;
        }

        if (!desiredWidth || desiredWidth <= 0 || desiredWidth > 2048) {
            console.warn('viewport agent called with invalid width.');
            return;
        }

        var getMeta = function () {
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
            },
            viewportMeta = getMeta(),
            adjustedScale = $window.width() / desiredWidth;

        viewportMeta.prop('content',
            "user-scalable=no," +
            "width=" + desiredWidth + "," +
            "initial-scale=" + adjustedScale + "," +
            "minimum-scale=" + adjustedScale + "," +
            "maximum-scale=" + adjustedScale
        );

        broadcast('viewportResized', desiredWidth);
    };

    app.vent.on('beforeInit', function () {
        // single call func removes args
        scale();
    });
    app.vent.on('finished', function () {
        // single call func removes args
        scale();
    });
    app.vent.on('rotate', scale);
}(SecondFunnel));