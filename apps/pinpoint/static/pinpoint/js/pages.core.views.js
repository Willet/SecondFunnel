/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _, console, App */
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
        pagesScrolled = 1;

    /**
     * View responsible for the "Hero Area"
     * (e.g. Shop-the-look, featured, or just a plain div)
     *
     * @constructor
     * @type {ItemView}
     */
    this.HeroAreaView = Marionette.ItemView.extend({
        // $(...).html() defaults to the first item successfully selected
        // so featured will be used only if stl is not found.
        'model': module.Tile,
        'template': "#shopthelook_template, #featured_template, #hero_template",
        'templates': function (currentView) {
            return [
                "#<%= options.store.slug %>_<%= options.page.layout %>_template",
                "#<%= options.store.slug %>_shopthelook_template",
                "#<%= options.store.slug %>_featured_template",
                "#<%= options.store.slug %>_hero_template",
                "#shopthelook_template",
                "#featured_template",
                "#hero_template"
            ];
        },
        /**
         * @param data   normal product data, or, if omitted,
         *               the featured product.
         */
        'initialize': function (data) {
            if (!data) {
                this.model = new module.Tile(data);
            } else {
                this.model = new module.Tile(App.option('page:product', {}));
            }
        },
        'onRender': function () {
            var buttons;
            if (this.$el.length) {  // if something rendered, it was successful
                if (!(App.support.touch() || App.support.mobile()) &&
                    this.$('.social-buttons').length >= 1) {

                    buttons = new App.sharing.SocialButtons({
                        'model': this.model
                    }).render().load();
                    this.$('.social-buttons').html(buttons.$el);
                }
                App.heroArea.$el.append(this.$el);
            }
        }
    });

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
        'templates': function (currentView) {
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
            if (!this.socialButtons.$el) {
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
        },

        'onClick': function (ev) {
            var tile = this.model,
                preview;

            // Tile is a banner tile
            if (tile.get('redirect-url')) {
                window.open(tile.get('redirect-url'), '_blank');
                return;
            }

            // clicking on social buttons is not clicking on the tile.
            if (!$(ev.target).parents('.button').length) {
                preview = new module.PreviewWindow({
                    'model': tile,
                    'caller': ev.currentTarget
                });
                // App.vent.trigger("click:tile", ev, this);
            }
        },

        /**
         * Before the View is rendered. this.$el is still an empty div.
         */
        'onBeforeRender': function () {
            var maxImageSize,
                self = this,
                defaultImage = self.model.getDefaultImage(),  // obj
                normalTileWidth = App.option('columnWidth', 255),
                wideTileWidth = normalTileWidth * 2,
                fullTileWidth = normalTileWidth * 4,  // 4col (standby)
                normalImageInfo = this.model.get('defaultImage')
                    .width(normalTileWidth, true),  // undefined if not found
                wideImageInfo = this.model.get('defaultImage'),
                    /*.width(wideTileWidth, true)*/  // undefined if not found
                sizes = {
                    'normal': normalTileWidth,
                    'wide': wideTileWidth,
                    'full': fullTileWidth
                };

            // templates use this as obj.image.url
            this.model.set('image',
                this.model.get('defaultImage')/*.width(normalTileWidth, true)*/);

            // 0.5 is an arbitrary 'lets make this tile wide' factor
            if (Math.random() > App.option('imageTileWide', 0.5) &&
                // "only if it is not a banner url"
                wideImageInfo && !self.model.get('redirect-url')) {
                // this.model.getDefaultImage().url = this.model.get('defaultImage').wide.url;
                this.$el.addClass('wide');
                this.model.set({'image': wideImageInfo});
            }

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
            if (model.get('dominant-colour')) {
                hexColor = model.get('dominant-colour');
                rgbaColor = App.utils.hex2rgba(hexColor, 0.5);

                $tileImg.css({
                    'background-color': rgbaColor
                });
            }

            // this is the 'image 404' event
            if ($tileImg && $tileImg.length >= 1) {
                $tileImg[0].onerror = function () {
                    self.close();
                };
            }

            $tileImg.load(allocateTile);

            if (App.support.touch()) {
                this.tapIndicator.show(new module.TapIndicator());
            }
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
     * Manages the HTML/View of ALL the tiles on the page (our discovery area)
     *
     * @class Feed
     * @constructor
     * @type {CompositeView}
     */
    this.Feed = Marionette.CollectionView.extend({
        'lastScrollTop': 0,
        'loading': false,

        'collection': null,

        /**
         * @param {Model} item
         * @return {TileView}
         */
        'getItemView': function (item) {
            //TODO: hack for newegg, provide better way
            if (item.get('type') === 'video') {
                item.set('type', item.get('template'));
            }

            return App.utils.findClass('TileView',
                App.core.getModifiedTemplateName(
                    item.get('type') || item.get('template')),
                module.TileView);
        },

        // buildItemView (marionette.collectionview.md#collectionviews-builditemview)

        'initialize': function (opts) {
            var self = this,
                options = opts.options;  // someone came up with this idea

            _.bindAll(this, 'pageScroll', 'toggleLoading');

            this.collection = new App.core.TileCollection();
            /* this.categories = new module.CategorySelector(  // v-- options.categories is deprecated
                App.option("page:categories") ||
                App.option("categories") || []
            ); */

            this.attachListeners();

            // If the collection has initial values, lay them out
            if (options.initialResults && options.initialResults.length > 0) {
                console.log('laying out initial results');

                // unique-by-id the list of initial results.
                options.initialResults = _.uniq(options.initialResults,
                    false, function (result) { return result['tile-id']; });

                // unique-by-original-url youtube videos
                options.initialResults = _.uniq(options.initialResults,
                    false, function (result) { return result['original-url']; });

                this.collection.add(options.initialResults);
                App.intentRank.addResultsShown(options.initialResults);
            }

            // ... then fetch more products from IR
            this.getTiles();

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
                if (window.addEventListener) {  // IE 8
                    window.addEventListener("orientationchange",
                        globals.orientationChangeHandler, false);
                }
            }(App._globals));

            $window
                .scrollStopped(function () {
                    // deal with tap indicator fade in/outs
                    App.vent.trigger('scrollStopped', self);
                });

            // Vent Listeners
            App.vent.on("click:tile", this.updateContentStream, this);
            // App.vent.on('change:campaign', this.categoryChanged, this);

            App.vent.on("finished", _.once(function () {
                // the first batch of results need to layout themselves
                App.layoutEngine.layout(self);
            }));
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
            // App.vent.off('change:campaign');
            App.vent.off("finished");

            App.vent.off('windowResize');  // in layoutEngine
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
            self.toggleLoading(true);
            return this.collection
                .fetch()
                .always(function (data) {
                    self.toggleLoading(false);

                    // see if we need to get more
                    // this setTimeout forces IE 8 to clear the stack
                    setTimeout(function () {
                        self.pageScroll();
                    }, 100);
                });
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
            // Changes the category (campaign) by refreshing IntentRank, clearing
            // the Layout Engine and collecting new tiles.
            var self = this;
            if (this.loading) {
                setTimeout(function () {
                    self.categoryChanged(ev, category);
                }, 100);
            } else {
                App.intentRank.changeCategory(category.model.get('id'));
                App.tracker.changeCampaign(category.model.get('id'));
                App.layoutEngine.empty(this);
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
            return this;
        },

        'pageScroll': function () {
            var pageHeight = $window.innerHeight(),
                windowTop = $window.scrollTop(),
                pageBottomPos = pageHeight + windowTop,
                documentBottomPos = $document.height(),
                viewportHeights = pageHeight * (App.option('prefetchHeight', 1.5));

            if (!this.loading && $('.previewContainer').length === 0 &&
                pageBottomPos >= documentBottomPos - viewportHeights) {
                // get more tiles to fill the screen.
                this.getTiles();
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
        }
    });

    /**
     * One instance of a category
     *
     * @constructor
     * @type {*}
     */
    /*this.CategoryView = Marionette.ItemView.extend({
        'events': {
            'click': function (ev) {
                ev.preventDefault();
                App.vent.trigger('change:campaign', ev, this);
            }
        },

        'initialize': function (options) {
            // Initializes the category view, expects some el to use
            this.el = options.el;
            this.$el = $(this.el);
            delete options.$el;
            this.model = new module.Category(options);
        }
    });*/

    /**
     * Computes the number of categories the page is allowed to display.
     * This CompositeView does not create an element, rather is passed
     * the element that it will use for category selection. (?)
     *
     * @constructor
     * @type {CompositeView}
     */
    /*this.CategorySelector = Marionette.CompositeView.extend({
        'itemView': module.CategoryView,

        'initialize': function (categories) {
            // Initialize a category view for each object with a
            // data-category option.
            var views = [];
            $('[data-category]').each(function () {
                var id = $(this).attr('data-category');
                if (_.findWhere(categories, {'id': Number(id)})) {
                    // Make sure category is a valid one.
                    views.push(new module.CategoryView({
                        'id': id,
                        'el': this
                    }));
                }
            });
            this.views = views;
        }
    });*/

    /**
     * Contents inside a PreviewWindow.
     * Content is displayed using a cascading level of templates, which
     * increases in specificity.
     *
     * @constructor
     * @type {ItemView}
     */
    this.PreviewContent = Marionette.ItemView.extend({
        'template': '#tile_preview_template',
        'templates': function (currentView) {
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

            console.debug('Template search tree for view %O: %O', currentView,
                templateRules);
            return templateRules;
        },
        'onBeforeRender': function () {
            // templates use this as obj.image.url
            this.model.set('image',
                    this.model.get('defaultImage').toJSON());
        },
        'onRender': function () {
            // ItemViews don't have regions - have to do it manually
            var buttons, width;
            if (!(App.support.touch() || App.support.mobile())) {
                buttons = new App.sharing.SocialButtons({model: this.model}).render().load().$el;
                this.$('.social-buttons').append(buttons);
            }
            width = Marionette.getOption(this, 'width');
            if (width) {
                this.$('.content').css('width', width + 'px');
            }

            // hide discovery, then show this window as a page.
            if (App.support.mobile()) {
                // out of scope
                $(App.option('discoveryTarget')).parent()
                    .swapWith(this.$el);
            }

            App.vent.trigger('previewRendered', this);
        },

        'initialize': function() {
            this.$el.attr({
                'id': 'preview-' + this.model.cid
            });
        },

        // Disable scrolling body when preview is shown
        'onShow': function() {
            $(document.body).addClass('no-scroll')
        },

        'close': function() {
            $(document.body).removeClass('no-scroll')
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
        'events': {
            'click .close, .mask': function () {
                // hide this, then restore discovery.
                var discoveryEl = $(App.option('discoveryTarget'));
                if (App.support.mobile()) {
                    this.$el.swapWith(discoveryEl.parent());

                    // handle results that got loaded while the discovery
                    // area has an undefined height.
                    App.layoutEngine.layout(App.discovery);
                }
                this.close();
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
            var ContentClass = App.utils.findClass('PreviewContent',
                    options.model.get('template'), module.PreviewContent),
                contentOpts = {
                    'model': options.model,
                    'caller': options.caller
                };

            this.render();
            if (!this.isClosed) {
                this.content.show(new ContentClass(contentOpts));
                if (this.content.currentView.isClosed) {
                    this.close();
                }
            }
        },

        'onMissingTemplate': function () {
            this.content.close();
            this.close();
        },

        'templateHelpers': function () {
            // return {data: $.extend({}, this.options, {template: this.template})};
        },

        'onRender': function () {
            // cannot declare display:table in marionette class.
            this.$el.css({'display': "table"});

            $('body').append(this.$el);
        }
    });

    /**
     * Visual overlay on a TileView that indicates it can be tapped.
     * This view is visible only on touch-enabled devices.
     *
     * @constructor
     * @type {*}
     */
    this.TapIndicator = Marionette.ItemView.extend({
        'template': "#tap_indicator_template",
        'className': 'tap_indicator',
        'initialize': function () {
            App.vent.on('scrollStopped',
                                 _.bind(this.onScrollStopped, this));
        },
        'onBeforeRender': function () {
            // http://jsperf.com/hasclass-vs-toggleclass
            // toggleClass with a boolean is 55% slower than manual checks
            if (App.support.touch()) {
                $('html').addClass('touch-enabled');
            } else {
                $('html').removeClass('touch-enabled');
            }
        },
        'onScrollStopped': function () {
            var $indicatorEl = this.$el;
            if ($indicatorEl
                    .parents(App.option('itemSelector'))
                    .hasClass('wide')) {
                if ($indicatorEl.is(':in-viewport')) {  // this one is in view.
                    $indicatorEl.cssDelay(500).cssFadeOut(600);
                }
            }
        }
    });
});
