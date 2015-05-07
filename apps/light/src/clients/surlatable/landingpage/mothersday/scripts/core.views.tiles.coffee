'use strict'

# @module core.views.tiles

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.BannerTile::onClick = ->
            App.vent.trigger('tracking:product:buyClick', @model)
            if @model.get("redirect-url")
                App.utils.openUrl @model.get("redirect-url")
            else
                super
            return