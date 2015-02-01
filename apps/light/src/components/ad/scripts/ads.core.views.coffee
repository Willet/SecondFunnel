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

    ###
    Reorder landscape tiles to only appear after a multiple-of-2
    products has appeared, allowing gapless layouts in two-col ads.

    This method requires state to be maintained in the tempTiles variable;
    it is not idempotent.

    @param {object} resp an array of tile json
    @returns {object} an array of tile json
    ###
    module.MasonryFeedView.prototype.reorderTiles = (resp) ->
        if @currentNonFilledRows is undefined
            @currentNonFilledRows = []
        columnCount = 2 # the number of columns (should get from masonry...)
        respBuilder = [] # new resp after filter(s)

        orientation_column_widths = { # column(s) wide
            "portrait": 1
            "landscape": 2
        }

        # default to portrait
        _.each resp, (tile) ->
            unless tile.orientation
                tile.orientation = "portrait"

        # only do this for iframe versions
        #unless App.utils.isIframe()
        #    return resp

        _.each resp, (tile) =>
            tileAdded = false
            tileColWidth = orientation_column_widths[tile.orientation]

            # tile is an entire row, can just add it right away
            if tileColWidth == columnCount
                respBuilder.push(tile)
                return

            # check existing non-filled rows
            @currentNonFilledRows = _.filter @currentNonFilledRows, (row) ->
                return true if tileAdded
                rowColWidth = _.reduce(row, ((memo, tile) -> memo + orientation_column_widths[tile.orientation]), 0)
                if rowColWidth + tileColWidth <= columnCount
                    # fits in the row, add it to the row
                    row.push tile

                if rowColWidth + tileColWidth == columnCount
                    # row is now full, "remove" from nonfilled rows and add it to response
                    _.each(row, (tile) -> respBuilder.push(tile))
                    tileAdded = true
                    return false # filter it out
                return true # let the row remain

            unless tileAdded
                # couldn't find place for tile, add as a new row
                newRow = [tile]
                @currentNonFilledRows.push(newRow)
        return respBuilder
