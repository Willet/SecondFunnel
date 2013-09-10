SecondFunnel.module("layoutEngine", function (layoutEngine, SecondFunnel) {
    // Masonry wrapper
    "use strict";

    var $document = $(document),
        $window = $(window);

    layoutEngine.options = {
        'isInitLayout': true,
        'isResizeBound': true,
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
    };

    layoutEngine.initialize = function ($elem, options) {
        var mobile = SecondFunnel.support.mobile();

        layoutEngine.selector = options.discoveryItemSelector;
        _.extend(layoutEngine.options, {
            'itemSelector': options.discoveryItemSelector,
            'columnWidth': options.columnWidth(),
            'isAnimated': !mobile,
            'transitionDuration': (mobile ?
                                   options.masonryMobileAnimationDuration :
                                   options.masonryAnimationDuration) + 's'
        }, options.masonry);

        $elem.masonry(layoutEngine.options).masonry('bindResize');
        layoutEngine.$el = $elem;
        broadcast('layoutEngineInitialized', layoutEngine);
        // @temporary
        layoutEngine.imagesLoaded = layoutEngine.imagesLoadedTransitional;
    };

    layoutEngine.call = function (callback, $fragment) {
        // relays the function to be run after imagesLoaded.
        if (typeof callback !== 'string') {
            console.error("Unsupported type " +
                (typeof callback) + " passed to LayoutEngine.");
            return layoutEngine;
        }
        if (!layoutEngine[callback]) {
            console.error("LayoutEngine has no property " + callback + ".");
            return layoutEngine;
        }

        // turn name of function into function itself
        var args = _.toArray(arguments);
        args[0] = layoutEngine[callback];  // [callback, fragment, ...]

        return layoutEngine.imagesLoaded.apply(layoutEngine, args);
    };

    layoutEngine.append = function ($fragment, callback) {
        broadcast('fragmentAppended', $fragment);
        if ($fragment.length) {
            layoutEngine.$el.append($fragment).masonry('appended', $fragment);
        }
        return callback ? callback($fragment) : layoutEngine;
    };

    layoutEngine.stamp = function (element) {
        broadcast('elementStamped', element);
        layoutEngine.$el.masonry('stamp', element);
        return layoutEngine;
    };

    layoutEngine.unstamp = function (element) {
        broadcast('elementUnstamped', element);
        layoutEngine.$el.masonry('unstamp', element);
        return layoutEngine;
    };

    layoutEngine.layout = function () {
        layoutEngine.$el.masonry('layout');
        return layoutEngine;
    };

    layoutEngine.reload = function ($fragment) {
        layoutEngine.$el.masonry('reloadItems');
        layoutEngine.$el.masonry();
        return layoutEngine;
    };

    layoutEngine.insert = function ($fragment, $target, callback) {
        var initialBottom = $target.position().top + $target.height();
        if ($fragment.length) {
            // Find a target that is low enough on the screen to insert after
            while ($target.position().top <= initialBottom &&
                   $target.next().length > 0) {
                $target = $target.next();
            }
            $fragment.insertAfter($target);
            layoutEngine.reload();
        }
        return callback ? callback($fragment) : layoutEngine;
    };

    layoutEngine.clear = function () {
        // Resets the LayoutEngine's instance so that it is empty
        layoutEngine.$el
            .masonry('destroy')
            .html("")
            .css('position', 'relative')
            .masonry(layoutEngine.options);
    };

    layoutEngine.imagesLoaded = function (callback, $fragment) {
        // This function is based on the understanding that the ImageService will
        // return dimensions and/or a dominant colour; elements in the $fragment have
        // assigned widths and heights; (e.g. .css('width', '100px'))
        var args = _.toArray(arguments).slice(1),
            toLoad = $fragment.children('img').length,
            $badImages = $();
        // We set the background image of the tile image as the dominant colour/loading;
        // when the image is loaded, we replace the src.
        $fragment.children('img').each(function () {
            // Create a dummy image to load the image
            var img = new Image(),
                self = this,
                onImage;
            img.src = $(this).attr('src');
            // Clear the src attribute so it doesn't load there
            $(this).attr('src', '');

            // Now apply handlers
            onImage = function () {
                // Function to check on each image load/error
                --toLoad;
                if ($badImages.length !== 0 && toLoad === 0) {
                    // If broken images exist, remove them and
                    // reload the layout.
                    $badImages.remove();
                    layoutEngine.reload();
                }
            };
            img.onload = function () {
                self.src = img.src;
                onImage();
            };

            img.onerror = function () {
                broadcast('tileRemoved', self);
                $badImages = $badImages.add($(self).parents(layoutEngine.selector));
                onImage();
            };
        });
        return callback.apply(layoutEngine, args);
    };

    layoutEngine.imagesLoadedTransitional = function (callback, $fragment) {
        // @deprecated: Use until ImageService is reading/returns dominant colour
        // Calls the broken handler to remove broken images as they appear;
        // when all images are loaded, calls the appropriate layout function
        var args = _.toArray(arguments).slice(2),
            $badImages = $(),
            imgLoad = imagesLoaded($fragment.children('img'));
        imgLoad.on('always', function (imgLoad) {
            // When all images are loaded and/or error'd remove the broken ones, and load
            // the good ones.
            if (imgLoad.hasAnyBroken) {
                // Iterate through the images and collect the bad images.
                var $badImages = $();
                _.each(imgLoad.images, function (image) {
                    if (!image.isLoaded) {
                        var $img = $(image.img),
                            $elem = $img.parents(layoutEngine.selector);
                        $fragment = $fragment.filter(function () {
                            return !$(this).is($elem);
                        });
                        $badImages = $badImages.add($elem);
                    }
                });
                // Batch removal of bad elements
                $badImages.remove();
            }

            // Trigger tracking event and call the callback
            // Uncomment the below if we want to track impressions
            // Will need to add appropriate category, etc.
//            SecondFunnel.vent.trigger('tracking:trackEvent', {
//                'category': '',
//                'action': '',
//                'label': '',
//                'nonInteraction': true
//            });
            args.unshift($fragment);
            callback.apply(layoutEngine, args);
        });
        return layoutEngine;
    };
});
