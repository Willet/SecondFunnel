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
                value = String(attributes.price).split('.')[0] # drop the decimal
                priceParts = String(attributes.salePrice).split('.')
            @set(
                displayPrice:
                    dollars: priceParts[0] or "0"
                    cents: priceParts[1] or "00"
                value: value or "0"
                sale: onSale
                currency: "$"
            )
    )

