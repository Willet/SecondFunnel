'use strict'

# @module core.views.tiles

module.exports = (module, App, Backbone, Marionette, $, _) ->
    class module.RecipeTileView extends module.ImageTileView
        # Recipe tiles behave exactly like Image Tiles, just look different
        template: "#recipe_tile_template"
