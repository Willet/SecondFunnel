/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _,
  Willet, broadcast */
SecondFunnel.module('core', function (core, SecondFunnel) {
    // other args: https://github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document),
        Tile, TileCollection, HeroAreaView, TileView, VideoTileView,
        Category, CategoryView, CategorySelector, PreviewContent, PreviewWindow,
        TapIndicator, getModifiedTemplateName;

    // not actual php values
    _.extend(SecondFunnel, {
        QUIET: 0, ERROR: 1, WARNING: 2, LOG: 3, VERBOSE: 4, ALL: 5
    });

    SecondFunnel.option = function (name, defaultValue) {
        // convenience method for accessing PAGES_INFO or TEST_*.
        // to access deep options (e.g. PAGES_INFO.store.name), use the key
        // "store.name" or "store:name" (preferred).
        var opt = Backbone.Marionette.getOption(SecondFunnel, name),
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
            if (SecondFunnel.options &&
                SecondFunnel.options.debug >= SecondFunnel.WARNING) {
                console.warn('Missing option: ' + name);
            }
        }
        return defaultValue;  // ...and defaultValue defaults to undefined
    };

    Backbone.Marionette.TemplateCache._exists = function (templateId) {
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
        cachedTemplate = new Backbone.Marionette.TemplateCache(templateId);
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

    Backbone.Marionette.View.prototype.getTemplate = function () {
        // Accept an arbitrary number of template selectors instead of just one.
        // function will return in a short-circuit manner once a template is found.
        var i, templateIDs = Backbone.Marionette.getOption(this, "templates"),
            template = Backbone.Marionette.getOption(this, "template"),
            temp, templateExists, data;

        if (templateIDs) {
            if (typeof templateIDs === 'function') {
                // if given as a function, call it, and expect [<string> selectors]
                templateIDs = templateIDs(this);
            }

            for (i = 0; i < templateIDs.length; i++) {
                data = $.extend({},
                    Backbone.Marionette.getOption(this, "model").attributes);
                data.template = getModifiedTemplateName(data.template);

                temp = _.template(templateIDs[i], {
                    'options': SecondFunnel.options,
                    'data': data
                });
                templateExists = Backbone.Marionette.TemplateCache._exists(temp);

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

    Backbone.Marionette.ItemView.prototype.onMissingTemplate = function () {
        // Default on missing template event
        this.remove();
    };

    Tile = Backbone.Model.extend({
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
                "type": this.get('template'),  // default type being its template
                "caption": SecondFunnel.utils.safeString(this.get("caption"))
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
                TargetClass = VideoTileView;
                break;
            default:
                TargetClass = SecondFunnel.utils.findClass(
                    'TileView', this.get('type'), TileView);
            }
            // #CtrlF fshkjr
            view = new TargetClass({'model': this});
            broadcast('tileViewInitialized', view, this);
            return view.render();
        }
    });

    TileCollection = Backbone.Collection.extend({
        // Our TileCollection manages ALL the tiles on the page.
        'model': function (attrs) {
            return new SecondFunnel.utils.findClass('Tile', '', Tile)(attrs);
        },
        'loading': false,
        // 'totalItems': null,  // TODO: what is this?

        'initialize': function (arrayOfData) {
            // Our TileCollection starts by rendering several Tiles using the
            // data it is passed.
            var data;
            for (data in arrayOfData) {  // Generate Tile
                if (arrayOfData.hasOwnProperty(data)) {
                    this.add(new Tile(data));
                }
            }
            broadcast('tileCollectionInitialized', this);
        }
    });

    HeroAreaView = Backbone.Marionette.ItemView.extend({
        // $(...).html() defaults to the first item successfully selected
        // so featured will be used only if stl is not found.
        'model': new Tile(SecondFunnel.option('page:product', {})),
        'template': "#stl_template, #featured_template, #hero_template",
        'onRender': function () {
            if (this.$el.length) {  // if something rendered, it was successful
                $('#hero-area').html(this.$el.html());

                if (!(SecondFunnel.support.touch() || SecondFunnel.support.mobile()) &&
                    this.$('.social-buttons').length >= 1) {
                    var buttons = new SecondFunnel.sharing.SocialButtons({
                            'model': this.model
                        })
                        .render().load().$el;
                    $('#hero-area').find('.social-buttons').append(buttons);
                }

            }
        }
    });

    TileView = Backbone.Marionette.Layout.extend({
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

            if (SecondFunnel.options.debug >= SecondFunnel.VERBOSE) {
                console.log('Template search tree for view %O: %O',
                            currentView, templateRules);
            }
            return templateRules;
        },
        'template': "#product_tile_template",
        'className': SecondFunnel.option('itemSelector',
            '').substring(1),

        'events': {
            'click': "onClick",
            'mouseenter': "onHover",
            "mouseleave": "onHover"
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
                preview = new PreviewWindow({
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
                    this.tapIndicator.show(new TapIndicator());
                }
            }

            this.$el.scaleImages();
        }
    });

    VideoTileView = TileView.extend({
        // VideoTile extends from TileView, allows playing of Video files;
        // for now, we only support YT
        'onInitialize': function (options) {
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

            if (typeof window.YT === 'undefined') {
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

    core.Discovery = Backbone.Marionette.CompositeView.extend({
        // Manages the HTML/View of ALL the tiles on the page (our discovery area)
        // tagName: "div"
        'el': $(SecondFunnel.option('discoveryTarget')),
        'itemView': TileView,
        'collection': null,
        'loading': false,
        'lastScrollTop': 0,
        'intentRankResults': [0, 0],  // after fetching stuff from IR, nothing was added to the page.

        // prevent default appendHtml behaviour (append in batch)
        'appendHtml': $.noop,

        'initialize': function (options) {
            var self = this;

            // Initialize IntentRank; use as a seperate module to make changes easier.
            SecondFunnel.intentRank.initialize(options);

            this.collection = new TileCollection();
            this.categories = new CategorySelector(  // v-- options.categories is deprecated
                SecondFunnel.option("page:categories") ||
                SecondFunnel.option("categories") || []
            );
            this.attachListeners();
            this.countColumns();

            // If the collection has initial values, lay them out
            if (options.initialResults && options.initialResults.length > 0) {
                if (options.debug >= SecondFunnel.LOG) {
                    console.log('laying out initial results');
                }
                this.layoutResults(options.initialResults, undefined,
                    function () {
                        self.getTiles();
                    });
            } else {
                // Load additional results and add them to our collection
                this.getTiles();
            }
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
                    $('.resizable', document).resize();

                    self.countColumns();

                    broadcast('windowResize');
                }, 500))
                .scrollStopped(function () {
                    // deal with tap indicator fade in/outs
                    if (SecondFunnel.support.touch()) {
                        SecondFunnel.vent.trigger('scrollStopped', self);
                    }
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

        'getTiles': function (options, $tile) {
            if (!this.loading) {
                this.toggleLoading();
                options = options || {};
                options.type = options.type || 'campaign';
                SecondFunnel.intentRank.getResults(options,
                    this.layoutResults, $tile);
            } else {
                if (SecondFunnel.option('debug', SecondFunnel.QUIET) >= SecondFunnel.WARNING) {
                    console.warn('Already loading tiles. Try again later');
                }
            }
            return this;
        },

        "getMoreResults": function () {
            // creates conditions needed to get more results.
            var self = this;
            this.toggleLoading(false);
            if (self.intentRankResults[1] === self.collection.models.length) {
                // loaded nothing last time.
                self.intentRankResults[0]++;
                if (self.intentRankResults[0] > 5) {
                    if (SecondFunnel.option('debug', SecondFunnel.QUIET) >=
                        SecondFunnel.ERROR) {
                        console.error('Too many consecutive endpoint failures. ' +
                            'Not trying again.');
                    }
                    return this;
                }
            } else {
                // success = counter reset
                self.intentRankResults[0] = 0;
                self.intentRankResults[1] = self.collection.models.length;
            }
            setTimeout(function () {
                self.pageScroll();
            }, 100);
            return this;
        },

        'layoutResults': function (data, tile, callback) {
            var self = this,
                $tileEls = $();
            callback = callback || this.getMoreResults;

            // Check if we don't have anything
            if (data.length === 0) {
                return this.toggleLoading();
            }

            // If we have data to use.
            data = this.filter(data);  // custom function
            _.each(data, function (tileData) {
                // Create the new tiles using the data
                var tile = new Tile(tileData),
                    img = tile.get('image'),
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

            if (tile) {
                SecondFunnel.layoutEngine.call('insert', $tileEls, tile.$el,
                    callback);
            } else {
                SecondFunnel.layoutEngine.call('append', $tileEls,
                    callback);
            }
            return this;
        },

        'filter': function (content, selector) {
            // Filter the content in the LayoutEngine based on the selector
            // passed and the criteria/filters defined in the SecondFunnel options.
            var filters = this.options.filters || [];
            filters.push(selector);
            filters = _.flatten(filters);

            for (var i = 0; i < filters.length; ++i) {
                var filter = filters[i];
                if (content.length === 0) {
                    break;
                }
                switch (typeof filter) {
                case 'function':
                    content = _.filter(content, filter);
                    break;
                case 'object':
                    content = _.where(content, filter);
                    break;
                }
            }
            return content;
        },

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
                return this;
            }
            return this.getTiles({
                'type': "content",
                'id': id
            }, tile);
        },

        'categoryChanged': function (ev, category) {
            // Changes the category (campaign) by refreshign IntentRank, clearing
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

    Category = Backbone.Model.extend({
        // Base empty category, no functionality needed here
    });

    CategoryView = Backbone.Marionette.ItemView.extend({
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
            this.model = new Category(options);
        }
    });

    CategorySelector = Backbone.Marionette.CompositeView.extend({
        // This CompositeView does not create an element, rather is passed
        // the element that it will use for category selection
        'itemView': CategoryView,

        'initialize': function (categories) {
            // Initialize a category view for each object with a
            // data-category option.
            var views = [];
            $('[data-category]').each(function () {
                var id = $(this).attr('data-category');
                if (_.findWhere(categories, {'id': Number(id)})) {
                    // Make sure category is a valid one.
                    views.push(new CategoryView({
                        'id': id,
                        'el': this
                    }));
                }
            });
            this.views = views;
        }
    });

    PreviewContent = Backbone.Marionette.ItemView.extend({
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

            if (SecondFunnel.options.debug >= SecondFunnel.VERBOSE) {
                console.log('Template search tree for view %O: %O',
                            currentView, templateRules);
            }
            return templateRules;
        },
        'onRender': function () {
            // ItemViews don't have regions - have to do it manually
            var buttons, width;
            if (!(SecondFunnel.support.touch() || SecondFunnel.support.mobile())) {
                buttons = new SecondFunnel.sharing.SocialButtons({model: this.model}).render().load().$el;
                this.$('.social-buttons').append(buttons);
            }
            width = Backbone.Marionette.getOption(this, 'width');
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


    PreviewWindow = Backbone.Marionette.Layout.extend({
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
                    options.model.get('template'), PreviewContent),
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

    TapIndicator = Backbone.Marionette.ItemView.extend({
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
        'onScrollStopped': function (dA) {
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

    // expose some classes (only if required)
    SecondFunnel.classRegistry = {
        HeroAreaView: HeroAreaView,
        Tile: Tile,
        TileView: TileView,
        trailingCommas: undefined
    };
});