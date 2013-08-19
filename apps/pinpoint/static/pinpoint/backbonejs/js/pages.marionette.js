// Declaration of the SecondFunnel JS application
var SecondFunnel = new Backbone.Marionette.Application();
// Custom event trigger/listener
SecondFunnel.vent = _.extend({}, Backbone.Events);
SecondFunnel.templates = {};

var Tile = Backbone.Model.extend({
    defaults: {
        // Default product tile settings, some tiles don't
        // come specifying a type or caption
        'caption': "I don't even",
        'tile-id': 0,
        'content-type': "product",
        // Default YT settings, some videos dont' come
        // specifying dimensions and/or autoplay settings.
        'width': 480,
        'height': 300,
        'autoplay': 0
    },

    initialize: function (data) {
        _.extend(this, data);
    },

    getType: function () {
        // Get the content type of this tile
        return this.data['content-type'];
    },

    getId: function () {
        // Get the ID of this tile (for DB queries)
        return this.data['tile-id'];
    }
});

var LayoutEngine = Backbone.Model.extend({
    // Our layoutEngine, acts as a BlackBox for whatever we're using
    options: {
        itemSelector: PAGES_INFO.discoveryItemSelector,
        isResizeBound: true,
        visibleStyle: {
            'opacity': 1,
            'webkit-transform': 'none'
        },
        isAnimated: true,
        columnWidth: PAGES_INFO.columnWidth(),
        transitionDuration: PAGES_INFO.masonryAnimationDuration + 's'
    },

    initialize: function ($elem, options) {
        _.extend(this, {'options': options });
        $elem.masonry(this.options).masonry('bindResize');
        this.$el = $elem;
    },

    append: function ($fragment, callback) {
        $fragment.hide().appendTo(this.$el);
        this.$el.masonry('appended', $fragment).masonry();
        return this.imagesLoaded($fragment, callback);
    },

    reload: function ($fragment) {
        this.$el.masonry('reloadItems');
        this.$el.masonry();
        return this;
    },

    insert: function ($target, $fragment, callback) {
        $fragment.hide().insertAfter($target);
        return this.imagesLoaded($fragment, callback);
    },

    imagesLoaded: function ($fragment, callback) {
        // Compiles a list of the broken image srcs and returns them
        // How we handle this is up to the Discovery module
        var self = this,
            good = [],
            broken = [];
        imagesLoaded($fragment).on('always', function (imgLoad) {
            _.each(imgLoad.images, function (img) {
                if (!img.isLoaded) {
                    img.img.remove();
                    broken.push(img.img);
                } else {
                    good.push(img.img);
                }
            });
            if (callback) {
                callback(good, broken);
            }
            $(imgLoad.elements).show();
            self.reload();
        });
    }
});

var IntentRank = Backbone.Model.extend({
    // intentRank module
    base: "http://intentrank-test.elasticbeanstalk.com/intentrank",
    templates: {
        'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
        'content': "<%=url%></store/<%=store.name%>/campaign/<%=campaign%>/<%=id%>/getresults"
    },
    store: PAGES_INFO.store,
    campaign: PAGES_INFO.campaign,

    getResults: function (callback, options) {
        var self = this,
            uri = _.template(this.templates[options.type],
                             _.extend({}, options, this, {
                                 'url': this.base
                             }));

        $.ajax({
            url: uri,
            data: {
                'results': 10, // TODO: Should be calculated somehow
            },
            contentType: "json",
            dataType: 'jsonp',
            timeout: 5000,
            success: function (results) {
                return callback(results);
            },
            error: function (jxqhr, textStatus, error) {
                return callback([]);
            }
        });
    }
});

var TileCollection = Backbone.Collection.extend({
    // Our TileCollection manages ALL the tiles on the page.
    model: function (attrs) {
        var SubClass = 'Tile';
        if (window[SubClass]) {
            return new window[SubClass](attrs);
        }
        return new Tile(attrs);  // base class
    },
    loading: false,
    totalItems: null,

    initialize: function (arrayOfData) {
        // Our TileCollection starts by rendering several Tiles using the
        // data it is passed.
        for (var data in arrayOfData) {
            // Generate Tile
            this.add(new Tile(data));
        }
    }
});

var TileView = Backbone.Marionette.ItemView.extend({
    // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
    template: "product",

    events: {
        'click': function (ev) {
            "use strict";
            var tile = this.model,
                preview = new PreviewWindow({model: tile});
            preview.render();
        }
    },

    initialize: function (options) {
        var data = options.model,
            template = SecondFunnel.templates[data.template];
        // Silently fall back to default template
        this.template = template || SecondFunnel.templates[this.template];

        // If the tile model is removed, remove the DOM element
        this.listenTo(this.model, 'destroy', this.remove);
    },

    onRender: function () {
        // Listen for the image being removed from the DOM, if it is, remove
        // the View/Model to free memory
        this.$("img").on('remove', this.model.destroy);
    }
});

var Discovery = Backbone.Marionette.CompositeView.extend({
    // Manages the HTML/View of ALL the tiles on the page (our discovery area)
    // tagName: "div"
    el: $(PAGES_INFO.discoveryTarget),
    itemView: TileView,
    intentRank: null,
    collection: null,
    layoutEngine: null,
    loading: false,

    triggers: {
        "scroll window": "pageScroll"
    },

    appendHtml: function (collectionView, itemView) {
        collectionView.$(":last").append(itemView.el);
    },

    initialize: function (options) {
        // Initialize IntentRank; use as a seperate module to make changes easier.
        SecondFunnel.intentRank = new IntentRank;
        // Black box Masonry (this will make migrating easier in the future)
        SecondFunnel.layoutEngine = new LayoutEngine(this.$el,
            options.masonry);

        $('script[type="text/template"]').each(function () {
            var id = $(this).attr('id');

            if (id.indexOf('_template') > -1) {
                id = id.replace('_template', '');  // remove id safety suffix
            }
            SecondFunnel.templates[id] = _.template($(this).html(), undefined,
                { variable: 'data' });
        });
        this.collection = options.collection || new TileCollection;
        // Load additional results and add them to our collection
        this.attachListeners().getTiles();
    },

    attachListeners: function () {
        // Attach our listeners that can't be handled through events
        _.bindAll(this, 'pageScroll');
        $(window).scroll(this.pageScroll);
        _.bindAll(this, 'toggleLoading');

        return this;
    },

    getTiles: function (options) {
        if (!this.loading) {
            this.toggleLoading();
            options = options || {};
            options.type = options.type || 'campaign';
            SecondFunnel.intentRank.getResults(_.partial(this.createTiles, this),
                                               options);
        }
        return this;
    },

    createTiles: function (self, data, $tile) {
        var start = self.collection.length,
            $fragment = $();

        _.each(data, function (tileData) {
            // Create the new tiles using the data
            var tile = new Tile(tileData),
                view = new TileView({model: tile});
            self.collection.add(new Tile(tileData));
            view.render();
            $fragment = $fragment.add(view.$el);
        });

        // TODO: Need elegant way to delete broken images w/o memory leak
        if ($tile) {
            SecondFunnel.layoutEngine.insert($fragment, $tile, self.toggleLoading);
        } else {
            SecondFunnel.layoutEngine.append($fragment, self.toggleLoading);
        }
        return self;
    },

    toggleLoading: function (self) {
        this.loading = !this.loading;
        return this;
    },

    pageScroll: function () {
        var pageBottomPos = $(window).innerHeight() + $(window).scrollTop(),
            documentBottomPos = $(document).height();

        if (pageBottomPos >= documentBottomPos - 150 && !this.loading) {
            this.getTiles();
        }
    }
});


var PreviewWindow = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    className: "previewContainer",
    template: "#preview_container_template",
    model: Tile,
    events: {
        'click .close': function () {
            this.$el.fadeOut().remove();
        }
    },

    onRender: function () {
        this.$el.css({display: "table"});
        $('body').append(this.$el.fadeIn(100));
    }
});

$(function () {
    // Add SecondFunnel component(s)
    SecondFunnel.addInitializer(function (options) {
        // Add our initiliazer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        SecondFunnel.discovery = new Discovery({});
        SecondFunnel.discovery.on("pageScroll", function(args) {
            "use strict";
            args.view.getTiles();
        });
    });

    // Start the SecondFunnel app
    SecondFunnel.start(PAGES_INFO);
});
