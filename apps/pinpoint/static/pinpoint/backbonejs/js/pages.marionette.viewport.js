SecondFunnel.vent.on('rotate', function (desiredWidth) {
    // attempt to lock the viewport to appear as wide as desiredWidth
    // by scaling the entire viewport.
    // the meta viewport tag is NOT standard, and does NOT work on all devices.
    // (this concerns mostly IE10 on Windows Phone)
    var enabled = SecondFunnel.option('lockWidth');

    if (typeof enabled === 'function') {
        enabled = enabled();
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
        adjustedScale = $(window).width() / desiredWidth;

    viewportMeta.prop('content',
        "user-scalable=no," +
        "width=" + desiredWidth + "," +
        "initial-scale=" + adjustedScale + "," +
        "minimum-scale=" + adjustedScale + "," +
        "maximum-scale=" + adjustedScale
    );

    broadcast('viewportResized', desiredWidth);
});