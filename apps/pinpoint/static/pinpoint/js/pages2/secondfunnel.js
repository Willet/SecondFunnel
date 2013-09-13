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
//    parse: function (response) {
//        // take some actions when
//        return response;
//    }
    fetch: function(options) {
        options = options || {};
        options.results = 10;
        options.dataType =  'jsonp';
        options.remove = false;  // don't remove things
        options.merge = false; // don't merge existing

        return Backbone.Collection.prototype.fetch.call(this, options);
    }
});