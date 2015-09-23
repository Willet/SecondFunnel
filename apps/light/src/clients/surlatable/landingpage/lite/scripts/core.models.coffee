'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    coreProductInitialize = module.Product::initialize
    module.Product::initialize = (attributes, options) ->
        coreProductInitialize.apply(@, arguments)
        # Convert price into dollars & cents
        if @get('salePrice')?
            priceParts = String(@get('salePrice')).split('.')
        else
            priceParts = String(@get('price')).split('.')
        @set(
            displayPrice:
                dollars: priceParts[0] or "0"
                cents: priceParts[1] or "00"
        )
