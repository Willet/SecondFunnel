'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    coreProductInitialize = module.Product::initialize
    module.Product::initialize = (attributes, options) ->
        coreProductInitialize.apply(@, arguments)
        # Convert price into dollars & cents
        price_parts = String(attributes.price).split('.')
        sale_string = ""
        on_sale = attributes.sale_price? and attributes.sale_price < attributes.price
        if on_sale
            sale_string = attributes.price
            price_parts = String(attributes.sale_price).split('.')
        @set(
            displayPrice:
                dollars: price_parts[0] or "0"
                cents: price_parts[1] or "00"
            saleString: sale_string
            sale: on_sale
        )
