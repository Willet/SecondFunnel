/*global SecondFunnel, Backbone, Marionette, imagesLoaded, console, broadcast */
/**
 * @module layoutEngine
 * @property initialize
 * @property stamp
 * @property unstamp
 * @property layout
 * @property reload
 */
SecondFunnel.module("layoutEngine", function (layoutEngine, SecondFunnel) {
    // Masonry wrapper
    "use strict";

    var $document = $(document),
        $window = $(window),
        defaults = {
            'columnWidth': 255,
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

    this.on('start', function () {  // this = layoutEngine
        return this.initialize(SecondFunnel.options);
    });

    this.initialize = function (options) {
        opts = $.extend({}, defaults, options, _.get(options, 'masonry'));

        this.$el = $(opts.discoveryTarget);

        if (typeof opts.columnWidth === 'function') {
            opts.columnWidth = opts.columnWidth(this.$el);
        }

        this.$el.masonry(opts);

        broadcast('layoutEngineInitialized', this, opts);
        return this;
    };

    this.stamp = function (element) {
        broadcast('elementStamped', element);
        this.$el.masonry('stamp', element);
        return this;
    };

    this.unstamp = function (element) {
        broadcast('elementUnstamped', element);
        this.$el.masonry('unstamp', element);
        return this;
    };

    this.layout = function () {
        this.$el.masonry('layout');
        return this;
    };

    this.reload = function ($fragment) {
        this.$el.masonry('reloadItems');
        this.$el.masonry();
        return this;
    };

    /**
     * Mix of append() and insert()
     *
     * @param fragment {array}: a array of elements.
     * @param $target {jQuery}: if given, fragment is inserted after the target,
     *                          if not, fragment is appended at the bottom.
     * @returns {Deferred}
     */
    this.add = function (fragment, $target) {
        var self = this;
        return $.when(this.imagesLoaded(fragment))
            .done(function (frag) {
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
                        self.reload();
                    }
                } else if (frag.length) {
                    self.$el
                        .append(frag)
                        .masonry('appended', frag);
                }
            });
    };

    /**
     * Resets the LayoutEngine's instance so that it is empty.
     * Conventional $el.empty() doesn't work because the container height
     * is set by masonry.
     */
    this.empty = function () {
        this.$el
            .masonry('destroy')
            .html("")
            .css('position', 'relative')
            .masonry(opts);
    };

    /**
     * Enable when IR supports colour and dimensions.
     *
     * @private
     * @returns {deferred(args)}
     */
    var __imagesLoaded = function ($fragment) {
        // This function is based on the understanding that the ImageService will
        // return dimensions and/or a dominant colour; elements in the $fragment have
        // assigned widths and heights; (e.g. .css('width', '100px'))
        var self = this,
            args = _.toArray(arguments).slice(1),
            toLoad = $fragment.children('img').length,
            $badImages = $(),
            deferred = new $.Deferred();
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
                    self.reload();

                    deferred.resolve(args);
                }
            };
            img.onload = function () {
                self.src = img.src;
                onImage();
            };

            img.onerror = function () {
                broadcast('tileRemoved', self);
                $badImages = $badImages.add($(self).parents(opts.itemSelector));
                onImage();
            };
        });
        return deferred.promise();
    };

    /**
     * @deprecated: Use until ImageService is reading/returns dominant colour
     * Calls the broken handler to remove broken images as they appear;
     * When all images are loaded, resolves the promise returned
     *
     * @param tiles
     * @returns {promise(args)}
     */
    this.imagesLoaded = function (tiles) {
        var deferred = new $.Deferred();

        // "Triggered after all images have been either loaded or confirmed broken."
        // huh? imagesLoaded uses $.Deferred?
        $(tiles).children('img').imagesLoaded().always(function (instance) {
            var $badImages = $(),
                goodTiles = [];

            if (instance.hasAnyBroken) {
                // Iterate through the images and collect the bad images.
                _.each(instance.images, function (image) {
                    var $img = $(image.img),  // image.img is a dom element
                        $elem;

                    if (image.isLoaded) {
                        $elem = $img.parents(opts.itemSelector);
                        if ($elem && $elem[0]) {
                            goodTiles.push($elem[0]);
                        }
                    } else {
                        console.warn('image ' + $img.attr('src') + ' is dead');
                        $badImages.add($img);
                    }
                });
                // Batch removal of bad elements
                $badImages.remove();

                deferred.resolve(goodTiles);
            } else {
                // no images broken
                deferred.resolve(tiles);
            }
        });

        return deferred.promise();
    };
});
