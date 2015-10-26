'use strict'

# @module core.views

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.CategoryCollectionView::onShow = ->
        # Enable sticky category bar
        # Has an offset for the category thumbnails
        sticky = App.option("page:stickyCategories")
        if _.isString(sticky)
            if sticky == 'desktop-only' and not App.support.mobile()
                @$el.parent().waypoint('sticky',
                    offset: '-2px' # 2px borders
                )
            else if sticky == 'mobile-only' and App.support.mobile()
                @$el.parent().waypoint('sticky',
                    offset: '-2px' # 2px borders
                )
        else if _.isBoolean(sticky) and sticky
            @$el.parent().waypoint('sticky',
                offset: '-2px' # 2px borders
            )

        return @
