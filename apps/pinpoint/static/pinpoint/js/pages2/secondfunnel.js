Tile = Backbone.Model.extend({
    url: "",
    defaults: {
        'content-type': 'product'
    },

    sync: function() {
        return false;
    }
});

TileCollection = Backbone.Collection.extend({
    url: "http://localhost:8000/intentrank/store/nativeshoes/campaign/32/getresults",
    model: Tile,
    parse: function (response) {
        return response;
    },
    fetch: function(options) {
        options = options || {};
        options.results = 10;
        // TODO: Enable option for overriding; sinon can't do jsonp with fakeserver
        options.dataType =  options.dataType || 'jsonp';
        options.remove = false;  // don't remove things
        options.merge = false; // don't merge existing
        options.callbackParameter = 'fn';

        return Backbone.Collection.prototype.fetch.call(this, options);
    }
});