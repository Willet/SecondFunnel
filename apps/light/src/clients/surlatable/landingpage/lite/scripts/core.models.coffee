'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    _.wrapMethod(module.Product::initialize, (wrappedFunc, attributes, options) ->
        wrappedFunc.apply(@, _.toArray(arguments.slice(1)))

        # Convert price into dollars & cents
        if attributes.sale_price?
            price_parts = String(attributes.sale_price).split('.')
        else
            price_parts = String(attributes.price).split('.')
        @set(
            displayPrice:
                dollars: price_parts[0] or "0"
                cents: price_parts[1] or "00"
        )
    )
