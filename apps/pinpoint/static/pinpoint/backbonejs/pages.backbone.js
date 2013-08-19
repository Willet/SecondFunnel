$(function () {
    window.SecondFunnel = {
        collections: {},
        models: {},
        views: {}
    };

    var Tile = Backbone.Model.extend({
        // Pinpoint Tiles (Blocks)
        data: {
            'caption': "",
            'content-id': 0,
            'content-type': "",
            'width': 480,
            'height': 300,
            'autoplay': 0
        },

        getType: function () {
            return this.data['type'];
        }
    });


    var TileCollection = Backbone.Collection.extend({
        // TODO: Extend this for additional usefulness 
        model: Tile,
    });
    var Tiles = new TileCollection;


    var TileView = Backbone.View.extend({
        // Defines the DOM controller for the Tiles (Blocks)
        // Various templates as defined on the user page.
        // TODO: This logic should NOT be here.
        default_templates: {
            'facebook': "product",
            'instagram': "product",
            'styld.by': "product",
            'tumblr': "product"
        },
        templates: {},
        events: {
            'click': "onTileClick",
            'mouseenter': "onHover",
            'mouseleave': "onHover"
        },

        initialize: function (options) {
            // Find all templates used in this page
            var instance = this;
            // Add the passed items to this namespace
            _.extend(this, options);
            $('script[type="text/template"]').each(function () {
                var html = $(this).html(),
                    id = $(this).attr('id');
                // Use the id of the template as the hash value
                instance.templates[id] = _.template(html, undefined,
                    { variable: 'data' });
            });
            _.each(this.default_templates, function (val, key) {
                instance.templates[key] = instance.templates[val];
            });
            // Add listeners
            this.listenTo(this.model, 'destroy', this.remove);
        },

        create: function (data) {
            var template = this.templates[data['template']];
            this.model.data = _.extend({}, this.model.data, data);

            if (template) {
                this.setElement(template(this.model.data));
                this.$el.attr('cid', this.model.cid).hide();
            } else {
                this.model.destroy();
                console.log("MISSING TEMPLATE FOR TEMPLATE: " + data['template']);
                return undefined;
            }

            return this;
        },

        onHover: function (e) {
            console.log(e.type + " on tile " + this.cid + " of type " + this.model.getType());
            return this;
        },

        getId: function () {
            return this.model.data['tile-id'];
        },

        onTileClick: function () {
            this.discovery.updateContentStream(this);
            return this;
        }
    });


    var DiscoveryArea = Backbone.View.extend({
        // DOM Controller for the Discovery Area (Main portion of the Landing Pages)
        el: $(PAGES_INFO.discoveryTarget),

        intentrank: {
            url: "http://intentrank-test.elasticbeanstalk.com/intentrank",
            templates: {
                'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
                'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
            }
        },
        loading: false,

        masonry: {
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
            }
        },

        initialize: function (options) {
            // Instantiate Listeners and Masonry
            _.extend(this, options, window.PAGES_INFO);
            this.$el.masonry(this.masonry.options);
            this.$el.masonry('bindResize');

            // Fetch initial results
            this.attachListeners().getResults('campaign');
        },

        getResults: function (intentRankType, $tile, id) {
            // Start by rendering the intentrank url
            var instance = this,
                intentrank = _.extend({'id': id}, this.intentrank, this),
                path = _.template(this.intentrank['templates'][intentRankType],
                    intentrank);
            this.toggleLoading();

            $.ajax({
                url: path,
                data: {
                    'results': 10
                },
                contentType: "json",
                dataType: 'jsonp',
                crossDomain: true,
                timeout: 5000,
                success: function (results) {
                    // If succesful in fetching, add the tiles
                    instance.addTiles(results, $tile);
                },
                error: function (jxqhr, textStatus, error) {
                    console.log("Error: " + error);
                    console.log("Status: " + textStatus);
                    instance.toggleLoading();
                }
            });
        },

        addTiles: function (data, $tile) {
            var $fragment = $(),
                instance = this;

            for (var i = 0; i < data.length && i < 10; ++i) {
                // Only load up to 10 tiles at time
                var el = this.add(data[i]);
                // If el is not defined, the block could not be generated,
                // continue.
                if (el) {
                    $fragment = $fragment.add(el);
                }
            }

            // Add our fragments and let masonry know to lay them on
            if ($tile) {
                $fragment.insertAfter($tile);
            } else {
                $fragment.appendTo(this.$el);
            }
            this.$el.masonry('reloadItems');
            return this.imagesLoading($fragment);
        },

        imagesLoading: function ($images) {
            var instance = this;
            imagesLoaded($images).on('always', function (imgLoad) {
                if (imgLoad.hasAnyBroken) {
                    // If there are any broken images, remove them
                    // before continuing
                    _.each(imgLoad.images, function (image) {
                        if (!image.isLoaded) {
                            var cid = $(image.img).parent('.tile').attr('cid'),
                                model = instance.collection._byId[cid];
                            instance.collection.remove(model);
                            model.destroy();
                        }
                    });
                }
                $(imgLoad.elements).show();
                instance.toggleLoading().$el.masonry();
            });
            return this;
        },

        attachListeners: function () {
            _.bindAll(this, 'pageScroll');
            $(window).scroll(this.pageScroll);
            return this;
        },

        add: function (data) {
            // Create the view and return the added
            // elements.
            var view = new TileView({model: new Tile, discovery: this });
            view = view.create(data);

            // Check for error
            if (!view) {
                return undefined;
            }
            // View rendered, return fragement
            this.collection.add(view.model);
            return view.el;
        },

        updateContentStream: function (view) {
            if (!this.loading) {
                this.getResults('content', view.$el, view.getId());
            }
            return this;
        },

        toggleLoading: function () {
            this.loading = !this.loading;
            return this;
        },

        pageScroll: function () {
            var offsetY = $(window).scrollTop() + $(window).height(),
                documentOffsetY = $(document).height();

            // Only update on pageScrolls within a certain threshold of the end of the page
            if (!this.loading && documentOffsetY - offsetY <= 150) {
                this.getResults('campaign', this.$el.children().last());
            }
            return this;
        }

    });

    var App = new DiscoveryArea({
        collection: Tiles
    });
});
