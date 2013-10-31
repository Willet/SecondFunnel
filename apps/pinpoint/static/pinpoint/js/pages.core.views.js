/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _,
  Willet, broadcast, console, SecondFunnel */
/**
 * @module core
 */
SecondFunnel.module('core', function (module, SecondFunnel) {
    // other args: https://github.com/marionettejs/Marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document);

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
        'template': "#stl_template, #featured_template, #hero_template",
        'templates': function (currentView) {
            return [  // dictated by CtrlF fshkjr
                "#<%= options.store.slug %>_stl_template",
                "#<%= options.store.slug %>_featured_template",
                "#<%= options.store.slug %>_hero_template",
                "#stl_template",
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
                this.model = new module.Tile(SecondFunnel.option('page:product', {}));
            }
        },
        'onRender': function () {
            var buttons;
            if (this.$el.length) {  // if something rendered, it was successful
                if (!(SecondFunnel.support.touch() || SecondFunnel.support.mobile()) &&
                    this.$('.social-buttons').length >= 1) {

                    buttons = new SecondFunnel.sharing.SocialButtons({
                        'model': this.model
                    }).render().load();
                    this.$('.social-buttons').html(buttons.$el);
                }
                SecondFunnel.heroArea.$el.append(this.$el);
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
        'tagName': SecondFunnel.option('tileElement', "div"),
        'template': "#product_tile_template",
        'templates': function (currentView) {
            var templateRules = [  // dictated by CtrlF fshkjr
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

            if (!SecondFunnel.support.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                templateRules = _.reject(templateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }

            return templateRules;
        },
        'className': SecondFunnel.option('itemSelector', '').substring(1),

        'events': {
            'click': "onClick",
            'mouseenter': "onHover",
            'mouseleave': "onHover"
        },

        'regions': _.extend({}, {  // if ItemView, the key is 'ui': /docs/marionette.itemview.md#organizing-ui-elements
            'socialButtons': '.social-buttons',
            'tapIndicator': '.tap-indicator-target'
        }, _.get(SecondFunnel.options, 'regions') || {}),

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
            _.each(data['content-type'].toLowerCase().split(),
                function (cName) {
                    self.className += " " + cName;
                });

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
            SecondFunnel.vent.trigger("tileHover", ev, this);
            if (!SecondFunnel.support.mobile() &&
                !SecondFunnel.support.touch() &&
                this.socialButtons && this.socialButtons.$el &&
                this.socialButtons.$el.children().length) {
                var inOrOut = (ev.type === 'mouseenter') ? 'fadeIn'
                    : 'fadeOut';
                this.socialButtons.$el[inOrOut](200);
                this.socialButtons.currentView.load();
            }
        },

        'onClick': function (ev) {
            var tile = this.model,
                preview;

            // clicking on social buttons is not clicking on the tile.
            if (!$(ev.target).parents('.button').length) {
                preview = new module.PreviewWindow({
                    'model': tile,
                    'caller': ev.currentTarget
                });
                SecondFunnel.vent.trigger("click:tile", ev, this);
            }
        },

        /**
         * Before the View is rendered. this.$el is still an empty div.
         */
        'onBeforeRender': function () {
            var maxImageSize,
                self = this,
                defaultImage = self.model.getDefaultImage(),  // obj
                normalTileWidth = SecondFunnel.option('columnWidth', 255),
                wideTileWidth = normalTileWidth * 2,
                fullTileWidth = normalTileWidth * 4,  // 4col (standby)
                sizes = {
                    'normal': normalTileWidth,
                    'wide': wideTileWidth,
                    'full': fullTileWidth
                };

            // templates use this as obj.image.url
            this.model.set('image',
                this.model.get('defaultImage').width(normalTileWidth, true));

            // 0.500 is an arbitrary 'lets make this tile wide' factor
            if (Math.random() > 0.500) {
                // this.model.getDefaultImage().url = this.model.get('defaultImage').wide.url;
                this.$el.addClass('wide');
                this.model.set({
                    'image': this.model.get('defaultImage')
                                 .width(wideTileWidth, true)
                });
            }

            // Listen for the image being removed from the DOM, if it is, remove
            // the View/Model to free memory
            this.$el.on('remove', function (ev) {
                if (ev.target === self.el) {
                    console.debug('Model being destroyed', this);
                    self.model.destroy();
                }
            });
        },

        'onMissingTemplate': function () {
            // If a tile fails to load, destroy the model
            // and subsequently this tile.
            console.debug('Missing template - this view is closing.', this);
            this.model.destroy();
            this.close();
        },

        /**
         * onRender occurs between beforeRender and show.
         */
        'onRender': function () {
            var self = this,
                model = this.model,
                tileImage = model.get('image'),  // assigned by onBeforeRender
                $tileImg = this.$('img.focus'),
                hexColor,
                rgbaColor;

            // set dominant colour on tile, and set the height of the tile
            // so it looks like it is all-ready
            if (model.get('dominant-colour')) {
                hexColor = model.get('dominant-colour');
                rgbaColor = SecondFunnel.utils.hex2rgba(hexColor, 0.5);

                $tileImg.css({
                    'background-color': rgbaColor
                });
            }

            // resize image... later (because $el is hidden, width() gives 0)
            // TODO
            /*_.defer(function () {
                // master.jpgs have no defined size
                if (tileImage.url.indexOf('master') < 0) {
                    // aim to fill the entire tile container
                    var maxImageWidth = $tileImg.parent().width();
                    // calculate tile's scaled image height
                    $tileImg.css({
                        'width': maxImageWidth + 'px',
                        'max-width': '100%',
                        'height': maxImageWidth / tileImage.width *
                                  tileImage.height + 'px'
                    });
                }
            });*/

            // this is the 'image 404' event
            $tileImg[0].onerror = function () {
                self.close();
            };

            if (this.tapIndicator && this.socialButtons) {
                // Need to do this check in case layout is closing due
                // to broken images.
                if (SecondFunnel.sharing.SocialButtons.prototype.buttonTypes.length &&
                    !(SecondFunnel.support.touch() || SecondFunnel.support.mobile())) {
                    this.socialButtons.show(new SecondFunnel.sharing.SocialButtons({model: this.model}));
                }
                if (SecondFunnel.support.touch()) {
                    this.tapIndicator.show(new module.TapIndicator());
                }
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

            if (this.model.is('youtube')) {
                this.model.set("thumbnail", 'http://i.ytimg.com/vi/' +
                                            this.model.get('original-id') +
                                            '/hqdefault.jpg');
            }
        },

        'onClick': function () {
            if (this.model.get('url')) {
                window.open(this.model.get('url'));
            }
        },

        'onPlaybackEnd': function (ev) {
            SecondFunnel.vent.trigger("videoEnded", ev, this);
        }
    });

    this.YoutubeTileView = this.VideoTileView.extend({
        'model': module.YoutubeTile,
        'template': function () {

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
                    'controls': SecondFunnel.support.mobile()
                },
                'events': {
                    'onReady': $.noop,
                    'onStateChange': function (newState) {
                        SecondFunnel.tracker.videoStateChange(
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
            return SecondFunnel.utils.findClass('TileView',
                    item.get('template') || item.get('type'), module.TileView);
        },

        // buildItemView (marionette.collectionview.md#collectionviews-builditemview)

        'initialize': function (options) {
            var self = this;

            _.bindAll(this, 'pageScroll', 'toggleLoading');

            this.collection = new SecondFunnel.core.TileCollection();
            this.categories = new module.CategorySelector(  // v-- options.categories is deprecated
                SecondFunnel.option("page:categories") ||
                SecondFunnel.option("categories") || []
            );

            this.attachListeners();

            // If the collection has initial values, lay them out
            if (options.initialResults && options.initialResults.length > 0) {
                console.log('laying out initial results');
                this.collection.add(options.initialResults);
            }

            // ... then fetch more products from IR
            return this.getTiles();
        },

        'attachListeners': function () {
            var self = this;

            SecondFunnel.layoutEngine.initialize(this, SecondFunnel.options);

            $window
                .scroll(_.throttle(this.pageScroll, 500))
                .resize(_.throttle(function () {
                    // did you know any DOM element without resize events
                    // can still react to potential resizes by having its
                    // own .bind('resize', function () {})?
                    $('.resizable', document).trigger('resize');

                    // automatically redraw tiles already added to the page
                    // to fit the current page mode if it changes
                    // (mobile/desktop)
                    // SecondFunnel.discovery.render();

                    SecondFunnel.vent.trigger('windowResize');
                }, 1000))
                .scrollStopped(function () {
                    // deal with tap indicator fade in/outs
                    SecondFunnel.vent.trigger('scrollStopped', self);
                });

            // serve orientation change event via vent
            if (window.addEventListener) {  // IE 8
                window.addEventListener("orientationchange", function () {
                    SecondFunnel.vent.trigger("rotate");
                }, false);
            }

            // Vent Listeners
            SecondFunnel.vent.on("click:tile", this.updateContentStream,
                this);
            SecondFunnel.vent.on('change:campaign', this.categoryChanged, this);
            return this;
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
                return (new $.Deferred()).promise();
            }
            self.toggleLoading(true);
            return this.collection
                .fetch()
                .always(function (data) {
                    self.toggleLoading(false);

                    // see if we need to get more
                    self.pageScroll();
                });
        },

        'onAfterItemAdded': function (itemView) {
            var self = this;
            SecondFunnel.layoutEngine.layout(self);
        },

        'appendHtml': function (collectionView, itemView, index) {
            // default functionality:
            // collectionView.$el.append(itemView.el);
            SecondFunnel.layoutEngine.add(collectionView, [itemView.el]);
        },

        'updateContentStream': function (ev, tile) {
            // Loads in related content below the specified tile
            var id = tile.model.get('tile-id');
            if (id === null) {
                console.warn('updateContentStream got a null ID. ' +
                    'I don\'t think it is supposed to happen.');
                return this;
            }
            return this.getTiles({
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
                SecondFunnel.intentRank.changeCategory(category.model.get('id'));
                SecondFunnel.tracker.changeCampaign(category.model.get('id'));
                SecondFunnel.layoutEngine.empty(this);
                return this.getTiles();
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
                pageBottomPos = pageHeight + $window.scrollTop(),
                documentBottomPos = $document.height(),
                viewportHeights = pageHeight * (SecondFunnel.option('prefetchHeight', 1.5));

            if (!this.loading && $('html').css('overflow') !== 'hidden' &&
                pageBottomPos >= documentBottomPos - viewportHeights) {
                // get more tiles to fill the screen.
                this.getTiles();
            }

            // detect scrolling detection. not used for anything yet.
            var st = $window.scrollTop();
            if (st > this.lastScrollTop) {
                broadcast('scrollDown', this);
            } else if (st < this.lastScrollTop) {
                broadcast('scrollUp', this);
            }  // if equal, broadcast nothing
            this.lastScrollTop = st;
        }
    });

    /**
     * One instance of a category
     *
     * @constructor
     * @type {*}
     */
    this.CategoryView = Marionette.ItemView.extend({
        'events': {
            'click': function (ev) {
                ev.preventDefault();
                SecondFunnel.vent.trigger('change:campaign', ev, this);
            }
        },

        'initialize': function (options) {
            // Initializes the category view, expects some el to use
            this.el = options.el;
            this.$el = $(this.el);
            delete options.$el;
            this.model = new module.Category(options);
        }
    });

    /**
     * Computes the number of categories the page is allowed to display.
     * This CompositeView does not create an element, rather is passed
     * the element that it will use for category selection. (?)
     *
     * @constructor
     * @type {CompositeView}
     */
    this.CategorySelector = Marionette.CompositeView.extend({
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
    });

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

            if (!SecondFunnel.support.mobile()) {
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
            if (!(SecondFunnel.support.touch() || SecondFunnel.support.mobile())) {
                buttons = new SecondFunnel.sharing.SocialButtons({model: this.model}).render().load().$el;
                this.$('.social-buttons').append(buttons);
            }
            width = Marionette.getOption(this, 'width');
            if (width) {
                this.$('.content').css('width', width + 'px');
            }

            // hide discovery, then show this window as a page.
            if (SecondFunnel.support.mobile()) {
                // out of scope
                $(SecondFunnel.option('discoveryTarget')).parent()
                    .swapWith(this.$el);
            }

            broadcast('previewRendered', this);
        },

        'initialize': function() {
            this.$el.attr({
                'id': 'preview-' + this.model.cid
            });
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
                var discoveryEl = $(SecondFunnel.option('discoveryTarget'));
                if (SecondFunnel.support.mobile()) {
                    this.$el.swapWith(discoveryEl.parent());

                    // handle results that got loaded while the discovery
                    // area has an undefined height.
                    SecondFunnel.layoutEngine.layout(SecondFunnel.discovery);
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
            var ContentClass = SecondFunnel.utils.findClass('PreviewContent',
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

            $('body').append(this.$el.fadeIn(SecondFunnel.option('previewAnimationDuration')));
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
            SecondFunnel.vent.on('scrollStopped',
                                 _.bind(this.onScrollStopped, this));
        },
        'onBeforeRender': function () {
            // http://jsperf.com/hasclass-vs-toggleclass
            // toggleClass with a boolean is 55% slower than manual checks
            if (SecondFunnel.support.touch()) {
                $('html').addClass('touch-enabled');
            } else {
                $('html').removeClass('touch-enabled');
            }
        },
        'onScrollStopped': function () {
            var $indicatorEl = this.$el;
            if ($indicatorEl
                    .parents(SecondFunnel.option('itemSelector'))
                    .hasClass('wide')) {
                if ($indicatorEl.is(':in-viewport')) {  // this one is in view.
                    $indicatorEl.delay(500).fadeOut(600);
                }
            }
        }
    });
});