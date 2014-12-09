'use strict'

# @module core.views

module.exports = (module, App, Backbone, Marionette, $, _) ->
    # Patch CategoryView to accept sub-category hero images
    _.extend module.CategoryView.prototype.events,
        'click': (event) ->
            category = @model
            $el = @$el
            $subCatEl = $el.find '.sub-category'

            if not $el.hasClass 'expanded'
                # First click, expand subcategories
                $el.addClass 'expanded'
                $el.siblings().removeClass 'expanded'
            else
                # Second click, select category
                $el.removeClass 'expanded'
                unless $el.hasClass 'selected' and not $subCatEl.hasClass 'selected'
                    # remove selected from child sub-categories
                    $subCatEl.removeClass 'selected'
                    # switch to the selected category if it has changed
                    unless $el.hasClass 'selected'
                        $el.addClass 'selected'
                        # remove selected from other categories
                        $el.siblings().each () ->
                            self = $(@)
                            self.removeClass 'selected'
                            self.find('.sub-category').removeClass 'selected'

                    desktopHeroImage = category.get "desktopHeroImage"
                    mobileHeroImage = category.get "mobileHeroImage"
                    # switch hero image *of category*
                    if desktopHeroImage and mobileHeroImage
                        App.heroArea.show(new App.core.HeroAreaView(
                            "desktopHeroImage": desktopHeroImage
                            "mobileHeroImage": mobileHeroImage
                        ))

                    App.navigate(category.get("name"),
                        trigger: true
                    )
            
            return false # stop propogation

        'click .sub-category': (event) ->
            $el = @$el
            category = @model
            $target = $(event.target)
            $subCatEl = if $target.hasClass 'sub-category' then $target else $target.parent '.sub-category'

            # Retrieve subcategory object
            subCategory = _.find category.get('subCategories'), (subcategory) ->
                return subcategory.name == $subCatEl.data('name')

            # Close categories drop-down
            $el.removeClass 'expanded'

            # switch to the selected category if it has changed
            unless $el.hasClass 'selected' and $subCatEl.hasClass 'selected' and not $subCatEl.siblings().hasClass 'selected'
                # switch to selected sub-category
                $subCatEl.addClass 'selected'
                $subCatEl.siblings().removeClass 'selected'
                # switch to selected category if not already
                unless $el.hasClass 'selected'
                    $el.addClass 'selected'
                    # remove selected from other categories
                    $el.siblings().each () ->
                        self = $(@)
                        self.removeClass 'selected'

                # If subCategory leads with "|", its an additional filter on the parent category
                if subCategory['name'].charAt(0) == "|"
                    switchCategory = category.get("name") + subCategory['name']
                # Else, subCategory is a category
                else
                    switchCategory = subCategory['name']

                # Set Hero image - check if subcategory has hero image specified
                desktopHeroImage = subCategory["desktopHeroImage"] or category.get("desktopHeroImage")
                mobileHeroImage = subCategory["mobileHeroImage"] or category.get("mobileHeroImage")
                
                if desktopHeroImage and mobileHeroImage
                    App.heroArea.show(new App.core.HeroAreaView(
                        "desktopHeroImage": desktopHeroImage
                        "mobileHeroImage": mobileHeroImage
                    ))

                App.navigate(switchCategory,
                    trigger: true
                )

            return false # stop propogation
