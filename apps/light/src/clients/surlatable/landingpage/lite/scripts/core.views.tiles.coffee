'use strict'

# @module core.views.tiles

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.BannerTileView::onClick = ->
            App.vent.trigger('tracking:product:buyClick', @model)
            if @model.get("redirect-url")
                App.utils.openUrl @model.get("redirect-url")
            return

    class module.RecipeTileView extends module.ImageTileView
        # Recipe tiles behave exactly like Image Tiles, just look different
        template: "#recipe_tile_template"
