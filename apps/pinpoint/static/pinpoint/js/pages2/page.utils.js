Page.module("utils", function(utils, page, B, M, $, _) {
    utils.ItemView = M.ItemView.extend({
        render: function() {
            try {
                Backbone.Marionette.ItemView.prototype.render.call(this);
            } catch (e) {
                // TODO: Do *more* something on error
                this.close();
            }
            return this;
        }
    })
});