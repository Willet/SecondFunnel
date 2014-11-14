'use strict';

$ = require('jquery')
_ = require('underscore')
Backbone = require('backbone')
Marionette = require('backbone.marionette')

module.exports = (module, App) ->
    ###
    A container tile that has no onclick or onhover

    @constructor
    @type {Layout}
    ###
    class module.ContainerTileView extends module.TileView
        onHover: (ev) ->
            return

        onClick: (ev) ->
            return

    class module.GroovesharkTileView extends module.ContainerTileView
        template: "#grooveshark_tile_template"

        onShow: (ev) ->
            App.vent.once 'layoutCompleted', ->
                # Move Grooveshark overlay onto the tile position
                position = $('.grooveshark-placeholder').offset()
                if position?
                    $('.grooveshark-tile-overlay').css(
                        'top': position.top
                        'left': position.left
                    )

        onClose: (ev) ->
            # Move Grooveshark overlay off of the screen
            $('.grooveshark-tile-overlay').css('left', '-10000px')

    class module.GiftcardTileView extends module.ContainerTileView
        template: "#giftcard_tile_template"

        onClick: (ev) ->
            tile = @model
            window.open tile.get("redirect-url"), "_blank"
            return

    ###
    Mobile categories for Aero behave differently than desktop

    @constructor
    @type {Layout}
    ###
    class module.MobileCategoryView extends Marionette.ItemView
        tagName: "div"
        className: "category"

        template: "#mobile_category_template"
        templates: ->
            templateRules = [
                "#<%= options.store.slug %>_mobile_category_template"
                "#mobile_category_template"
            ]
            templateRules

        events:
            click: (event) ->
                view = @
                $el = view.$el
                category = view.model.get("name")
                nofilter = view.model.get("nofilter")
                eventTarget = $(event.target)

                # switch to the selected category
                # if it has changed
                if not $el.hasClass("selected")
                    $el.siblings().each () ->
                        self = $(@)
                        self.removeClass 'selected'

                    $el.addClass "selected"

                    if view.model.get("desktopHeroImage") and view.model.get("mobileHeroImage") and App.layoutEngine
                        App.heroArea.show(new App.core.HeroAreaView(
                            "desktopHeroImage": view.model.get "desktopHeroImage"
                            "mobileHeroImage": view.model.get "mobileHeroImage"
                        ))

                    App.navigate(category,
                        trigger: true
                    )

    ###
    A collection of Categories to display on mobile.

    @constrcutor
    @type {CollectionView}
    ###
    class module.MobileCategoryCollectionView extends Marionette.CollectionView
        tagName: "div"
        className: "category-area"

        itemView: module.MobileCategoryView

        initialize: (options) ->
            categories = _.map(App.option("page:mobileCategories", []), (category) ->
                if typeof(category) is "string"
                    category = {name: category}
                category
            )
            if categories.length > 0

                # This specifies that there should be a home button, by default, this is true.
                if App.option("categoryHome")
                    if App.option("categoryHome").length
                        home = App.option("categoryHome")
                    else
                        home = "home"
                    categories.unshift {name: home}

                @collection = new module.CategoryCollection(categories, model: module.Category)
            else
                @collection = new module.CategoryCollection([], model: module.Category)

            return @

        onRender: ->
            @$el.children().eq(0).trigger 'click'

    return