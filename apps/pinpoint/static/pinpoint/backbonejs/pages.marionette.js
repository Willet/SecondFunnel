$(function () {
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
            _.extend(this, options);
            $elem.masonry(options || this.options).masonry('bindResize');
            this.$el = $elem;
        },

        append: function ($fragment) {
            this.$el.append($fragment).masonry('appended', $fragment);
            return this;
        },

        reload: function ($fragment) {
            this.$el.masonry('reloadItems').masonry();
            return this;
        },

        insert: function ($target, $fragment) {
            $fragment.insertAfter($target);
            this.reload();
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
        template: "#product",
        tagName: "div",
        className: "tile ",
        
        initialize: function (data) {
            var template = SecondFunnel.templates[data.template];
            _.extend(this, data);
            this.template = template || this.template;

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
        //id: SecondFunnel.getRegion('mainRegion').substring(1),
        itemView: TileView,
        intentRank: null,

        appendHtml: function (collectionView, itemView) {
            collectionView.$(":last").append(itemView.el);
        },

        initialize: function (options) {
            // Initialize IntentRank; use as a seperate module to make changes easier.
            this.intentRank = new IntentRank();
            // Black box Masonry (this will make migrating easier in the future)
            this.layoutEngine = new LayoutEngine(this.$el, options.masonry);

            _.each($('script[type="text/template"]'), function(){
                var id = $(this).attr('id');
                SecondFunnel.templates[id] = $(this).html();
            });
            this.collection = options.collection;
            // Load additional results and add them to our collection
            this.getTiles();
        },

        getTiles: function(options) {
            options = options || {};
            options.type = options.type || 'campaign';
            this.intentRank.getResults(this.createTiles, options);
            return this;
        },

        createTiles: function(data) {
            var self = this;
            // TODO: Find a way to move this logic.
            this.collection = this.collection || new TileCollection;
            _.each(data, function(tileData) {
                var tile = new Tile(tileData),
                    view = new TileView({model: tile});
                self.collection.add(new Tile(tileData));
            });
        }
    });


    // Add SecondFunnel component(s)
    SecondFunnel.addInitializer(function (options) {
        // Add our initiliazer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        SecondFunnel.discovery = new Discovery({});
    });

    // Start the SecondFunnel app
    SecondFunnel.start(PAGES_INFO);
});
