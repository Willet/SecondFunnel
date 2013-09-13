Tile = Backbone.Model.extend({
    url: "",
    defaults: {
        'content-type': 'product'
    },

    sync: function() {
        return false;
    }
});