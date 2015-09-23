'use strict'

# @module core.models

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.Product::initialize = _.wrap(
        module.Product::initialize,
        (initialize, attributes, options) ->
            initialize.call(@, attributes, options)

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
