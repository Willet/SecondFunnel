'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    coreProductInitialize = module.Product::initialize
    module.Product::initialize = (attributes, options) ->
        coreProductInitialize.apply(@, arguments)
        # Convert price into dollars & cents
        priceParts = String(attributes.price).split('.')
        saleString = ""
        savePercent = 0
        on_sale = attributes.salePrice? and attributes.salePrice < attributes.price
        if on_sale
            saleString = attributes.price
            priceParts = String(attributes.salePrice).split('.')
            savePercent = Math.round(20 * (1 - (attributes.salePrice / attributes.price))) * 5
        @set(
            displayPrice:
                dollars: priceParts[0] or "0"
                cents: priceParts[1] or "00"
            saleString: saleString
            sale: on_sale
            savePercent: savePercent
        )
