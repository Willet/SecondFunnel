"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->
    class module.childProductViewTracking extends Marionette.Behavior
        # Note: the childEvents hash is not supported in behaviors (RAGE!)
        #       Once it is fixed, you can use this beautiful clean hash
        #       See: https://github.com/marionettejs/backbone.marionette/issues/2776
        formatTrackingData: (childView) ->
            return _.extend({}, @view.model.toJSON, product: childView.model)

        childEvents:
            "click:image": (childView) ->
                App.vent.trigger("tracking:product:imageView", formatTrackingData(childView))
            "click:moreInfo": (childView) ->
                App.vent.trigger("tracking:product:moreInfoClick", formatTrackingData(childView))
            "click:findStore": (childView) ->
                App.vent.trigger("tracking:product:findStoreClick", formatTrackingData(childView))
            "click:buy": (childView) ->
                App.vent.trigger("tracking:product:buyClick", formatTrackingData(childView))
