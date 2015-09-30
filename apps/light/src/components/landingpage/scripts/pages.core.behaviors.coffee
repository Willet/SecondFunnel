"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->
    class module.childProductViewTracking extends Marionette.Behavior
        formatTrackingData: (childView) ->
            data = @model.toJSON
            data.product = childView.model

        childEvents:
            'click:image': (childView) ->
                App.vent.trigger("tracking:product:imageView", formatTrackingData(childView))
            'click:moreInfo': (childView) ->
                App.vent.trigger("tracking:product:moreInfoClick", formatTrackingData(childView))
            'click:findStore': (childView) ->
                App.vent.trigger("tracking:product:findStoreClick", formatTrackingData(childView))
            'click:buy': (childView) ->
                App.vent.trigger("tracking:product:buyClick", formatTrackingData(childView))
