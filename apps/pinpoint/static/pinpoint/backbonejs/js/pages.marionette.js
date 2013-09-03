/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _, Willet */
// JSLint/Emacs js2-mode directive to stop global 'undefined' warnings.
// Declaration of the SecondFunnel JS application
SecondFunnel = (function (SecondFunnel, $window, $document) {
    "use strict";

    var Tile, TileCollection, FeaturedAreaView, TileView,
        VideoTileView, Discovery, Category, CategoryView,
        CategorySelector, PreviewContent, PreviewWindow,
        TapIndicator, EventManager, ShadowTile;

    // keep reference to options. this needs to be done before classes are declared.
    SecondFunnel.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};
    SecondFunnel.classRegistry = {};
    SecondFunnel.option = function (name, defaultValue) {
        // convenience method for accessing PAGES_INFO or TEST_*
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
            console.error('no such path');
        }
        return defaultValue;  // ...and defaultValue defaults to undefined
    };
    try {
        SecondFunnel.options.debug = 0;

        if (window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1') {
            SecondFunnel.options.debug = 1;
        }

        (function (hash) {
            var hashIdx = hash.indexOf('debug=');
            if (hashIdx > -1) {
                SecondFunnel.options.debug = hash[hashIdx + 6];
            }
        }(window.location.hash + window.location.search));
    } catch (e) {
        // this is an optional operation. never let this stop the script.
    }

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
                data.template = SecondFunnel.getModifiedTemplateName(data.template);

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

    Backbone.Marionette.ItemView.prototype.superRender = Backbone.Marionette.ItemView.prototype.render;  // TODO: ugly
    Backbone.Marionette.ItemView.prototype.render =  function () {
        try {
            this.superRender();
        } catch (err) {
            // If template not found signal error in rendering view.
            if (err.name &&  err.name === "NoTemplateError") {
                SecondFunnel.vent.trigger('log', "Could not find template " +
                   this.template + ". View did not render.");
                // Trigger methods
                this.isClosed = true;
                this.triggerMethod("missing:template", this);
            } else {
                throw err;
            }
        }
        return this;
    };

    Backbone.Marionette.ItemView.prototype.onMissingTemplate = function () {
        // Default on missing template event
        this.remove();
    };


    SecondFunnel.module("utils", function (utils) {
        utils.safeString = function (str, opts) {
            // trims the string and checks if it's just 'None'.
            // more checks to come later.
            return $.trim(str).replace(/^(None|undefined|false|0)$/, '');
        };

        utils.makeView = function (classType, params) {
            // view factory to allow views that bind to arbitrary regions
            // and use any template decided at runtime, e.g.
            //   someTemplate = '#derp1'
            //   a = makeView('Layout', {template: someTemplate})
            //   a.render()
            classType = classType || 'ItemView';
            return Backbone.Marionette[classType].extend(params);
        };

        utils.addWidget = function (name, selector, functionality) {
            // add a predefined UI component implemented as a region.
            // name must be unique. if addWidget is called with an existing
            // widget, the old one is overwritten.
            SecondFunnel.options.regions = SecondFunnel.options.regions || {};
            SecondFunnel.options.regionWidgets = SecondFunnel.options.regionWidgets || {};
            SecondFunnel.options.regions[name] = selector;
            SecondFunnel.options.regionWidgets[name] = functionality;
            broadcast('widgetAdded', name, selector, functionality);
        };

        utils.runWidgets = function (viewObject) {
            // process widget regions.
            // each widget function receives args (the view, the $element, option alias).
            var self = viewObject;

            // process itself (if it is a view)
            _.each(SecondFunnel.options.regions, function (selector, name, list) {
                var widgetFunc = SecondFunnel.options.regionWidgets[name];
                self.$(selector).each(function (idx, el) {
                    return widgetFunc(self, $(el), SecondFunnel.option);
                });
            });

            // process children regions (if it is a layout)
            _.each(self.regions, function (selector, name, list) {
                var isWidget = _.contains(SecondFunnel.options.regions, name),
                    widgetFunc = (SecondFunnel.options.regionWidgets || {})[name];
                if (isWidget && widgetFunc) {
                    self.$(selector).each(function (idx, el) {
                        return widgetFunc(self, $(el), SecondFunnel.option);
                    });
                }
            });
        };

        utils.pickImageSize = function (url, minWidth, scalePolicy) {
            // returns a url that is either
            //   - the url, if it is not an image service url, or
            //   - an image url pointing to one that is at least as wide as
            //     minWidth, or
            //   - an image url pointing to one that is at most as wide as
            //     the window width, or
            //   - if minWidth is ridiculously large, master.jpg.
            // if scalePolicy is "max", then the image served is always smaller
            //   than requested.
            var i,
                prevKey = 'pico',
                maxLogicalSize = Math.min($window.width(), $window.height()),
                sizable = /images\.secondfunnel\.com.+\.(jpe?g|png)/.test(url),
                nameRegex = /([^/]+)\.(jpe?g|png)/,
                imageSizes = SecondFunnel.option('imageSizes', {
                    // see Scraper: ImageServiceIntegrationTest.java#L52
                    "pico": 16,
                    "icon": 32,
                    "thumb": 50,
                    "small": 100,
                    "compact": 160,
                    "medium": 240,
                    "large": 480,
                    "grande": 600,
                    "1024x1024": 1024,
                    "master": 2048
                });

            if (!sizable) {
                return url;
            }

            for (i in imageSizes) {
                if (imageSizes.hasOwnProperty(i)) {
                    if (!scalePolicy || scalePolicy === 'min') {
                        if (imageSizes[i] >= minWidth) {
                            return url.replace(nameRegex, i + '.$2');
                        }
                    } else if (scalePolicy === 'max') {
                        if (imageSizes[i] >= minWidth) {
                            return url.replace(nameRegex, prevKey + '.$2');
                        }
                    }
                    if (imageSizes[i] >= maxLogicalSize) {
                        return url.replace(nameRegex, prevKey + '.$2');
                    }
                }
                prevKey = i;
            }
            return url;
        };
    });

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

            this.type = 'image';  // TODO: what is this
            this.set({
                "type": "image",
                "caption": SecondFunnel.utils.safeString(this.get("caption"))
            });
            if (_.contains(videoTypes, type)) {
                this.type = 'video';
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

        'createView': function () {
            var targetClassName, TargetClass, view;

            switch (this.type) {
            case "video":
                TargetClass = VideoTileView;
                break;
            default:
                targetClassName = _.capitalize(this.type) + 'TileView';
                if (window[targetClassName] !== undefined) {
                    TargetClass = window[targetClassName];
                    break;
                }
                if (SecondFunnel.classRegistry &&
                    SecondFunnel.classRegistry[targetClassName] !== undefined) {
                    // if designers want to define a new tile view, they must
                    // let SecondFunnel know about its existence.
                    TargetClass = SecondFunnel.classRegistry[targetClassName];
                    break;
                }
                TargetClass = TileView;
            }
            // undeclared / class not found in scope
            view = new TargetClass({model: this});
            broadcast('tileViewInitialized', view, this);
            return view.render();
        }
    });

    TileCollection = Backbone.Collection.extend({
        // Our TileCollection manages ALL the tiles on the page.
        'model': function (attrs) {
            var SubClass = 'Tile';
            if (window[SubClass]) {
                return new window[SubClass](attrs);
            }
            return new Tile(attrs);  // base class
        },
        'loading': false,
        'totalItems': null,

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

    FeaturedAreaView = Backbone.Marionette.ItemView.extend({
        // $(...).html() defaults to the first item successfully selected
        // so featured will be used only if stl is not found.
        'model': new Tile(SecondFunnel.option('featured')),
        'template': "#stl_template, #featured_template, #hero_template",
        'onRender': function () {
            if (this.$el.length) {  // if something rendered, it was successful
                $('#hero-area').html(this.$el.html());
            }

            // process widgets
            SecondFunnel.utils.runWidgets(this);
        }
    });

    TileView = Backbone.Marionette.Layout.extend({
        // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
        'tagName': SecondFunnel.option('tileElement', "div"),
        'templates': function (currentView) {
            return [
                "#<%= data.template %>_<%= data['content-type'] %>_tile_template",
                "#<%= data['content-type'] %>_<%= data.template %>_tile_template",
                "#<%= data.template %>_tile_template",
                "#product_tile_template" // default
            ];
        },
        'template': "#product_tile_template",
        'className': SecondFunnel.option('discoveryItemSelector',
            '').substring(1),

        'events': {
            'click': "onClick",
            'mouseenter': "onHover",
            "mouseleave": "onHover"
        },

        'regions': _.extend({}, {
            'socialButtons': '.social-buttons',
            'tapIndicator': '.tap-indicator-target'
        }, SecondFunnel.options.regions || {}),

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
                'id': this.cid
            });

            // do some kind of magic such that these methods are always called
            // with its context being this object.
            _.bindAll(this, 'close', 'modelChanged');

            // If the tile model is changed, re-render the tile
            this.listenTo(this.model, 'changed', this.modelChanged);

            // If the tile model is removed, remove the DOM element
            this.listenTo(this.model, 'destroy', this.close);
            // Call onInitialize if it exists
            if (this.onInitialize) {
                this.onInitialize(options);
            }
        },

        'modelChanged': function (model, value) {
            this.render();
        },

        'onHover': function (ev) {
            // Trigger tile hover event with event and tile
            SecondFunnel.vent.trigger("tileHover", ev, this);
            if (!SecondFunnel.observable.mobile() &&
                !SecondFunnel.observable.touch() &&
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
                preview = new PreviewWindow({
                    'model': tile,
                    'caller': ev.currentTarget
                });
            SecondFunnel.vent.trigger("tileClicked", ev, this);
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
                if (Math.random() < 0.333) {
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
                columnWidth = SecondFunnel.option('columnWidth', $.noop)() || 256;
            if (tileImg.length) {
                tileImg.attr('src', SecondFunnel.utils.pickImageSize(tileImg.attr('src'),
                                    columnWidth * columns));
            }

            if (this.tapIndicator && this.socialButtons) {
                // Need to do this check in case layout is closing due
                // to broken images.
                if (SecondFunnel.sharing.SocialButtons.prototype.buttonTypes.length && 
                    !(SecondFunnel.observable.touch() || SecondFunnel.observable.mobile())) {
                    this.socialButtons.show(new SecondFunnel.sharing.SocialButtons({model: this.model}));
                }
                this.tapIndicator.show(new TapIndicator());
            }

            this.$el.scaleImages();

            // process widgets
            SecondFunnel.utils.runWidgets(this);
        }
    });

    // TODO: Seperate this into modules/seperate files
    VideoTileView = TileView.extend({
        // VideoTile extends from TileView, allows playing of Video files; for
        // now, we only support YT
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
            this.onClick = this['on' + handler] || this.onVideo;
        },

        'onYoutube': function (ev) {
            // Renders a YouTube video in the tile
            var thumbId = 'thumb-' + this.cid,
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
                    'controls': SecondFunnel.observable.mobile()
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

        'onVideo': function () {
            // TODO: play videos more appropriately
            window.open(this.model.get('original-url') || this.model.get('url'));
        },

        'onPlaybackEnd': function (ev) {
            SecondFunnel.vent.trigger("videoEnded", ev, this);
        }
    });

    ShadowTile = Tile.extend({
        // based on a View, this object contains a get() and a set()
        // that does NOT alter its original model.
        'propBag': {},
        'get': function (key) {
            return this.propBag[key] || Backbone.Model.prototype.get.apply(this, arguments);
        },
        'set': function (key, val, options) {
            this.propBag[key] = val;
            return this;
        }
    });

    Discovery = Backbone.Marionette.CompositeView.extend({
        // Manages the HTML/View of ALL the tiles on the page (our discovery area)
        // tagName: "div"
        'el': $(SecondFunnel.option('discoveryTarget')),
        'itemView': TileView,
        'collection': null,
        'loading': false,
        'lastScrollTop': 0,

        // prevent default appendHtml behaviour (append in batch)
        'appendHtml': $.noop,

        'initialize': function (options) {
            var self = this;

            // Initialize IntentRank; use as a seperate module to make changes easier.
            SecondFunnel.intentRank.initialize(options);

            // Black box Masonry (this will make migrating easier in the future)
            SecondFunnel.layoutEngine.initialize(this.$el,
                options);
            this.collection = new TileCollection();
            this.categories = new CategorySelector(options.categories || []);
            this.attachListeners();

            // If the collection has initial values, lay them out
            if (options.initialResults && options.initialResults.length > 0) {
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
            // TODO: Find a better way than this...
            _.bindAll(this, 'pageScroll', 'toggleLoading',
                'toggleMoreResults', 'layoutResults');
            $window
                .scroll(_.throttle(this.pageScroll, 500))
                .resize(_.throttle(function () {
                    // did you know any DOM element without resize events
                    // can still react to potential resizes by having its
                    // own .bind('resize', function () {})?
                    $('.resizable', document).resize();

                    broadcast('windowResize');
                }, 500));

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
            }
            return this;
        },

        'toggleMoreResults': function () {
            var self = this;
            this.toggleLoading(false);
            setTimeout(function () {
                self.pageScroll();
            }, 100);
            return this;
        },

        'layoutResults': function (data, tile, callback) {
            var self = this,
                $fragment = $();
            callback = callback || this.toggleMoreResults;

            // Check if we don't have anything
            if (data.length === 0) {
                return this.toggleLoading();
            }

            // If we have data to use.
            data = this.filter(data);
            _.each(data, function (tileData) {
                // Create the new tiles using the data
                var tile = new Tile(tileData),
                    img = tile.get('image'),
                    view = tile.createView();

                if (!view.isClosed) {
                    // Ensure we were given something
                    self.collection.add(tile);
                    $fragment = $fragment.add(view.$el);
                }
            });

            if (tile) {
                SecondFunnel.layoutEngine.call('insert', $fragment, tile.$el,
                    callback);
            } else {
                SecondFunnel.layoutEngine.call('append', $fragment,
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

        'updateContentStream': function (ev, tile) {
            // Loads in related content below the specified tile
            var id = tile.model.get('tile-id');
            return id === null ? this :
                   this.getTiles({
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
                SecondFunnel.layoutEngine.clear();
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
            var pageBottomPos = $window.innerHeight() + $window.scrollTop(),
                documentBottomPos = $document.height(),
                viewportHeights = $window.innerHeight() * (SecondFunnel.option('prefetchHeight',
                    1));

            if (pageBottomPos >= documentBottomPos - viewportHeights && !this.loading) {
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
        // This ItemView does not create an element, rather is passed
        // the element that it will use for category selection
        itemView: CategoryView,

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
            var defaultTemplateRules = [
                // supported contexts: options, data
                '#<%= options.store.name %>_<%= data.template %>_mobile_preview_template',
                '#<%= options.store.name %>_<%= data.template %>_preview_template',
                '#<%= data.template %>_mobile_preview_template',
                '#<%= data.template %>_preview_template',
                '#tile_mobile_preview_template', // fallback
                '#tile_preview_template' // fallback
            ];

            if (!SecondFunnel.observable.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                defaultTemplateRules = _.reject(defaultTemplateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }
            return defaultTemplateRules;
        },
        'onRender': function () {
            // ItemViews don't have regions - have to do it manually
            var buttons, width;
            if (!(SecondFunnel.observable.touch() || SecondFunnel.observable.mobile())) {
                buttons = new SecondFunnel.sharing.SocialButtons({model: this.model}).render().load().$el;
                this.$('.social-buttons').append(buttons);
            }
            width = Backbone.Marionette.getOption(this, 'width');
            if (width) {
                this.$('.content').css('width', width + 'px');
            }

            this.$el.scaleImages();

            // process widgets
            SecondFunnel.utils.runWidgets(this);

            // out of scope
            $('.scrollable', '.previewContainer').scrollable(true);
            broadcast('previewRendered', this);
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
            this.render();
            if (!this.isClosed) {
                this.content.show(new PreviewContent({
                    'model': options.model,
                    'caller': options.caller
                }));
                if (this.content.currentView.isClosed) {
                    this.close();
                }
            }
        },

        'onMissingTemplate': function () {
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

            // process widgets
            SecondFunnel.utils.runWidgets(this);

            $('body').append(this.$el.fadeIn(SecondFunnel.option('previewAnimationDuration')));
        }
    });

    TapIndicator = Backbone.Marionette.ItemView.extend({
        'template': "#tap_indicator_template",
        'className': 'tap_indicator animated fadeIn',
        'onBeforeRender': function () {
            // http://jsperf.com/hasclass-vs-toggleclass
            // toggleClass with a boolean is 55% slower than manual checks
            if (SecondFunnel.observable.touch()) {
                $('html').addClass('touch-enabled');
            } else {
                $('html').removeClass('touch-enabled');
            }
        }
    });

    EventManager = Backbone.View.extend({
        // Top-level event binding wrapper. all events bubble up to this level.
        // the theme can declare as many event handlers as they like by creating
        // their own new EventManager({ event: handler, event: ... })s.
        'el': $window.add($document),
        'initialize': function (bindings) {
            var self = this;
            _.each(bindings, function (func, key, l) {
                var event = key.substr(0, key.indexOf(' ')),
                    selectors = key.substr(key.indexOf(' ') + 1);
                self.$el.on(event, selectors, func);
                if (SecondFunnel.option('debug', 0) > 0) {
                    console.log('regEvent ' + key);
                }
            });
        }
    });

    // expose some classes (only if required)
    SecondFunnel.classRegistry = {
        Discovery: Discovery,
        EventManager: EventManager,
        FeaturedAreaView: FeaturedAreaView,
        ShadowTile: ShadowTile
    };

    return SecondFunnel;
}(new Backbone.Marionette.Application(), $(window), $(document)));