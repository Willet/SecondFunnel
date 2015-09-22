'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    coreProductInitialize = module.Product::initialize
    module.Product::initialize = (attributes, options) ->
        coreProductInitialize.apply(@, arguments)
        # Convert price into dollars & cents
        priceParts = String(attributes.price).split('.')
        sale_string = ""
        on_sale = attributes.salePrice? and attributes.salePrice < attributes.price
        if on_sale
            sale_string = attributes.price
            priceParts = String(attributes.salePrice).split('.')
        @set(
            displayPrice:
                dollars: priceParts[0] or "0"
                cents: priceParts[1] or "00"
            saleString: sale_string
            sale: on_sale
        )
