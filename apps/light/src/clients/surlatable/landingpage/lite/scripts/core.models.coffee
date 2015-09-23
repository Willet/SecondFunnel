'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    _.wrapMethod(module.Product::initialize, (wrappedFunc, attributes, options) ->
        wrappedFunc.apply(@, _.toArray(arguments.slice(1)))

        # Convert price into dollars & cents
        if attributes.salePrice?
            priceParts = String(attributes.salePrice).split('.')
        else
            priceParts = String(attributes.price).split('.')
        @set(
            displayPrice:
                dollars: priceParts[0] or "0"
                cents: priceParts[1] or "00"
        )
    )
