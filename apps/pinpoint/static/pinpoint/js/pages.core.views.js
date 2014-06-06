/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _, console, App, parseFloat */
/**
 * @module core
 */
App.module('core', function (module, App) {
    // other args: https://github.com/marionettejs/Marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document),
        // specifically, pages scrolled downwards; pagesScrolled defaults
        // to 1 because the user always sees the first page.
        pagesScrolled = 1,
        everScrolled = false;

    /**
     * View for showing a Tile (or its extensions).
     * This Layout contains socialButtons and tapIndicator regions.
     *
     * @constructor
     * @type {Layout}
     */
    this.TileView = Marionette.Layout.extend({
        'tagName': App.option('tileElement', "div"),
        'template': "#product_tile_template",
        'templates': function () {
            var templateRules = [
                "#<%= options.store.slug %>_<%= data.source %>_<%= data.template %>_mobile_tile_template",  // gap_instagram_image_mobile_tile_template
                "#<%= data.source %>_<%= data.template %>_mobile_tile_template",                            // instagram_image_mobile_tile_template
                "#<%= options.store.slug %>_<%= data.template %>_mobile_tile_template",                     // gap_image_mobile_tile_template
                "#<%= data.template %>_mobile_tile_template",                                               // image_mobile_tile_template

                "#<%= options.store.slug %>_<%= data.source %>_<%= data.template %>_tile_template",         // gap_instagram_image_tile_template
                "#<%= data.source %>_<%= data.template %>_tile_template",                                   // instagram_image_tile_template
                "#<%= options.store.slug %>_<%= data.template %>_tile_template",                            // gap_image_tile_template
                "#<%= data.template %>_tile_template",                                                      // image_tile_template

                "#product_mobile_tile_template",                                                            // fallback
                "#product_tile_template"                                                                    // fallback
            ];

            if (!App.support.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                templateRules = _.reject(templateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }

            return templateRules;
        },
        'className': App.option('itemSelector', '').substring(1),

        'events': {
            'click': "onClick",
            'mouseenter': "onHover",
            'mouseleave': "onHover"
        },

        'regions': _.extend({}, {  // if ItemView, the key is 'ui': /docs/marionette.itemview.md#organizing-ui-elements
            'socialButtons': '.social-buttons',
            'tapIndicator': '.tap-indicator-target'
        }, _.get(App.options, 'regions') || {}),

        /**
         * Creates the TileView using the options.
         * Subclasses should not override this method, rather provide an
         * 'onInitialize' function.
         *
         * @param options {Tile}   Required. Passing in a Tile initializes the
         *                         TileView.
         */
        'initialize': function (options) {
            var data = options.model.attributes,
                self = this;

            // expose tile "types" as classes on the dom
            if (data.type) {
                _.each(data.type.toLowerCase().split(),
                    function (cName) {
                        self.className += " " + cName;
                    });
            }

            if (data.template) {
                self.className += " " + data.template;
            }

            // expose model reference in form of id
            this.$el.attr({
                'class': this.className,
                'id': this.model.cid
            });

            // do some kind of magic such that these methods are always called
            // with its context being this object.
            _.bindAll(this, 'close', 'modelChanged');

            // If the tile model is changed, re-render the tile
            this.listenTo(this.model, 'changed', this.modelChanged);

            // If the tile model is removed, remove the DOM element
            this.listenTo(this.model, 'destroy', this.close);
            // Call onInitialize if it exists
            this.triggerMethod('initialize');
        },

        'modelChanged': function (model, value) {
            this.render();
        },

        'onHover': function (ev) {
            // Trigger tile hover event with event and tile
            App.vent.trigger("tileHover", ev, this);
            if (App.support.mobile() || App.support.touch()) {
                return this;  // don't need buttons here
            }

            // load buttons for this tile only if it hasn't already been loaded
            if (!this.socialButtons.$el && App.sharing) {
                this.socialButtons.show(new App.sharing.SocialButtons({
                    model: this.model
                }));
            }

            // show/hide buttons only if there are buttons
            if (this.socialButtons && this.socialButtons.$el &&
                this.socialButtons.$el.children().length) {
                var inOrOut = (ev.type === 'mouseenter')? 'cssFadeIn': 'cssFadeOut';
                this.socialButtons.currentView.load();
                this.socialButtons.$el[inOrOut](200);
            }
            return this;
        },

        'onClick': function (ev) {
            var tile = this.model, sku, url;

            if (App.option('openTileInPopup', false)) {
                if (tile.get('template') === 'product') {
                    url = tile.get('url');
                } else if (tile.get('tagged-products') &&
                           tile.get('tagged-products').length) {
                    url = tile.get('tagged-products')[0].url;
                }
                if (App.option('tilePopupUrl')) {
                    // override for ad units whose tiles point to our pages
                    url = App.option('tilePopupUrl');
                }
                if (url && url.length) {
                    sku = tile.get('sku');
                    if (sku) {
                        url += '/sku/' + sku;
                    }
                    window.open(url, '_blank');
                }
                return;
            }

            // Tile is a banner tile
            if (tile.get('redirect-url') &&
                !(App.option('disableBannerRedirectOnMobile') &&
                    App.support.mobile())) {
                window.open(tile.get('redirect-url'), '_blank');
                return;
            }

            // clicking on social buttons is not clicking on the tile.
            if (!$(ev.target).parents('.button').length) {
                App.router.navigate(String(tile.get('tile-id')), {
                    trigger: true
                });
            }
        },

        /**
         * Before the View is rendered. this.$el is still an empty div.
         */
        'onBeforeRender': function () {
            var columns, wideable, showWide, idealWidth, imageInfo,
                self = this,
                normalTileWidth = App.layoutEngine.width(),
                // TODO: Make the configurable; perhaps a page property?
                widable_templates = {
                    'image': true,
                    'youtube': true,
                    'banner': true
                }, columnDetails = {
                    '1': '',
                    '2': 'wide',
                    '3': 'three-col',
                    '4': 'full'
                };

            // templates use this as obj.image.url
            this.model.set('image', this.model.get('defaultImage'));

            wideable = widable_templates[this.model.get('template')];
            showWide = (Math.random() > App.option('imageTileWide', 0.5));

            if (_.isNumber(self.model.get('colspan'))) {
                columns = self.model.get('colspan');
            } else if (wideable && showWide) {
                columns = 2;
            } else {
                columns = 1;
            }

            if (App.support.mobile()) { // maximum of 2 columns
                if (columns <= 2) {
                    columns = 1;
                } else {
                    columns = 2;
                }
            }

            while(0 <= columns) {
                idealWidth = normalTileWidth * columns;
                imageInfo = this.model.get('defaultImage').width(idealWidth, true);
                if (imageInfo) {
                    break;
                }
                columns--;
            }

            this.model.set({'image': imageInfo});
            this.$el.addClass(columnDetails[columns]);

            // Listen for the image being removed from the DOM, if it is, remove
            // the View/Model to free memory
            this.$el.on('remove', function (ev) {
                if (ev.target === self.el) {
                    console.warn('Model being destroyed', this);
                    self.model.destroy();
                }
            });
        },

        'onMissingTemplate': function () {
            // If a tile fails to load, destroy the model
            // and subsequently this tile.
            console.warn('Missing template - this view is closing.', this);
            this.model.destroy();
            this.close();
        },

        /**
         * onRender occurs between beforeRender and show.
         */
        'onRender': function () {
            var self = this,
                model = this.model,
                allocateTile = _.throttle(function () {
                    // after the tile's dimensions are finalised, ask
                    // masonry to handle it
                    App.layoutEngine.layout(App.discovery);
                }, 1000),
                tileImage = model.get('image'),  // assigned by onBeforeRender
                $tileImg = this.$('img.focus'),
                hexColor,
                rgbaColor;

            // set dominant colour on tile, and set the height of the tile
            // so it looks like it is all-ready
            if (model.get('dominant-color')) {
                hexColor = model.get('dominant-color');
                rgbaColor = App.utils.hex2rgba(hexColor, 0.5);

                $tileImg.css({
                    'background-color': rgbaColor
                });
            }

            // this is the 'image 404' event
            if ($tileImg && $tileImg.length >= 1) {
                $tileImg[0].onerror = function () {
                    console.warn("Image error, closing views: " + arguments);
                    self.close();
                };
            }

            if (App.sharing &&
                App.option('conditionalSocialButtons', {})[model.get('colspan')]) {
                var socialButtons = $('.socialButtons', this.$el),
                    buttons = new App.sharing.SocialButtons({
                        'model': model,
                        'buttonTypes': App.option('conditionalSocialButtons', {})[model.get('colspan')]
                    });

                socialButtons.append(buttons.render().$el);
            }

            // add view to our database
            App.vent.trigger('tracking:trackTileView', model.get('tile-id'));

            $tileImg.load(allocateTile);
        }
    });

    /**
     * Right now, there is no distinction between a tile and a product tile.
     * @type {*}
     */
    this.ProductTileView = this.TileView.extend({
        'template': "#product_tile_template",
        'model': module.Tile
    });

    this.ImageTileView = this.TileView.extend({
        'template': "#image_tile_template",
        'model': module.ImageTile
    });

    /**
     * View for showing a Tile whose attributes decide it should be rendered
     * differently from a normal tile.
     *
     * VideoTile extends from TileView, allows playing of Video files;
     * for now, we only support YT
     *
     * @constructor
     * @type {TileView}
     */
    this.VideoTileView = this.TileView.extend({
        'template': "#video_tile_template",
        'model': module.VideoTile,

        'onInitialize': function () {
            // Add here additional things to do when loading a VideoTile
            this.$el.addClass('wide');
        },

        'onClick': function () {
            if (this.model.get('url')) {
                window.open(this.model.get('url'));
            }
        },

        'onPlaybackEnd': function (ev) {
            App.vent.trigger("videoEnded", ev, this);
        }
    });

    this.YoutubeTileView = this.VideoTileView.extend({
        'model': module.YoutubeTile,
        'template': function () {
        },
        'onInitialize': function () {
            // Add here additional things to do when loading a YoutubeTile
            this.$el.addClass('wide');
            this.model.set("thumbnail", 'http://i.ytimg.com/vi/' +
                            this.model.get('original-id') +
                            '/hqdefault.jpg');
        },

        /**
         * Renders a YouTube video in the tile.
         *
         * @param ev {jQuery.Event}   JS event object
         * @returns undefined
         */
        'onClick': function (ev) {
            var thumbId = 'thumb-' + this.model.cid,
                $thumb = this.$('div.thumbnail'),
                self = this;

            if (window.YT === undefined) {
                console.warn('YT could not load. Opening link to youtube.com');
                window.open(this.model.get('original-url'));
                return;
            }

            $thumb.attr('id', thumbId).wrap('<div class="video-container" />');
            var player = new window.YT.Player(thumbId, {
                'width': $thumb.width(),
                'height': $thumb.height(),
                'videoId': this.model.attributes['original-id'] || this.model.id,
                'playerVars': {
                    'wmode': 'opaque',
                    'autoplay': 1,
                    'controls': App.support.mobile()
                },
                'events': {
                    'onReady': $.noop,
                    'onStateChange': function (newState) {
                        App.tracker.videoStateChange(
                            self.model.attributes['original-id'] || self.model.id,
                            newState
                        );
                        switch (newState) {
                        case window.YT.PlayerState.ENDED:
                            self.onPlaybackEnd();
                            break;
                        default:
                            break;
                        }
                    },
                    'onError': $.noop
                }
            });
        }
    });

    /**
     * A Generic collection of TileViews
     *
     * @constructor
     * @type {CollectionView}
     */
    this.TileCollectionView = Marionette.CollectionView.extend({
        'initialize': function (options) {
            var self = this;
            this.on('itemview:item:clicked', function (childView) {
                self.trigger('collection:item:clicked', childView);
            });
        }
    });

    /**
     * Manages the HTML/View of ALL the tiles on the page (our discovery area)
     *
     * @class Feed
     * @constructor
     * @type {TileCollectionView}
     */
    this.Feed = this.TileCollectionView.extend({
        'lastScrollTop': 0,
        'loading': false,
        'collection': null,
        'ended': false,

        // buildItemView (marionette.collectionview.md#collectionviews-builditemview)
        /**
         * Oeveride getItemView to allow different itemViews to be
         * used.
         *
         * @param {Model} item
         * @return {TileView}
         */
        'getItemView': function (item) {
            return App.utils.findClass('TileView',
                App.core.getModifiedTemplateName(
                    item.get('type') || item.get('template')),
                module.TileView);
        },


        'initialize': function (opts) {
            var self = this,
                deferred = $.Deferred(),
                options = opts.options; // someone came up with this idea

            _.bindAll(this, 'pageScroll', 'toggleLoading');

            this.collection = new App.core.TileCollection();

            this.toggleLoading(true);
            this.attachListeners();

            // If the collection has initial values, lay them out
            if (options.initialResults && $(options.initialResults).length) {
                console.debug('laying out initial results');
                // If already have array just lay out, otherwise
                // assume we have an a xmlhttprequest object
                // (saved by a prefetch in campaign_config.html)
                if ($.isArray(options.initialResults)) {
                    deferred = $.when(options.initialResults);
                } else {
                    options.initialResults.onreadystatechange = function () {
                        // XMLHttpRequest.DONE on IE 9+ and other browsers; support for IE8
                        if (this.readyState === 4 && this.status === 200) {
                            deferred.resolve(JSON.parse(this.response || this.responseText));
                        }
                    };
                }
                // When resolved, layout the results
                deferred.done(function(data) {
                    options.initialResults = data;
                    App.options.IRResultsReturned = data.length;
                    self.collection.add(data);
                    App.intentRank.addResultsShown(data);
                });
            } else { // if nothing, immediately fetch more from IR
                this.toggleLoading(false).getTiles();
            }

            // most-recent feed is the active feed
            App.discovery = this;

            return this;
        },

        'attachListeners': function () {
            var self = this;

            // loads masonry on this view
            App.layoutEngine.initialize(this, App.options);

            // unbind window.scroll and resize before init binds them again.
            (function (globals) {
                globals.scrollHandler = _.throttle(self.pageScroll, 500);
                globals.resizeHandler = _.throttle(function () {
                    $('.resizable', document).trigger('resize');
                    App.vent.trigger('windowResize');
                }, 1000);
                globals.orientationChangeHandler = function () {
                    App.vent.trigger("rotate");
                };

                $window
                    .scroll(globals.scrollHandler)
                    .resize(globals.resizeHandler);

                // serve orientation change event via vent
                $(window).on('rotate', globals.orientationChangeHandler);
            }(App._globals));

            $window.scrollStopped(function () {
                // deal with tap indicator fade in/outs
                App.vent.trigger('scrollStopped', self);
            });

            if (App.utils.isIframe()) {
                $window.scrollStopped(function () {
                    // deal with tap indicator fade in/outs
                    self.$('.tile:not(:in-viewport)').css({'visibility': 'hidden'});
                    // the rest are visible
                    self.$('.tile:in-viewport').css({'visibility': 'visible'});
                });
            }

            // Vent Listeners
            App.vent.on("click:tile", this.updateContentStream, this);
            App.vent.on('change:category', this.categoryChanged, this);

            App.vent.on("feedEnded", function () {
                console.debug("feed ended");
                App.discovery.ended = true;
            });

            App.vent.on("finished", _.once(function () {
                // the first batch of results need to layout themselves
                App.layoutEngine.layout(self);
            }));

            // Custom event listeners
            this.on('after:item:appended', this.onAfterItemAppended);

            return this;
        },

        /**
         * remove events bound in attachListeners.
         */
        'detachListeners': function () {
            (function (globals) {
                $window
                    .unbind('scroll', globals.scrollHandler)
                    .unbind('resize', globals.resizeHandler);

                if (window.removeEventListener) {
                    window.removeEventListener("orientationchange",
                        globals.orientationChangeHandler, false);
                }
            }(App._globals));

            App.vent.off("click:tile");
            App.vent.off('change:category');
            App.vent.off("finished");

            App.vent.off('windowResize');  // in layoutEngine

            // Custom event listeners
            this.off('after:item:appended', this.onAfterItemAppended);
        },

        'onClose': function () {
            return this.detachListeners();
        },

        /**
         *
         * @param options
         * @param tile {TileView}  supply a tile View to have tiles inserted
         *                         after it. (optional)
         * @returns deferred
         */
        'getTiles': function (options, tile) {
            var self = this;
            if (this.loading) {
                // do nothing
                return (new $.Deferred()).promise();
            }

            var xhr = this.toggleLoading(true)
                .collection
                .fetch();

            xhr.done(function (tileInfo) {
                // feed ended / IR busted
                if (tileInfo && tileInfo.length === 0) {
                    self.toggleLoading(false);
                    App.vent.trigger("feedEnded", this);
                }
            });

            return xhr;
        },

        'render': _.throttle(function () {
            // limit how many times the feed can re-render.
            Marionette.CollectionView.prototype.render.apply(this, arguments);
        }, 500),

        'appendHtml': function (collectionView, itemView, index) {
            // default functionality:
            // collectionView.$el.append(itemView.el);
            App.layoutEngine.add(collectionView, [itemView.el]);
        },

        /**
         * Called when new content has been appended to the collectionView via
         * the layoutEngine.  Toggles loading to false, and calls pageScroll.
         *
         * @returns this
         */
        'onAfterItemAppended': function (view, el) {
            var self = this;

            setTimeout(function () {
                self
                    .toggleLoading(false)
                    .pageScroll();
            }, 500);

            return this;
        },

        /**
         * @return undefined
         */
        'updateContentStream': function (ev, tile) {
            // Loads in related content below the specified tile
            var id = tile.model.get('tile-id');
            if (id === null) {
                console.warn('updateContentStream got a null ID. ' +
                    'I don\'t think it is supposed to happen.');
            }
            this.getTiles({
                'type': "content",
                'id': id
            }, tile);
        },

        'categoryChanged': function (ev, category) {
            // Changes the category by refreshing IntentRank, clearing
            // the Layout Engine and collecting new tiles.
            var self = this;
            App.tracker.changeCategory(category);
            if (this.loading) {
                console.debug("changing category on edge");
                this.on('loadingFinished', _.once(function () {
                    App.layoutEngine.empty(self);
                    self.ended = false;
                    self.getTiles();
                }));
            } else {
                App.layoutEngine.empty(this);
                this.ended = false;
                this.getTiles();
            }

            return this;
        },

        'toggleLoading': function (bool) {
            if (typeof bool === 'boolean') {
                this.loading = bool;
            } else {
                this.loading = !this.loading;
            }

            var loadingIndicator = this.$el.parents('.container')
                .find('.loading:last');
            if (this.loading) {
                loadingIndicator.show();
            } else {
                loadingIndicator.hide();
                this.trigger('loadingFinished');
            }

            return this;
        },

        'pageScroll': function () {
            var children = this.$el.children(),
                pageHeight = $window.innerHeight(),
                windowTop = $window.scrollTop(),
                pageBottomPos = pageHeight + windowTop,
                documentBottomPos = $document.height(),
                viewportHeights = pageHeight * (App.option('prefetchHeight', 2.5));

            if (this.ended) {
                return this;
            }

            if (!this.loading && (children.length === 0 || !App.previewArea.currentView) &&
                    pageBottomPos >= documentBottomPos - viewportHeights) {
                // get more tiles to fill the screen.
                this.getTiles();
            }

            // Did the user scroll ever?
            if ($window.scrollTop() > 0) {
                // only log this event once per user
                App.vent.trigger('tracking:trackEvent', {
                    'category': 'visit',
                    'action': 'scroll'
                });
            }

            // "did user scroll down more than a page?"
            if ((windowTop / pageHeight) > pagesScrolled) {
                App.vent.trigger('tracking:trackEvent', {
                    'category': 'visit',
                    'action': 'scroll',
                    'label': pagesScrolled  // reports 1 if 1 page *scrolled*
                });

                pagesScrolled++;  // user scrolled down once more
            }

            // detect scrolling detection. not used for anything yet.
            var st = $window.scrollTop();
            if (st > this.lastScrollTop) {
                App.vent.trigger('scrollDown', this);
            } else if (st < this.lastScrollTop) {
                App.vent.trigger('scrollUp', this);
            }  // if equal, trigger nothing
            this.lastScrollTop = st;

            return this;
        }
    });


    this.ProductInfoView = Marionette.ItemView.extend({
        'initialize': function (options) {
            if (!options.infoItem) {
                throw new Error('infoItem is a required property');
            }

            this.options = options;
        },

        'getTemplate': function () {
            return '#product_' + this.options.infoItem + '_template';
        }
    });

    this.ExpandedContent = Marionette.Layout.extend({
        'regions': {
            price: '.price',
            title: '.title',
            buy: '.buy',
            description: '.description',
            galleryMainImage: '.gallery-main-image'
        },

        'onBeforeRender': function () {
            // Need to get an appropriate sized image
            var image = $.extend(true, {},
                this.model.get('defaultImage').attributes);
            image = new App.core.Image(image);

            if (App.support.mobile()) {
                image.url = image.height($window.height());
            } else {
                image = image.height(App.utils.getViewportSized(true), true);
            }

            if (this.model.get('tagged-products') && this.model.get('tagged-products').length > 1) {
                this.model.set('tagged-products', _.sortBy(this.model.get('tagged-products'), function (obj) {
                    return -1 * parseFloat((obj.price || '$0').substr(1), 10);
                }));
            }

            // templates use this as obj.image.url
            this.model.set('image', image);
        },
        'initialize': function() {
            this.$el.attr({
                'id': 'preview-' + this.model.cid
            });
        },
        'close': function () {
            /* See NOTE in onShow */
            if (!App.support.isAnAndroid()) {
                $(document.body).removeClass('no-scroll');
            }

            App.options.galleryIndex = 0;
        },

        'renderSubregions': function (product) {
            _.keys(this.regions).forEach(function (key) {
                this[key].show(new App.core.ProductInfoView({
                    model: product,
                    infoItem: key
                }));
            }, this);

            // TODO: turn gallery into a view
            $('.gallery', this.$el).empty();
            App.utils.runWidgets(this);

            this.resizeContainer();
        },

        'resizeContainer': function () {
            var shrinkContainer = function (element) {
                    return function () {
                        var container = element.closest('.fullscreen'),
                            heightReduction, widthReduction, left, right;

                        if (--imageCount !== 0) {
                            return;
                        }

                        if (!(container && container.length)) {
                            // no container to shrink
                            return;
                        }

                        heightReduction = $(window).height();
                        widthReduction = container.outerWidth();
                        left = parseInt(container.css('left').split('px')[0], 10);
                        right = parseInt(container.css('right').split('px')[0], 10);

                        heightReduction -= element.outerHeight();
                        heightReduction -= $('.close', container).outerHeight();
                        heightReduction /= 2; // Split over top and bottom

                        if (heightReduction <= 0 || App.support.mobile()) {
                            heightReduction = '0'; // String because jQuery checks for falsey values
                        }

                        widthReduction -= $('.row', container).outerWidth();
                        widthReduction /= 2;

                        //Only large changes to prevent jitter
                        if (widthReduction > 15 || widthReduction < -15) {
                            left += widthReduction;
                            right += widthReduction;
                        }

                        if (left <= 0 || App.support.mobile()) {
                            left = '0';
                        }

                        if (right <= 0 || App.support.mobile()) {
                            right = '0';
                        }

                        container.css({
                            'top': heightReduction,
                            'bottom': heightReduction,
                            'left': left,
                            'right': right
                        });
                    };
                },
                imageCount;

            imageCount = $('img.main-image, img.image', this.$el).length;

            // http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
            $('img.main-image, img.image', this.$el)
                .one('load', shrinkContainer(this.$el))
                .each(function () {
                    var self = $(this);

                    if (this.complete) {
                        // Without the timeout the box may not be rendered. This lets the onShow method return
                        setTimeout(function () {
                            self.load();
                        }, 1);
                    }
                });
        }
    });

    /**
     * Contents inside a PreviewWindow.
     * Content is displayed using a cascading level of templates, which
     * increases in specificity.
     *
     * @constructor
     * @type {Layout}
     */
    this.PreviewContent = Marionette.Layout.extend({
        'template': '#tile_preview_template',
        'templates': function () {
            var templateRules = [
                // supported contexts: options, data
                '#<%= options.store.slug %>_<%= data.template %>_mobile_preview_template',
                '#<%= data.template %>_mobile_preview_template',
                '#<%= options.store.slug %>_<%= data.template %>_preview_template',
                '#<%= data.template %>_preview_template',
                '#product_mobile_preview_template',
                '#product_preview_template',
                '#tile_mobile_preview_template', // fallback
                '#tile_preview_template' // fallback
            ];

            if (!App.support.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                templateRules = _.reject(templateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }
            return templateRules;
        },
        'onRender': function () {
            // ItemViews don't have regions - have to do it manually
            var self = this,
                socialButtons = this.$('.social-buttons'),
                buttons, related;

            if (socialButtons.length >= 1) {
                buttons = new App.sharing.SocialButtons({model: this.model}).render().load().$el;
                socialButtons.append(buttons);
            }

            if (this.model.get('tagged-products') && this.model.get('tagged-products').length > 1) {
                this.$('.stl-look .stl-item').on('click', function () {
                    var $this = $(this),
                        index = $this.data('index'),
                        product = self.model.get('tagged-products')[index],
                        productModel = new App.core.Product(product),
                        container = self.$el.closest('.fullscreen');

                    $this.addClass('selected').siblings().removeClass('selected');
                    App.options['galleryIndex'] = index;

                    if (product.images.length === 1) {
                        $('.gallery', self.$el).addClass('hide');
                    } else {
                        $('.gallery', self.$el).removeClass('hide');
                    }

                    if (socialButtons.length >= 1) {
                        socialButtons.empty();
                        buttons = new App.sharing.SocialButtons({model: self.model}).render().load().$el;
                        socialButtons.append(buttons);
                    }

                    if (container && container.length) {
                        container.css({
                            top: '0',
                            bottom: '0',
                            left: '0',
                            right: '0'
                        });
                    }

                    self.renderSubregions(productModel);
                });

                // First image is always selected
                this.$('.stl-look').each(function () {
                    $(this).find('.stl-item').first().click();
                });
            }

            // hide discovery, then show this window as a page.
            if (App.support.mobile()) {
                App.discoveryArea.$el.parent().swapWith(this.$el); // out of scope
            }

            App.vent.trigger('previewRendered', this);
        },
        // Disable scrolling body when preview is shown
        'onShow': function () {
            var product;

            if (this.model.get('tagged-products') && this.model.get('tagged-products').length) {
                product = new App.core.Product(this.model.get('tagged-products')[App.option('galleryIndex', 0)]);
                this.renderSubregions(product);
            } else if (this.model.get('template', '') === 'product') {
                this.renderSubregions(this.model);
            } else  {
                this.resizeContainer();
            }

            /*
            NOTE: Previously, it was thought that adding `no-scroll`
            to android devices was OK, because no problems were observed
            on some device.

            Turns out, that was wrong.

            It seems like no-scroll prevent scrolling on *some* android
            devices, but not others.

            So, for now, only add no-scroll if the device is NOT an android.
             */
            if (!App.support.isAnAndroid()) {
                var width = Marionette.getOption(this, 'width');

                if (width) {
                    this.$('.content').css('width', width + 'px');
                } else if (App.support.mobile()) {
                    this.$el.width($window.width()); // assign width
                }
                // if it's a real preview, add no-scroll
                if (!this.$el.parents('#hero-area').length) {
                    $(document.body).addClass('no-scroll');
                }
            }
        }
    });

    /**
     * View responsible for the "Hero Area"
     * (e.g. Shop-the-look, featured, or just a plain div)
     *
     * @constructor
     * @type {Layout}
     */
    this.HeroAreaView = this.ExpandedContent.extend({
        'model': module.Tile,
        'superClass': App.core.ExpandedContent,
        'getTemplate': function () {
            // if page config contains a product, render hero area with a
            // template that supports it
            if (App.option('featured') !== undefined &&
                $('#shopthelook_template').length) {
                return "#shopthelook_template";
            }
            return "#hero_template";
        },
        /**
         * @param data   normal product data, or, if omitted,
         *               the featured product.
         */
        'initialize': function (data) {
            var self = this,
                tile = data;
            if ($.isEmptyObject(data)) {
                tile = App.option('featured');
            }
            this.model = new module.Tile(tile);

            // "super"
            this.superClass.prototype.initialize.call(this, tile);

            this.listenTo(App.vent, 'windowResize', function () {
                // self.render();
                App.heroArea.show(self);
            });
        },
        'onRender': function () {
            // ItemViews don't have regions - have to do it manually
            var self = this,
                socialButtons = this.$('.social-buttons'),
                buttons, related;

            if (socialButtons.length >= 1) {
                buttons = new App.sharing.SocialButtons({model: this.model}).render().load().$el;
                socialButtons.append(buttons);
            }

            if (this.model.get('tagged-products') && this.model.get('tagged-products').length > 1) {
                this.$('.stl-look .stl-item').on('click', function () {
                    var $this = $(this),
                        index = $this.data('index'),
                        product = self.model.get('tagged-products')[index],
                        productModel = new App.core.Product(product),
                        container = self.$el.closest('.fullscreen');

                    $this.addClass('selected').siblings().removeClass('selected');
                    App.options['galleryIndex'] = index;

                    if (product.images.length === 1) {
                        $('.gallery', self.$el).addClass('hide');
                    } else {
                        $('.gallery', self.$el).removeClass('hide');
                    }

                    if (socialButtons.length >= 1) {
                        socialButtons.empty();
                        buttons = new App.sharing.SocialButtons({model: self.model}).render().load().$el;
                        socialButtons.append(buttons);
                    }

                    if (container && container.length) {
                        container.css({
                            top: '0',
                            bottom: '0',
                            left: '0',
                            right: '0'
                        });
                    }

                    self.renderSubregions(productModel);
                });

                // First image is always selected
                this.$('.stl-look').each(function () {
                    $(this).find('.stl-item').first().click();
                });
            }
        },
        'onShow': function () {
            var product;

            if (this.model.get('tagged-products') && this.model.get('tagged-products').length) {
                product = new App.core.Product(this.model.get('tagged-products')[App.option('galleryIndex', 0)]);
                this.renderSubregions(product);
            } else if (this.model.get('template', '') === 'product') {
                this.renderSubregions(this.model);
            } else  {
                this.resizeContainer();
            }
        }
    });

    /**
     * Container view for a PreviewContent object.
     *
     * @constructor
     * @type {Layout}
     */
    this.PreviewWindow = Marionette.Layout.extend({
        'tagName': "div",
        'className': "previewContainer",
        'template': "#preview_container_template",
        'templates': function () {
            var templateRules = [
                // supported contexts: options, data
                '#<%= options.store.slug %>_<%= data.template %>_mobile_preview_container_template',
                '#<%= data.template %>_mobile_preview_container_template',
                '#<%= options.store.slug %>_<%= data.template %>_preview_container_template',
                '#<%= data.template %>_preview_container_template',
                '#product_mobile_preview_container_template',
                '#product_preview_container_template',
                '#mobile_preview_container_template', // fallback
                '#preview_container_template' // fallback
            ];

            if (!App.support.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                templateRules = _.reject(templateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }
            return templateRules;
        },
        'events': {
            'click .close, .mask': function () {
                //If we have been home then it's safe to use back()
                if (App.initialPage === '') {
                    Backbone.history.history.back();
                } else {
                    App.router.navigate('', {
                        trigger: true,
                        replace: true
                    });
                }
            }
        },

        'regions': {
            'content': '.template.target',
            'socialButtons': '.social-buttons'
        },

        /**
         * Initialize the PreviewWindow by rendering the content to
         * display in it as well.
         *
         * @param options {Object}   optional overrides.
         */
        'initialize': function (options) {
            this.options = options;
        },

        'onMissingTemplate': function () {
            this.content.close();
            this.close();
        },

        'templateHelpers': function () {
            // return {data: $.extend({}, this.options, {template: this.template})};
        },

        'onRender': function () {
            var heightMultiplier,
                self = this,
                previewLoadingScreen = $('#preview-loading');
            // cannot declare display:table in marionette class.
            heightMultiplier = App.utils.portrait() ? 1 : 2;
            this.$el.css({
                'display': "table",
                'height': App.support.mobile() ?
                    heightMultiplier * $window.height() : ""
            });

            var ContentClass,
                template = this.options.model.get('template'),
                related = this.options.model.get('tagged-products') || [],
                contentOpts = {
                    'model': this.options.model
                };

            ContentClass = App.utils.findClass('PreviewContent',
                template, module.PreviewContent);

            this.content.show(new ContentClass(contentOpts));
            previewLoadingScreen.hide();

            this.listenTo(App.vent, 'rotate', function (width) {
                // On change in orientation, we want to rerender our layout
                // this is automatically unbound on close, so we don't have to clean
                heightMultiplier = App.utils.portrait() ? 1 : 2;
                self.$el.css({
                    'height': App.support.mobile() ?
                        heightMultiplier * $window.height() : ""
                });
                self.content.show(new ContentClass(contentOpts));
            });
        },

        'onShow': function () {
            var position_window = (function (previewWindow) {
                return function () {
                    var window_middle = $window.scrollTop() + $window.height() / 2;

                    if (App.window_middle) {
                        window_middle = App.window_middle;
                    }

                    if (App.windowHeight && App.support.mobile()) {
                        previewWindow.$el.css('height', App.windowHeight);
                    }

                    previewWindow.$el.css('top', Math.max(window_middle - (previewWindow.$el.height() / 2), 0));
                };
            }(this));

            position_window();

            $('img', this.$el).on('load', function () {
                position_window();
            });
        },

        'onClose': function () {
            // hide this, then restore discovery.
            if (App.support.mobile()) {
                this.$el.swapWith(App.discoveryArea.$el.parent());
                // handle results that got loaded while the discovery
                // area has an undefined height.
                App.layoutEngine.layout(App.discovery);
            }
        }
    });

    /**
     * View for switching categories.
     *
     * @constructor
     * @type {ItemView}
     */
    this.CategoryView = Marionette.ItemView.extend({
        'tagName': "div",
        'className': 'category',
        'template': "#category_template",
        'templates': function () {
            var templateRules = [
                "#<%= options.store.slug %>_mobile_category_template",
                "#<%= options.store.slug %>_category_template",
                "#mobile_category_template",
                "#category_template"
            ];

            if (!App.support.mobile()) {
                templateRules = _.reject(templateRules, function(t) {
                    return t.indexOf('mobile') > -1;
                });
            }

            return templateRules;
        },

        'events': {
            'click': "onClick"
        },

        'onClick': function (ev) {
            this.trigger('click', this);
        }
    });

    /**
     * A collection of Categories to display.
     *
     * @constrcutor
     * @type {CollectionView}
     */
    this.CategoryCollectionView = Marionette.CollectionView.extend({
        'tagName': "div",
        'className': "category-area",
        'itemView': this.CategoryView,
        'collection': null,

        'initialize': function (options) {
            var self = this,
                home = null,
                categories = App.option('categories', []).slice(0);
            this.collection = new App.core.CategoryCollection();

            if (App.option('categoryHome', true) && categories.length) {
                // This specifies that there should be a home button, by
                // default, this is true.
                if (App.option('categoryHome').length) {
                    home = App.option('categoryHome');
                } else {
                    home = "home";
                }
                categories.unshift(home);
                this.nofilter = true;
            }

            // Initialize by adding all the categories to this view
            _.each(categories, function (category) {
                category = new App.core.Category({
                  'name': category,
                  'nofilter': (category === home)
                });
                self.collection.add(category);
            });
        },

        'onRender': function () {
            if (this.nofilter) {
                this.$el.children().eq(0).click();
            }
        },

        'onItemviewClick': function (view) {
            var $el = view.$el,
                category = view.model.get('name'),
                nofilter = view.model.get('nofilter');

            // Switch the selected category class
            $el.siblings().removeClass('selected');
            if ($el.hasClass('selected') && !nofilter) {
                // Reset intentRank by clearing the category, if we have a
                // nofilter class, click it instead.
                $el.removeClass('selected');
                if (this.nofilter) {
                    $el.siblings().eq(0).click();
                } else {
                    App.intentRank.changeCategory();
                }
            } else if (!$el.hasClass('selected')) {
                // On click, pass the new category to intentRank, if the view
                // is the nofilter view, clear.
                $el.addClass('selected');
                if (nofilter) {
                    App.intentRank.changeCategory();
                } else {
                    App.intentRank.changeCategory(category);
                }
            }
            return this;
        }
    });
});
