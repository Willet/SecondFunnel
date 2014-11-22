'use strict';

$ = require('jquery')
_ = require('underscore')
Backbone = require('backbone')
Marionette = require('backbone.marionette')

module.exports = (module, App) ->

    class module.BannerTileView extends module.TileView
        template: "#banner_tile_template"

        onClick: (ev) ->
            url = App.utils.generateAdClickUrl( @model.get 'url' )
            window.open url, "_self"
            return
