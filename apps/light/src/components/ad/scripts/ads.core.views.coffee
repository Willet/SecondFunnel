'use strict';

module.exports = (module, App, Backbone, Marionette, $, _) ->

	module.TileView.prototype.onClick = ->
		# Build base url
        if App.option("ad:tilePopupUrl")
            # Option masking url for page associated with this ad
            url = App.option("ad:tilePopupUrl")
        # missing schema
        if url.indexOf("http") is -1 and App.store.get("slug") and App.store.get("default_page_name")
            url = "http://#{App.store.get('slug')}.secondfunnel.com/#{App.store.get('default_page_name')}"

        # Append tile specific id and redirect
        if url and url.length
            sku = tile.get("sku")
            tileId = tile.get("tile-id")

           	# option to link to preview pop-up over feed
            if App.option('ad:tiles:openTilesInPreview', false) and tileId
                url += "#preview/#{tileId}"
            else
                if tileId
                    url += "/tile/#{tileId}"
                else if sku
                    url += "/sku/#{sku}"
            App.utils.openUrl url
        return


    class module.ProductTileView extends module.TileView
        template: "#product_tile_template"

        onClick: ->
            if App.option('ad:tiles:openProductTileInPDP')
                App.utils.openUrl @model.get("url")
            else
                super
            return
