'use strict';

module.exports = (module, App, Backbone, Marionette, $, _) ->

	module.ImageTileView.prototype.onClick = ->
		if App.option("page:openTileInPopup", false)
            if App.option("tilePopupUrl")
                # override for ad units whose tiles point to our pages
                url = App.option("tilePopupUrl")
            else if tile.get("template") is "product"
                url = tile.get("url")
            else if tile.get("tagged-products") and tile.get("tagged-products").length
                url = tile.get("tagged-products")[0].url
            # missing schema
            if url.indexOf("http") is -1 and App.store.get("slug")
                url = "http://" + App.store.get("slug") + ".secondfunnel.com" + url

            if url and url.length
                sku = tile.get("sku")
                tileId = tile.get("tile-id")

                if App.option('hashPopupRedirect', false) and tileId
                    url += "#" + tileId
                else
                    if tileId
                        url += "/tile/" + tileId
                    else if sku
                        url += "/sku/" + sku
                App.utils.openUrl url
            return  

    class module.BannerTileView extends module.TileView
        template: "#banner_tile_template"

        onClick: (ev) ->
            App.utils.openUrl @model.get('url')
            return false # stop propagation
