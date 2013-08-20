// JQuery Special event to listen to delete
$(function() {
    // stackoverflow.com/questions/2200494
    var ev = new $.Event('remove'),
        orig = $.fn.remove;
    $.fn.remove = function () {
        $(this).trigger(ev);
        return orig.apply(this, arguments);
    };
});


// TODO: Seperate this into modules/seperate files
// Declaration of the SecondFunnel JS application
var SecondFunnel = new Backbone.Marionette.Application();
window.SecondFunnel = SecondFunnel;
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
        for (var key in data) {
            this.set(key, data[key]);
        }
    },

    getType: function () {
        // Get the content type of this tile
        return this['content-type'];
    },

    isProduct: function () {
        // TODO: This should be something else
        return this.getType() != 'youtube';
    },

    getId: function () {
        // Get the ID of this tile (for DB queries)
        return this['tile-id'];
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
    },

    removeBroken: function ( instance, image ) {
        // Assume either instance or image is an instance of an LoadingImage object
        // Remove if broken
        image = image || instance;
        if ( !image.isLoaded ) {
            $(image.img).remove();
        }
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
        args = args.length > 2? args.slice(2) : [];

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
    template: "product",

    events: {
        'click': "onClick"
    },

    initialize: function (options) {
        var data = options.model,
            template = SecondFunnel.templates[data.template];
        // Silently fall back to default template
        this.template = template || SecondFunnel.templates[this.template];

        _.bindAll(this, 'close'); 
        // If the tile model is removed, remove the DOM element
        this.listenTo(this.model, 'destroy', this.close);
    },

    render: function () {
        // Override to force the ItemView not to wrap
        this.setElement(this.template(this.model.attributes));
        this.onRender();
    },

    close: function () {
        // As it stands, since we aren't using a REST API, we don't store
        // the models anywhere so we don't need to destroy them.
        // Remove view and unbind listeners
        this.remove();
        this.unbind();
        this.views = [];
    },

    onClick: function (ev) {
        "use strict";
        var tile = this.model,
            preview = new PreviewWindow(tile);
        preview.render();
        preview.content.show(new PreviewContent(tile));
        SecondFunnel.vent.trigger("tileClicked", this);
    },

    onRender: function (ev) {
        // Listen for the image being removed from the DOM, if it is, remove
        // the View/Model to free memory
        this.$("img").on('remove', this.close);
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

        // TODO: Find a better way than this...
        _.bindAll(this, 'toggleLoading', 'layoutResults', 'updateContentStream');

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

            // TODO: refactor into youtube subview
            if (tileData.template === 'youtube') {
                tileData.thumbnail = 'http://i.ytimg.com/vi/' + tileData['original-id'] +
                    '/hqdefault.jpg';
            }

            var tile = new Tile(tileData),
                view = new TileView({model: tile});
            self.collection.add(tile);

            view.render();
            $fragment = $fragment.add(view.$el);
        });

        // TODO: Need elegant way to delete broken images w/o memory leak
        if ($tile) {
            SecondFunnel.layoutEngine.insert($fragment, $tile, this.toggleLoading);
        } else {
            SecondFunnel.layoutEngine.append($fragment, this.toggleLoading);
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
    template: function () {
        return SecondFunnel.templates['tile_preview'];
    },

    render: function () {
        // Override render to force Marionette not to wrap
        this.template = this.template();
        this.$el.html(this.template(this.attributes));
    }
});


var PreviewWindow = Backbone.Marionette.Layout.extend({
    'tagName': "div",
    'className': "previewContainer",
    'template': "#preview_container_template",// SecondFunnel.templates['preview_container'],
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
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
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
        SecondFunnel.discovery.on("pageScroll", function(args) {
            "use strict";
            args.view.getTiles();
        });
    });

    // Start the SecondFunnel app
    SecondFunnel.start(PAGES_INFO);
});
