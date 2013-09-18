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
        regions: {
            'socialButtons': '.social-buttons',
            'tapIndicator': '.tap-indicator',
            'loadingIndicator': '.loading-indicator'
        },

        // Fire an event when something happens
        // TODO: Is this how we want to handle *all* events?
        //triggers: {},

        events: function() {
            return {
                'click': 'activate'
            }
        },

        activate: function() {
            // TODO: Do something, likely preview
            return this;
        },

        render: function() {
            try {
                Backbone.Marionette.Layout.prototype.render.call(this);
            } catch (e) {
                // TODO: Do *more* something on error
                this.close();
            }
        }
    });
});