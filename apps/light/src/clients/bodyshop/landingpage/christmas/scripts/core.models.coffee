'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.Product::initialize = _.wrap(
        module.Product::initialize,
        (initialize, attributes, options) ->
            initialize.call(@, attributes, options)

            # Convert price into dollars & cents
            priceParts = String(attributes.price).split('.')
            saleString = ""
            savePercent = 0
            onSale = attributes.salePrice? and parseInt(attributes.salePrice) < parseInt(attributes.price)
            if onSale
                saleString = attributes.price
                priceParts = String(attributes.salePrice).split('.')
                # round percent saved to nearest 5% like slt main site
                savePercent = Math.floor(20 * (1 - (attributes.salePrice / attributes.price))) * 5
            @set(
                displayPrice:
                    dollars: priceParts[0] or "0"
                    cents: priceParts[1] or "00"
                saleString: saleString
                sale: onSale
                savePercent: savePercent
                currency: "$"
            )
    )

    module.ProductTile::options =
        showThumbnails: false
        previewFeed: true

