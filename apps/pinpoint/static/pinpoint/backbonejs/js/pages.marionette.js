// JQuery Special event to listen to delete
$(function () {
    // stackoverflow.com/questions/2200494
    // does not work with jQuery UI
    // does not work when affected by html(), replace(), replaceWith(), ...
    var ev = new $.Event('remove'),
        orig = $.fn.remove;
    $.fn.remove = $.fn.remove || function () {
        $(this).trigger(ev);
        return orig.apply(this, arguments);
    };
});

// Marionette TemplateCache extension to allow checking cache for template
Backbone.Marionette.TemplateCache._exists = function (templateId) {
    // Checks if the Template exists in the cache, if not found
    // updates the cache with the template (if it exists), otherwise fail
    // returns true if exists otherwise false.
    var cached = this.templateCaches[templateId],
        template = Backbone.Marionette.$(templateId).html();

    if (cached || template) {
        if (!cached) {
            // template exists but was not cached
            var cachedTemplate = new Backbone.Marionette.TemplateCache(templateId);
            this.templateCaches[templateId] = cachedTemplate;
        }
        return true;
    }
    // template does not exist
    return false;
};


// TODO: Seperate this into modules/seperate files
// Declaration of the SecondFunnel JS application
var SecondFunnel = new Backbone.Marionette.Application();
window.SecondFunnel = SecondFunnel;
// Custom event trigger/listener
SecondFunnel.vent = _.extend({}, Backbone.Events);

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
        for (var key in data) {
            this.set(key, data[key]);
        }
    },

    getType: function () {
        // Get the content type of this tile
        return this.attributes['content-type'];
    },

    isProduct: function () {
        return this.getType() == 'product';
    },

    getId: function () {
        // Get the ID of this tile (for DB queries)
        return this.attributes['tile-id'];
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
        $fragment.children('img').eq(0).addClass('loading');
        $fragment.appendTo(this.$el);
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
            imgLoad = imagesLoaded($fragment);
        // Remove broken images as they appear
        imgLoad.on('progress', this.removeBroken);
        imgLoad.on('always', function () {
            // When all images are loaded, show the non-broken ones and reload
            $(this.elements).show().delay(100);
            self.reload();
            // Callback with the successfully loaded images
            callback(this.elements);
        });
        return this;
    },

    removeBroken: function (instance, image) {
        // Assume either instance or image is an instance of an LoadingImage object
        // Remove if broken
        image = image || instance;
        var $img = $(image.img);
        $img.removeClass('loading');
        if ( !image.isLoaded ) {
            $img.remove();
        }
        return this;
    }
});

var IntentRank = Backbone.Model.extend({
    // intentRank module
    base: "http://intentrank-test.elasticbeanstalk.com/intentrank",
    templates: {
        'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
        'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
    },
    store: PAGES_INFO.store,
    campaign: PAGES_INFO.campaign,

    getResults: function (options, callback) {
        var uri = _.template(this.templates[options.type],
                _.extend({}, options, this, {
                    'url': this.base
                })),
            args = Array.prototype.slice.apply(arguments);
        args = args.length > 2 ? args.slice(2) : [];

        $.ajax({
            url: uri,
            data: {
                'results': 10 // TODO: Should be calculated somehow
            },
            contentType: "json",
            dataType: 'jsonp',
            timeout: 5000,
            success: function (results) {
                args.unshift(results);
                return callback.apply(callback, args);
            },
            error: function (jxqhr, textStatus, error) {
                args.unshift([]);
                return callback.apply(callback, args);
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
    tagName: "div", // TODO: Should this be a setting?
    template: "#product_tile_template",
    className: PAGES_INFO.discoveryItemSelector.substring(1),

    events: {
        'click :not(.youtube)': "onClick",
        'mouseenter': "onHover",
        "mouseleave": "onHover"
    },

    initialize: function (options) {
        var data = options.model.attributes,
            template = "#" + data.template + "_tile_template",
            self = this;

        if (Backbone.Marionette.TemplateCache._exists(template)) {
            this.template = template;
        }

        _.each(data['content-type'].toLowerCase().split(), function (cName) {
            self.className += " " + cName;
        });
        this.$el.attr('class', this.className);

        // TODO: Is there a better way?
        if (this.$el.hasClass('youtube')) {
            this.$el.addClass('wide');
        }

        _.bindAll(this, 'close'); 
        // If the tile model is removed, remove the DOM element
        this.listenTo(this.model, 'destroy', this.close);
    },

    close: function () {
        // As it stands, since we aren't using a REST API, we don't store
        // the models anywhere so we don't need to destroy them.
        // Remove view and unbind listeners
        this.remove();
        this.unbind();
        this.views = [];
    },

    onHover: function (ev) {
        // Trigger tile hover event with event and tile
        SecondFunnel.vent.trigger("tileHover", ev, this);
    },

    onClick: function (ev) {
        "use strict";
        var tile = this.model,
            preview = new PreviewWindow({'model': tile});
        preview.render();
        preview.content.show(new PreviewContent({'model': tile}));

        SecondFunnel.vent.trigger("tileClicked", this);
    },

    onRender: function (ev) {
        // Listen for the image being removed from the DOM, if it is, remove
        // the View/Model to free memory
        this.$("img").on('remove', this.close);
    }
});


var YoutubeTileView = TileView.extend({
    // Subview of the TileView for Youtube Tiles
    initialize: function (options) {
        var data = options.model.attributes;
        _.extend({}, data, {
            'thumbnail': 'http://i.ytimg.com/vi/' + data['original-id'] +
                '/hqdefault.jpg'
        });
    },

    onClick: function (ev) {
        
    },

    onRender: function (ev) {
        // Don't do anything on Render...
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

        this.collection = options.collection || new TileCollection;
        // Load additional results and add them to our collection
        this.attachListeners().getTiles();
    },

    attachListeners: function () {
        // Attach our listeners that can't be handled through events
        _.bindAll(this, 'pageScroll');
        $(window).scroll(this.pageScroll);

        // TODO: Find a better way than this...
        _.bindAll(this, 'toggleLoading', 'layoutResults',
            'updateContentStream');

        // Vent Listeners
        SecondFunnel.vent.on("tileClicked", this.updateContentStream);

        return this;
    },

    getTiles: function (options) {
        if (!this.loading) {
            this.toggleLoading();
            options = options || {};
            options.type = options.type || 'campaign';
            SecondFunnel.intentRank.getResults(options, this.layoutResults);
        }
        return this;
    },

    layoutResults: function (data, $tile) {
        var self = this,
            start = self.collection.length,
            $fragment = $();

        _.each(data, function (tileData) {
            // Create the new tiles using the data
            var tile = new Tile(tileData),
                view = new TileView({model: tile});
            self.collection.add(tile);

            view.render();
            $fragment = $fragment.add(view.$el);
        });

        if ($fragment.length > 0) {
            if ($tile) {
                SecondFunnel.layoutEngine.insert($fragment, $tile,
                    this.toggleLoading);
            } else {
                SecondFunnel.layoutEngine.append($fragment,
                    this.toggleLoading);
            }
        }
        return this;
    },

    updateContentStream: function (tile) {
        var $tile = tile.$el;
        tile = tile.model;

        SecondFunnel.intentRank.getResults({
            'type': "content",
            'id': tile.getId()
        }, this.layoutResults, $tile);
        return this;
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


var PreviewContent = Backbone.Marionette.ItemView.extend({
    template: '#tile_preview_template'
});


var PreviewWindow = Backbone.Marionette.Layout.extend({
    'tagName': "div",
    'className': "previewContainer",
    'template': "#preview_container_template",
    'events': {
        'click .close, .mask': function () {
            this.$el.fadeOut().remove();
        }
    },
    'regions': {
        'content': '.template.target'
    },
    'onBeforeRender': function () {
    },
    'templateHelpers': function () {
        // return {data: $.extend({}, this.options, {template: this.template})};
    },
    'onRender': function () {
        this.$el.css({display: "table"});
        $('body').append(this.$el.fadeIn(100));
    }
});

function syntaxHighlight(json) {
    // something about internets http://stackoverflow.com/a/7220510/1558430
    if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 2);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g,
        '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
}

$(function () {
    // Add SecondFunnel component(s)
    SecondFunnel.addInitializer(function (options) {
        // Add our initiliazer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        SecondFunnel.discovery = new Discovery({});
        SecondFunnel.discovery.on("pageScroll", function (args) {
            "use strict";
            args.view.getTiles();
        });
    });

    // Start the SecondFunnel app
    SecondFunnel.start(PAGES_INFO);
});
