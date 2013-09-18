// Should we use Marionette.extend instead?
Marionette.Application.prototype.getOption = function(optionName) {
    var value = Marionette.getOption(this, optionName);

    // TODO: Do we want it to fallback to the `defaults` object, or
    // a value that we pass in (e.g. a second parameter)?
    if (_.isUndefined(value)) {
        value = this.defaults[optionName];
    }

    return value;
}

Page = new Backbone.Marionette.Application();

Page.defaults = {
    LOG: {QUIET: 0, ERROR: 1, WARNING: 2, LOG: 3, VERBOSE: 4, ALL: 5}
};

Page.addRegions({
    'heroArea': '#hero-area',
    'discoveryArea': '#discovery-area'
});

Page.addInitializer(function(options) {
    // TODO: Replace with actually rendering the correct views.
    this.heroArea.show(new Backbone.View());
    this.discoveryArea.show(new Backbone.View());
});

Page.addInitializer(function(options) {
    var preloadedModels = [];
    options = options || {};

    // TODO: Change name as necessary
    options.models = options.models || [];

    // TODO: Change to make the default number configurable
    preloadedModels = _.first(options.models, 4);

    this.tiles = new TileCollection();
    this.tiles.reset(preloadedModels);
});

// TODO: Should this always be last?
Page.addInitializer(function(options) {
    _.extend(this, options);
});