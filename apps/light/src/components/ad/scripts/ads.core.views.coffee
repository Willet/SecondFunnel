'use strict';

module.exports = (module, App, Backbone, Marionette, $, _) ->

	# TODO !!!
	#module.ImageTileView.prototype.onClick = ->
		#  

    class module.BannerTileView extends module.TileView
        template: "#banner_tile_template"

        onClick: (ev) ->
            url = App.utils.generateAdClickUrl( @model.get 'url' )
            window.open url, "_blank"
            return false # stop propagation
