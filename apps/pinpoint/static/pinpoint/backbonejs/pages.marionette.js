// Declaration of the SecondFunnel JS application
var SecondFunnel = new Backbone.Marionette.Application();
// Custom event trigger/listener
SecondFunnel.vent = _.extend({}, Backbone.Events);
SecondFunnel.templates = {};
// Add layout

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
    loading: false,
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
        console.log(this.$el);
        this.$el.append($fragment).masonry('appended', $fragment);
        return this.imagesLoaded($fragment, callback);
    },
    
    reload: function ($fragment) {
        this.$el.masonry('reloadItems').masonry();
        return this;
    },
    
    insert: function ($target, $fragment, callback) {
        $fragment.insertAfter($target);
        return this.imagesLoaded($fragment, callback);
    },
    
    imagesLoaded: function($fragment, callback) {
        // Compiles a list of the broken image srcs and returns them
        // How we handle this is up to the Discovery module
        var self = this,
            broken = [];
        imagesLoaded($fragment).on('always', function( imgLoad ) {
            if (imgLoad.hasAnyBroken) {
                broken = _.filter(imgLoad.images, function (img) { return !img.isLoaded; });
                broken = _.map(broken, function () { return this.img; });
            }
            callback(broken);
            $(imgLoad.elements).show();
            self.reload();
        });
    },
    
    isLoading: function () {
        return this.loading;
    },
    
    toggleLoading: function () {
        this.loading = !this.loading;
        return this;
    }
});

var IntentRank = Backbone.Model.extend({
    // intentRank module
    loading: false,
    base: "http://intentrank-test.elasticbeanstalk.com/intentrank",
    templates: {
            'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
        'content': "<%=url%></store/<%=store.name%>/campaign/<%=campaign%>/<%=id%>/getresults"
    },
    store: PAGES_INFO.store,
    campaign: PAGES_INFO.campaign,
    
    getResults: function (callback, options) {
        if (!this.isLoading()) {
            var self = this,
                uri = _.template(this.templates[options.type], _.extend({}, options, this, {
                    'url': this.base
                }));
            this.toggleLoading();
            
            $.ajax({
                url: uri,
                data: {
                    'results': 10, // TODO: Should be calculated somehow
                },
                contentType: "json",
                dataType: 'jsonp',
                timeout: 5000,
                success: function(results) {
                    self.toggleLoading();
                    return callback(results);
                },
                error: function(jxqhr, textStatus, error) {
                    self.toggleLoading();
                    return callback([]);
                }
            });
        }
    },
    
    toggleLoading: function () {
        this.loading = !this.loading;
        return this;
    },
    
    isLoading: function () {
        return this.loading;
    }
    
});

var TileCollection = Backbone.Collection.extend({
    // Our TileCollection manages ALL the tiles on the page.
    model: Tile,
    loading: false,
    totalItems: null,
    
    initialize: function (arrayOfData) {
        // Our TileCollection starts by rendering several Tiles using the
        // data it is passed.
        for (var data in arrayOfData) {
                // Generate Tile
        }
    }
});

var TileView = Backbone.Marionette.ItemView.extend({
    // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
    template: "product",
    tagName: "div",
    className: "tile ",
    
    initialize: function (options) {
        var data = options.model,
            template = SecondFunnel.templates[data.template];
        this.template = template || SecondFunnel.templates[this.template];
        
        console.log(SecondFunnel.templates);
        if (!template) {
            console.log("No template found for " + data.template + ". Falling back to #product.");
        }
        this.className += data['content-type'];
        
        // If the tile model is removed, remove the DOM element
        this.listenTo(this.model, 'destroy', this.remove);
    }
});

var Discovery = Backbone.Marionette.CompositeView.extend({
    // Manages the HTML/View of ALL the tiles on the page (our discovery area)
    // tagName: "div"
    id: PAGES_INFO.discoveryTarget,
    itemView: TileView,
    intentRank: null,
    collection: null,
    layoutEngine: null,
    
    appendHtml: function (collectionView, itemView) {
        collectionView.$(":last").append(itemView.el);
    },
    
    initialize: function (options) {
        // Initialize IntentRank; use as a seperate module to make changes easier.
        SecondFunnel.intentRank = new IntentRank;
        // Black box Masonry (this will make migrating easier in the future)
        SecondFunnel.layoutEngine = new LayoutEngine(this.$el, options.masonry);
        
        $('script[type="text/template"]').each(function(){
            var id = $(this).attr('id');
            SecondFunnel.templates[id] = _.template($(this).html(), undefined, { variable: 'data' });
            });
        this.collection = options.collection || new TileCollection;
        this.$el = $(this.id);
        // Load additional results and add them to our collection
        this.getTiles();
    },
    
    getTiles: function(options) {
        options = options || {};
        options.type = options.type || 'campaign';
        SecondFunnel.intentRank.getResults(_.partial(this.createTiles, this), options);
        return this;
    },
    
    createTiles: function(self, data, $tile) {
        var start = self.collection.length,
            $fragment = $();
        
        _.each(data, function(tileData) {
            // Create the new tiles using the data
            var tile = new Tile(tileData),
                    view = new TileView({model: tile});
            self.collection.add(new Tile(tileData));
            view.render();
            $fragment = $fragment.add(view.$el);
        });
        
        var remove = _.partial(self.removeBroken, start);
        if ($tile) {
            SecondFunnel.layoutEngine.insert($fragment, $tile, remove);
        } else {
            SecondFunnel.layoutEngine.append($fragment, remove);
            }
        return this;
    },
    
    removeBroken: function(index, broken) {
        // Removes the broken images alongside their model and views
        console.log(broken);
        return this;
    },
    
    toggleLoading: function () {
        SecondFunnel.layoutEngine.toggleLoading();
        return this;
    },
    
    isLoading: function () {
        return SecondFunnel.layoutEngine.isLoading();
    }
});


$(function () {
    // Add SecondFunnel component(s)
    SecondFunnel.addInitializer(function (options) {
        // Add our initiliazer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        SecondFunnel.discovery = new Discovery({});
    });
    
    // Start the SecondFunnel app
    SecondFunnel.start(PAGES_INFO);
});
