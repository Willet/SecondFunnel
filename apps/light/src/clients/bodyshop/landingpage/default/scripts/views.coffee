'use strict';

module.exports = (module, App, Backbone, Marionette, $, _) ->

    class module.BannerTileView extends module.TileView
        template: "#banner_tile_template"

        onClick: (ev) ->
            url = App.utils.addUrlTrackingParameters( @model.get 'url' )
            window.open url, App.utils.openInWindow()
            return false # stop propagation
