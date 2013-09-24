/*global SecondFunnel, Backbone, Marionette, console, broadcast */
SecondFunnel.module("layoutEngine", function (layoutEngine, SecondFunnel) {
    // Masonry wrapper
    "use strict";

    var $document = $(document),
        $window = $(window),
        defaults = {
            'columnWidth': SecondFunnel.option('columnWidth', $.noop)() || 255,
            'isAnimated': !SecondFunnel.support.mobile(),
            'transitionDuration': '0.4s',
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
        },
        opts;  // last-used options (used by clear())

    layoutEngine.on('start', function () {  // this = layoutEngine
        opts = $.extend({}, defaults, opts, _.get(opts, 'masonry'));

        this.$el = $(SecondFunnel.option('discoveryTarget'));
        this.$el.masonry(opts);

        broadcast('layoutEngineInitialized', layoutEngine, opts);
        return layoutEngine;
    });

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

    /**
     * Mix of append() and insert()
     *
     * @param $fragment
     * @param $target: if given, fragment is inserted after the target,
     *                 if not, fragment is appended at the bottom.
     * @returns {*}
     */
    layoutEngine.add = function ($fragment, $target) {
        return $.when(layoutEngine.imagesLoaded($fragment))
            .always(function () {
                if ($target && $target.length) {
                    var initialBottom = $target.position().top +
                        $target.height();
                    if ($fragment.length) {
                        // Find a target that is low enough on the screen to insert after
                        while ($target.position().top <= initialBottom &&
                               $target.next().length > 0) {
                            $target = $target.next();
                        }
                        $fragment.insertAfter($target);
                        layoutEngine.reload();
                    }
                } else if ($fragment.length) {
                    layoutEngine.$el
                        .append($fragment)
                        .masonry('appended', $fragment);
                }
            });
    };

    /**
     * Resets the LayoutEngine's instance so that it is empty.
     * Conventional $el.empty() doesn't work because the container height
     * is set by masonry.
     */
    layoutEngine.empty = function () {
        layoutEngine.$el
            .masonry('destroy')
            .html("")
            .css('position', 'relative')
            .masonry(opts);
    };

    /**
     * @private (enable when IR supports colour and dimensions)
     * TODO: use deferred
     */
    var __imagesLoaded = function (callback, $fragment) {
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
                $badImages = $badImages.add($(self).parents(layoutEngine.itemSelector));
                onImage();
            };
        });
        return callback.apply(layoutEngine, args);
    };

    layoutEngine.imagesLoaded = function ($fragment) {
        // @deprecated: Use until ImageService is reading/returns dominant colour
        // Calls the broken handler to remove broken images as they appear;
        // when all images are loaded, calls the appropriate layout function
        var args = _.toArray(arguments).slice(2),
            $badImages = $(),
            imgLoad = imagesLoaded($fragment.children('img')),
            deferred = new $.Deferred();

        imgLoad.on('always', function (imgLoad) {
            // When all images are loaded and/or error'd remove the broken ones, and load
            // the good ones.
            if (imgLoad.hasAnyBroken) {
                // Iterate through the images and collect the bad images.
                var $badImages = $();
                _.each(imgLoad.images, function (image) {
                    if (!image.isLoaded) {
                        var $img = $(image.img),
                            $elem = $img.parents(layoutEngine.itemSelector);
                        $fragment = $fragment.filter(function () {
                            return !$(this).is($elem);
                        });
                        $badImages = $badImages.add($elem);
                    }
                });
                // Batch removal of bad elements
                $badImages.remove();
            }

            args.unshift($fragment);
            // callback.apply(layoutEngine, args);
            // deferred.resolve.apply(deferred, args);
            deferred.resolve($fragment);
        });

        return deferred.promise();
    };
});
