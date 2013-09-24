/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _,
  Willet, broadcast, console, SecondFunnel */
SecondFunnel.module('core', function (core, SecondFunnel) {
    // other args: https://github.com/marionettejs/Marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document),
        getModifiedTemplateName;

    /**
     * convenience method for accessing PAGES_INFO or TEST_*.
     *
     * To access deep options (e.g. PAGES_INFO.store.name), use the key
     * "store.name" or "store:name" (preferred).
     *
     * @param {string} name
     * @param {*} defaultValue
     * @returns {*}
     */
    SecondFunnel.option = function (name, defaultValue) {
        var opt = Marionette.getOption(SecondFunnel, name),
            keyNest = _.compact(name.split(/[:.]/)),
            keyName,
            cursor = SecondFunnel.options,
            i,
            depth;

        if (opt !== undefined && (keyNest.length === 1 && !_.isEmpty(opt))) {
            // getOption() returns a blank object when it thinks it is accessing
            // a nested option so we have to patch that up
            return opt;
        }
        // marionette sucks, so we'll do extra traversing to get stuff out of
        // our nested objects ourselves
        try {
            for (i = 0, depth = keyNest.length; i < depth; i++) {
                keyName = keyNest[i];
                cursor = cursor[keyName];
            }
            if (cursor !== undefined) {
                return cursor;
            }
        } catch (KeyError) {
            // requested traversal path does not exist. do the next line
            console.warn('Missing option: ' + name);
        }
        return defaultValue;  // ...and defaultValue defaults to undefined
    };

    Marionette.TemplateCache._exists = function (templateId) {
        // Marionette TemplateCache extension to allow checking cache for template
        // Checks if the Template exists in the cache, if not found
        // updates the cache with the template (if it exists), otherwise fail
        // returns true if exists otherwise false.
        var cached = this.templateCaches[templateId],
            cachedTemplate;

        if (cached) {
            return true;
        }

        // template exists but was not cached
        cachedTemplate = new Marionette.TemplateCache(templateId);
        try {
            cachedTemplate.load();
            // Only cache on success
            this.templateCaches[templateId] = cachedTemplate;
        } catch (err) {
            if (!(err.name && err.name === "NoTemplateError")) {
                throw err;
            }
        }
        return !!this.templateCaches[templateId];
    };

    Marionette.View.prototype.getTemplate = function () {
        // Accept an arbitrary number of template selectors instead of just one.
        // function will return in a short-circuit manner once a template is found.
        var i, templateIDs = Marionette.getOption(this, "templates"),
            template = Marionette.getOption(this, "template"),
            temp, templateExists, data;

        if (templateIDs) {
            if (typeof templateIDs === 'function') {
                // if given as a function, call it, and expect [<string> selectors]
                templateIDs = templateIDs(this);
            }

            for (i = 0; i < templateIDs.length; i++) {
                data = $.extend({},
                    Marionette.getOption(this, "model").attributes);
                data.template = getModifiedTemplateName(data.template);

                temp = _.template(templateIDs[i], {
                    'options': SecondFunnel.options,
                    'data': data
                });
                templateExists = Marionette.TemplateCache._exists(temp);

                if (templateExists) {
                    // replace this thing's desired template ID to the
                    // highest-order template found
                    template = temp;
                    break;
                }
            }
        }
        return template;
    };

    Marionette.ItemView.prototype.onMissingTemplate = function () {
        // Default on missing template event
        this.remove();
    };

    core.Tile = Backbone.Model.extend({
        'defaults': {
            // Default product tile settings, some tiles don't
            // come specifying a type or caption
            'caption': "Shop product",
            'tile-id': null,
            'content-type': "product",
            'related-products': [],
            // Awaiting ImageService for a name
            // TODO: What's the real name?
            'dominant-color': "pink"
        },

        'initialize': function (attributes, options) {
            var videoTypes = ["youtube", "video"],
                type = this.get('content-type').toLowerCase();

            // set up tile type overrides
            this.set({
                'type': this.get('template'),  // default type being its template
                'caption': SecondFunnel.utils.safeString(this.get("caption"))
            });
            if (_.contains(videoTypes, type)) {
                this.set('type', 'video');
            }
            broadcast('tileModelInitialized', this);
        },

        'sync': function () {
            return false;  // forces ajax PUT requests to the server to succeed.
        },

        'is': function (type) {
            // check if a tile is of (type). the type is _not_ the tile's template.
            return this.get('content-type').toLowerCase() === type.toLowerCase();
        },

        /**
         * Using its model instance, create a view of the "best" class.
         * If the chosen view's matching template cannot be found, this
         * returns undefined.
         *
         * @returns {TileView}
         */
        'createView': function () {
            var TargetClass, view;

            switch (this.get('type')) {
            case "video":
                TargetClass = core.VideoTileView;
                break;
            default:
                TargetClass = SecondFunnel.utils.findClass(
                    'TileView', this.get('type'), core.TileView);
            }
            // #CtrlF fshkjr
            view = new TargetClass({'model': this});
            broadcast('tileViewInitialized', view, this);
            return view.render();
        }
    });

    core.TileCollection = Backbone.Collection.extend({
        // Our TileCollection manages ALL the tiles on the page.
        'model': function (attrs) {
            return new SecondFunnel.utils.findClass('Tile', '', core.Tile)(attrs);
        },
        'loading': false,
        // 'totalItems': null,  // TODO: what is this?

        'initialize': function (arrayOfData) {
            // Our TileCollection starts by rendering several Tiles using the
            // data it is passed.
            var data;
            for (data in arrayOfData) {  // Generate Tile
                if (arrayOfData.hasOwnProperty(data)) {
                    this.add(new core.Tile(data));
                }
            }
            broadcast('tileCollectionInitialized', this);
        }
    });

    core.HeroAreaView = Marionette.ItemView.extend({
        // $(...).html() defaults to the first item successfully selected
        // so featured will be used only if stl is not found.
        'model': new core.Tile(SecondFunnel.option('page:product', {})),
        'template': "#stl_template, #featured_template, #hero_template",
        'onRender': function () {
            var buttons,
                $heroArea = $('#hero-area');
            if (this.$el.length) {  // if something rendered, it was successful
                $heroArea.html(this.$el.html());

                if (!(SecondFunnel.support.touch() || SecondFunnel.support.mobile()) &&
                    this.$('.social-buttons').length >= 1) {
                        buttons = new SecondFunnel.sharing.SocialButtons({
                            'model': this.model
                        })
                        .render().load().$el;
                    $heroArea.find('.social-buttons').append(buttons);
                }

            }
        }
    });

    core.TileView = Marionette.Layout.extend({
        // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
        'tagName': SecondFunnel.option('tileElement', "div"),
        'templates': function (currentView) {
            var templateRules = [  // dictated by CtrlF fshkjr
                "#<%= options.store.slug %>_<%= data['content-type'] %>_<%= data.template %>_mobile_tile_template",  // gap_instagram_image_mobile_tile_template
                "#<%= data['content-type'] %>_<%= data.template %>_mobile_tile_template",                            // instagram_image_mobile_tile_template
                "#<%= options.store.slug %>_<%= data.template %>_mobile_tile_template",                              // gap_image_mobile_tile_template
                "#<%= data.template %>_mobile_tile_template",                                                        // image_mobile_tile_template

                "#<%= options.store.slug %>_<%= data['content-type'] %>_<%= data.template %>_tile_template",         // gap_instagram_image_tile_template
                "#<%= data['content-type'] %>_<%= data.template %>_tile_template",                                   // instagram_image_tile_template
                "#<%= options.store.slug %>_<%= data.template %>_tile_template",                                     // gap_image_tile_template
                "#<%= data.template %>_tile_template",                                                               // image_tile_template

                "#product_mobile_tile_template",                                                                     // fallback
                "#product_tile_template"                                                                             // fallback
            ];

            if (!SecondFunnel.support.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                templateRules = _.reject(templateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }

            console.debug('Template search tree for view %O: %O',
                        currentView, templateRules);
            return templateRules;
        },
        'template': "#product_tile_template",
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

        'initialize': function (options) {
            // Creates the TileView using the options.  Subclasses should not override this
            // method, rather provide an 'onInitialize' function
            var data = options.model.attributes,
                self = this;

            _.each(data['content-type'].toLowerCase().split(),
                function (cName) {
                    self.className += " " + cName;
                });
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
                preview = new core.PreviewWindow({
                    'model': tile,
                    'caller': ev.currentTarget
                });
                SecondFunnel.vent.trigger("tileClicked", ev, this);
            }
        },

        'onBeforeRender': function () {
            var maxImageSize,
                self = this;
            try {
                maxImageSize = _.findWhere(this.model.images[0].sizes,
                    {'name': 'master'})[0];
                this.model.set('size', maxImageSize);

                if (Math.random() > 0.333 && maxImageSize.width >= 512) {
                    this.$el.addClass('wide');
                }  // else: leave it as 1-col
            } catch (imageServiceNotReady) {
                if (this.model.get('template') === 'combobox' || (Math.random() < 0.333)) {
                    this.$el.addClass('wide');
                }
            }
            // Listen for the image being removed from the DOM, if it is, remove
            // the View/Model to free memory
            this.$el.on('remove', function (ev) {
                if (ev.target === self.el) {
                    self.model.destroy();
                }
            });
        },

        'onMissingTemplate': function () {
            // If a tile fails to load, destroy the model
            // and subsequently this tile.
            this.model.destroy();
            this.close();
        },

        'onRender': function () {
            if (this.model.get('size')) {
                // Check if ImageService is ready
                this.$("img").css({
                    'background-color': this.model.get('dominant-color'),
                    'width': this.model.get('size').width,
                    'height': this.model.get('size').height
                });
            }

            // semi-stupid view-based resizer
            var tileImg = this.$('img.focus'),
                columns = (this.$el.hasClass('wide') && $window.width() > 480) ? 2 : 1,
                columnWidth = SecondFunnel.option('columnWidth', $.noop)() || 255;
            if (tileImg.length) {
                tileImg.attr('src', SecondFunnel.utils.pickImageSize(tileImg.attr('src'),
                                    columnWidth * columns));
            }

            if (this.tapIndicator && this.socialButtons) {
                // Need to do this check in case layout is closing due
                // to broken images.
                if (SecondFunnel.sharing.SocialButtons.prototype.buttonTypes.length &&
                    !(SecondFunnel.support.touch() || SecondFunnel.support.mobile())) {
                    this.socialButtons.show(new SecondFunnel.sharing.SocialButtons({model: this.model}));
                }
                if (SecondFunnel.support.touch()) {
                    this.tapIndicator.show(new core.TapIndicator());
                }
            }

            this.$el.scaleImages();
        }
    });

    core.VideoTileView = core.TileView.extend({
        // VideoTile extends from TileView, allows playing of Video files;
        // for now, we only support YT
        'onInitialize': function () {
            // Add here additional things to do when loading a VideoTile
            this.$el.addClass('wide');

            if (this.model.is('youtube')) {
                this.model.set("thumbnail", 'http://i.ytimg.com/vi/' +
                                            this.model.get('original-id') +
                                            '/hqdefault.jpg');
            }

            // Determine which click handler to use; determined by the
            // content type.
            var handler = _.capitalize(this.model.get('content-type'));
            this.onClick = this['onClick' + handler] || this.onClickVideo;
        },

        'onClickYoutube': function (ev) {
            // Renders a YouTube video in the tile
            var thumbId = 'thumb-' + this.model.cid,
                $thumb = this.$('div.thumbnail'),
                self = this;

            if (window.YT === undefined) {
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
        },

        'onClickVideo': function () {
            // TODO: play videos more appropriately
            window.open(this.model.get('original-url') || this.model.get('url'));
        },

        'onPlaybackEnd': function (ev) {
            SecondFunnel.vent.trigger("videoEnded", ev, this);
        }
    });

    core.Discovery = Marionette.CompositeView.extend({
        // Manages the HTML/View of ALL the tiles on the page (our discovery area)
        // tagName: "div"
        'el': $(SecondFunnel.option('discoveryTarget')),
        'itemView': core.TileView,
        'collection': null,
        'loading': false,
        'lastScrollTop': 0,

        // prevent default appendHtml behaviour (append in batch)
        'appendHtml': $.noop,

        'initialize': function (options) {
            var self = this;

            this.collection = new core.TileCollection();
            this.categories = new core.CategorySelector(  // v-- options.categories is deprecated
                SecondFunnel.option("page:categories") ||
                SecondFunnel.option("categories") || []
            );
            this.attachListeners();
            this.countColumns();

            // If the collection has initial values, lay them out
            if (options.initialResults && options.initialResults.length > 0) {
                console.log('laying out initial results');
                this.layoutResults(options.initialResults);
            }
            // ... then fetch more products from IR
            this.getTiles();
        },

        'attachListeners': function () {
            var self = this;
            // TODO: Find a better way than this...
            _.bindAll(this, 'pageScroll', 'toggleLoading',
                'getMoreResults', 'layoutResults');
            $window
                .scroll(_.throttle(this.pageScroll, 500))
                .resize(_.throttle(function () {
                    // did you know any DOM element without resize events
                    // can still react to potential resizes by having its
                    // own .bind('resize', function () {})?
                    $('.resizable', document).trigger('resize');

                    self.countColumns();

                    broadcast('windowResize');
                }, 500))
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
            SecondFunnel.vent.on("tileClicked", this.updateContentStream,
                this);
            SecondFunnel.vent.on('changeCampaign', this.categoryChanged, this);
            return this;
        },

        /**
         *
         * @param options
         * @param tile {TileView}: supply a tile View to have tiles inserted
         *                         after it. (optional)
         * @returns this
         */
        'getTiles': function (options, tile) {
            var self = this,
                opts;
            if (this.loading) {
                console.warn('Already loading tiles. Try again later');
                return this;
            }
            this.toggleLoading(true);
            opts = options || {};
            opts.type = opts.type || 'campaign';

            $.when(SecondFunnel.intentRank.getResults(opts))
                .always(function (data) {
                    self.layoutResults(data, tile);
                })
                .always(this.getMoreResults);
            return this;
        },

        /**
         * @param data {array}: byproduct of .always() passing back the data.
         *                      its use is not recommended.
         * @returns this
         */
        'getMoreResults': function (data) {
            // creates conditions needed to get more results.
            var self = this;
            this.toggleLoading(false);

            setTimeout(function () {
                self.pageScroll();
            }, 100);
            return this;
        },

        /**
         * @param data {array}: list of product json objects
         * @param tile {View}: pre-rendered tile view
         * @returns this
         */
        'layoutResults': function (data, tile) {
            var self = this,
                $tileEls = $(),
                $tile;

            // Check if we don't have anything
            if (data.length === 0) {
                return this.toggleLoading(false);
            }

            // If we have data to use.
            _.each(data, function (tileData) {
                // Create the new tiles using the data
                var tile = new core.Tile(tileData),
                    view = tile.createView();

                // add this model to our collection of models.
                self.collection.add(tile);
                if (view && !view.isClosed) {
                    // Ensure we were given something
                    $tileEls = $tileEls.add(view.$el);
                } else if (view === undefined) {
                    // render unsuccessful (warning already issued in createView)
                    return null;
                }
            });

            if (tile && tile.$el) {
                $tile = tile.$el;  // this would be the "insert after" target
            }
            SecondFunnel.layoutEngine.add($tileEls, $tile)
                .always(function () {
                    self.toggleLoading(false);
                })
                .always(this.getMoreResults);
            return this;
        },

        /**
         * Adds "col-n" classes to the html tag.
         * @returns {number}
         */
        'countColumns': function () {
            var i,
                $html = $('html'),
                maxColsDef = SecondFunnel.option('maxColumnCount', 4),
                maxCols = $window.width() / (SecondFunnel.option('columnWidth', $.noop)() || 255);
            $html.removeClass(function (idx, cls) {
                // remove all current col-* classes
                return (cls.match(/col-\d+/g) || []).join(' ');
            });
            for (i = 0; i < maxCols; i++) {
                if (i <= maxColsDef) {
                    $html.addClass('col-' + i);
                }
            }

            SecondFunnel.layoutEngine.layout();
            return maxCols;
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
                SecondFunnel.layoutEngine.empty();
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
                viewportHeights = pageHeight * (SecondFunnel.option('prefetchHeight', 1));

            if (!this.loading && $('html').css('overflow') !== 'hidden' &&
                pageBottomPos >= documentBottomPos - viewportHeights) {
                // get more tiles to fill the screen.
                this.getTiles();
            }

            // detect scrolling detection. not used for anything yet.
            var st = $window.scrollTop();
            if (st > this.lastScrollTop) {
                broadcast('scrollDown', this);
            } else {
                broadcast('scrollUp', this);
            }
            this.lastScrollTop = st;
        }
    });

    core.Category = Backbone.Model.extend({
        // Base empty category, no functionality needed here
    });

    core.CategoryView = Marionette.ItemView.extend({
        'events': {
            'click': function (ev) {
                ev.preventDefault();
                SecondFunnel.vent.trigger('changeCampaign', ev, this);
            }
        },

        'initialize': function (options) {
            // Initializes the category view, expects some el to use
            this.el = options.el;
            this.$el = $(this.el);
            delete options.$el;
            this.model = new core.Category(options);
        }
    });

    core.CategorySelector = Marionette.CompositeView.extend({
        // This CompositeView does not create an element, rather is passed
        // the element that it will use for category selection
        'itemView': core.CategoryView,

        'initialize': function (categories) {
            // Initialize a category view for each object with a
            // data-category option.
            var views = [];
            $('[data-category]').each(function () {
                var id = $(this).attr('data-category');
                if (_.findWhere(categories, {'id': Number(id)})) {
                    // Make sure category is a valid one.
                    views.push(new core.CategoryView({
                        'id': id,
                        'el': this
                    }));
                }
            });
            this.views = views;
        }
    });

    core.PreviewContent = Marionette.ItemView.extend({
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

            this.$el.scaleImages();

            // out of scope
            $('.scrollable', '.previewContainer').scrollable(true);

            // disable scrolling for the rest of the document
            $(document.body).addClass('no-scroll');
            broadcast('previewRendered', this);
        },

        'initialize': function() {
            this.$el.attr({
                'id': 'preview-' + this.model.cid
            });
        },

        'close': function() {
            $(document.body).removeClass('no-scroll');
        }
    });


    core.PreviewWindow = Marionette.Layout.extend({
        'tagName': "div",
        'className': "previewContainer",
        'template': "#preview_container_template",
        'events': {
            'click .close, .mask': function () {
                this.$el.scrollable(false);
                this.$el.fadeOut(SecondFunnel.option('previewAnimationDuration'));
                this.close();
            }
        },

        'regions': {
            'content': '.template.target',
            'socialButtons': '.social-buttons'
        },


        'initialize': function (options) {
            // Initialize the PreviewWindow by rendering the content to
            // display in it as well.
            var ContentClass = SecondFunnel.utils.findClass('PreviewContent',
                    options.model.get('template'), core.PreviewContent),
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
            this.content.currentView.close();
            this.close();
        },

        'onBeforeRender': function () {

        },

        'templateHelpers': function () {
            // return {data: $.extend({}, this.options, {template: this.template})};
        },

        'onRender': function () {
            this.$el.css({display: "table"});
            this.$el.scaleImages();

            $('body').append(this.$el.fadeIn(SecondFunnel.option('previewAnimationDuration')));
        }
    });

    core.TapIndicator = Marionette.ItemView.extend({
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

    getModifiedTemplateName = function (name) {
        // If this logic gets any more complex, it should be moved into
        // Tile or TileView.
        return name.replace(/(styld[\.\-]by|tumblr|pinterest|facebook|instagram)/i,
            'image');
    };
});