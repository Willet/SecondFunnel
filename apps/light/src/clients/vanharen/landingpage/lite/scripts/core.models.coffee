'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.Product::initialize = _.wrap(
        module.Product::initialize,
        (initialize, attributes, options) ->
            initialize.call(@, attributes, options)

            # Convert price into euros & cents
            onSale = attributes.salePrice? and parseInt(attributes.salePrice) < parseInt(attributes.price)
            if onSale
                saleString = attributes.price
                priceParts = String(attributes.salePrice).split('.')
            else
                saleString: ""
                priceParts = String(attributes.price).split('.')
            @set(
                displayPrice:
                    euros: priceParts[0] or "0"
                    cents: priceParts[1] or "00"
                oldPrice: saleString
                sale: onSale
            )
    )