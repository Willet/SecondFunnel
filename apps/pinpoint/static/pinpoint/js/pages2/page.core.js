Page.module("core", function(core, page, B, M, $, _) {
    // Models
    core.Tile = Backbone.Model.extend({
        idAttribute: 'db-id', // TODO: Replace with proper id
        defaults: {
            'content-type': 'product'
        },

        sync: function() {
            return false;
        }
    });

    // Collections
    core.TileCollection = Backbone.Collection.extend({
        url: "http://localhost:8000/intentrank/store/nativeshoes/campaign/32/getresults",
        model: core.Tile,

        add: function (model) {
            Backbone.Collection.prototype.add.call(this, model);
        },

        set: function (models, options) {
            // If the element already exists, fire an add event anyway
            // Alternatively, we could dupe the model via .toJSON();

            // Need to check for duplicates before we call set, otherwise all results
            // will be duplicates.
            var i, model, existing, duplicates = [];
            for(i = 0; i < models.length; i++) {
                if (!(model = this._prepareModel(models[i], options))) continue;

                // Of COURSE they already exist!
                if (existing = this.get(model)) {
                    duplicates.push(existing);
                }
            }

            Backbone.Collection.prototype.set.call(this, models, options);

            // After Backbone has done its stuff, fire the necessary 'add' events
            // Inspired by Backbone's existing methods `set` method
            for(i = 0; i < duplicates.length; i++) {
                (existing = duplicates[i]).trigger('add', existing, this, options);
            }
        },

        parse: function (response) {
            return response;
        },

        fetch: function(options) {
            options = options || {};
            options.results = 10;
            // TODO: Enable option for overriding; sinon can't do jsonp with fakeserver
            options.dataType =  options.dataType || 'jsonp';
            options.remove = false;  // don't remove things
            options.callbackParameter = 'fn';

            return Backbone.Collection.prototype.fetch.call(this, options);
        }
    });

    // Views
    core.TileView = Backbone.Marionette.Layout.extend({
        template: '#willet-tile-view',
        className: 'tile',

        defaults: {
            loading: true
        },

        // maybe later, just have a stack of indicators?
        regions: {
            'tapIndicator'    : '.tap-region',
            'buttonsIndicator': '.buttons-region',
            'loadingIndicator': '.loading-region'
        },

        templateHelpers: function() {
            var view = this;
            return {
                tile: view.model.toJSON()
            }
        },

        // Fire an event when something happens
        // TODO: Is this how we want to handle *all* events?
        //triggers: {},

        events: function() {
            var events = {
                'click': 'activate'
            };

            if (!page.mobile) {
                events.mouseenter = 'mouseenter';
                events.mouseleave = 'mouseleave';
            }

            return events;
        },

        initialize: function (options) {
            options = options || {};

            // Should loading indicator know about the model?
            // Probably; its going to be sizing things.

            // Does loading indicator know about its parent?

            this.loading = options.loading || this.defaults.loading;
            this.indicators = {
                'loading': options.loadingIndicator || new core.LoadingIndicator,
                'tap': options.tapIndicator || new core.TapIndicator,
                'buttons': options.buttonsIndicator || new core.ButtonsIndicator
            };
        },

        activate: function() {
            page.vent.trigger('preview', page, this.model);
            // Why do I need to pass along the page?
            page.vent.trigger('fetch:related', page);
            return this;
        },

        mouseenter: function() {
            this.buttonsIndicator.show(this.indicators.buttons);
        },

        mouseleave: function() {
            this.buttonsIndicator.reset();
        },

        render: function() {
            var self = this;
            try {
                Backbone.Marionette.Layout.prototype.render.call(this);

                // TODO: Should this be in 'after:render'? Does that exist?
                // TODO: Don't do things like this
                this.loadingIndicator.show(this.indicators.loading);

                // TODO: Move this down to tapIndicator?
                if (page.mobile) {
                    this.tapIndicator.show(this.indicators.tap);
                } else {
                    this.$el.addClass('mouse-hint');
                };

                this.$el.imagesLoaded(function() {
                    self.triggerMethod('loaded');
                });
            } catch (e) {
                // TODO: Do *more* something on error
                this.close();
            }
            return this;
        },

        setLoading: function(state) {
            this.loading = !!state;

            // Why wouldn't the loading indicator exist?

            if (this.loadingIndicator) {
                this.loadingIndicator.reset();
            }
            return this;
        },

        onLoaded: function() {
            this.setLoading(false);
            // What else to do when loaded?
        }
    });

    core.VideoView = core.TileView.extend({
        className: 'tile video'
    });

    // TODO: Fill tile with proper width / height of image
    // Also, BG color
    core.LoadingIndicator = Page.utils.ItemView.extend({
        'tagName': 'div',
        'className': 'loading',
        'template': '#willet-tile-loading'
    });

    core.TapIndicator = Page.utils.ItemView.extend({
        'tagName': 'div',
        'className': 'tap',
        'template': '#willet-tile-tap'
    });

    core.ButtonsIndicator = Page.utils.ItemView.extend({
        'tagName': 'div',
        'className': 'buttons',
        'template': '#willet-buttons'
    });

    core.HeroAreaView = Page.utils.ItemView.extend({
        'tagName': 'div',
        'template': '#willet-hero-area'
    });

    core.Preview = Page.utils.ItemView.extend({
        'tagName': 'div',
        'template': '#willet-preview',
        'id': 'preview-window',
        events: {
            'click .mask': 'onMaskClick' // bad name
        },
        onMaskClick: function() {
            // TODO: Should this just close itself instead?
            page.vent.trigger('preview:close', page);
        },
        onBeforeClose: function() {
            this.$el.hide();
        },
        onShow: function() {
            this.$el.show();
        }
    });

    core.DiscoveryArea = Backbone.Marionette.CollectionView.extend({
        // Will render some view when there are no results...
        'emptyView': core.LoadingIndicator,
        'itemView': core.TileView,
        getItemView: function(item) {
            var type = item.get('template'),
                cls;

            switch(type) {
                case 'video':
                    cls = core.VideoView;
                    break;
                default:
                    cls = core.TileView;
                    break;
            }

            return cls;
        },
        initialize: function (options) {
            this.layoutManager = new Masonry(
                this.el, {
                    itemSelector: '.tile',
                    columnWidth: 202
                }
            );
        },
        onAfterItemAdded: function (itemView) {
            this.layoutManager.appended(itemView.$el);

            // TODO: Is there an event that fires after
            // we have finished with all items?
            this.layoutManager.layout();
        }
    });
});