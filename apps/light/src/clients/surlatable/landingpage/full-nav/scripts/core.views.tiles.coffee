'use strict'

# @module core.views.tiles

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.BannerTileView::onClick = ->
            App.vent.trigger('tracking:product:buyClick', @model)
            if @model.get("redirectUrl")
                App.utils.openUrl @model.get("redirectUrl")
            return
