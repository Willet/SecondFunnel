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
    class module.MobileCategoryView extends module.CategoryView
        tagName: "div"
        className: "category"

        template: "#category_template"
        templates: ->
            templateRules = [
                "#<%= options.store.slug %>_category_template"
                "#category_template"
            ]
            templateRules

        events:
            'click .sub-category': (event) ->
                $target = $(event.target)
                category = $target.data 'name'
                $el = @$el
                
                if category
                    unless $el.hasClass 'selected' and $target.hasClass 'selected' and not $target.siblings().hasClass 'selected'
                        # switch to selected sub-category
                        $target.addClass 'selected'
                        $target.siblings().removeClass 'selected'
                        # switch to selected category if not already
                        unless $el.hasClass 'selected'
                            $el.addClass 'selected'
                            # remove selected from other categories
                            $el.siblings().each () ->
                                self = $(@)
                                self.removeClass 'selected'
                                self.find('.sub-category').removeClass 'selected'

                        # switch hero image *of category*
                        if @model.get("desktopHeroImage") and @model.get("mobileHeroImage") and App.layoutEngine
                            App.heroArea.show(new App.core.HeroAreaView(
                                "desktopHeroImage": @model.get "desktopHeroImage"
                                "mobileHeroImage": @model.get "mobileHeroImage"
                            ))

                        App.navigate(category,
                            trigger: true
                        )
                else if App.option('debug', false)
                    console.error "Attempted to switch to sub-category '#{category}' which does not exist."
                return false # stop propogation

            'click': (event) ->
                category = @model.get("name")
                $el = @$el
                subcategories = $el.find '.sub-category'

                if category
                    unless $el.hasClass 'selected' and not subcategories.hasClass 'selected'
                        # remove selected from child sub-categories
                        subcategories.removeClass 'selected'
                        # switch to the selected category if it has changed
                        unless $el.hasClass 'selected'
                            $el.addClass 'selected'
                            # remove selected from other categories
                            $el.siblings().each () ->
                                self = $(@)
                                self.removeClass 'selected'
                                self.find('.sub-category').removeClass 'selected'

                        # switch hero image *of category*
                        if @model.get("desktopHeroImage") and @model.get("mobileHeroImage") and App.layoutEngine
                            App.heroArea.show(new App.core.HeroAreaView(
                                "desktopHeroImage": @model.get "desktopHeroImage"
                                "mobileHeroImage": @model.get "mobileHeroImage"
                            ))

                        App.navigate(category,
                            trigger: true
                        )
                else if App.option('debug', false)
                    console.error "Attempted to switch to category '#{category}' which does not exist."
                return false # stop propogation

    ###
    A collection of Categories to display on mobile.

    @constructor
    @type {CollectionView}
    ###
    class module.MobileCategoryCollectionView extends module.CategoryCollectionView
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
            # This loads strictly after the page is already initialized
            # Try to load whatever is currently loaded if it is a mobile category too
            # Otherwise, load to first category
            loadCategory = $("span[data-name='#{App.intentRank.options.category}']", @$el) or @$el.children().eq(0)
            loadCategory.trigger 'click'
            return @
