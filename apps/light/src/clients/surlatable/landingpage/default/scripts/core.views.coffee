'use strict'

# @module core.views

module.exports = (module, App, Backbone, Marionette, $, _) ->
    # Patch CategoryView to accept sub-category hero images
    module.CategoryView.onClick = (event) ->
            view = @
            $el = view.$el
            category = view.model.get("name")
            nofilter = view.model.get("nofilter")
            eventTarget = $(event.target)

            if eventTarget.hasClass('sub-category')
                if not eventTarget.hasClass('selected') and eventTarget.data('name') # this is not in the above if on purpose
                    subCategory = _.find(view.model.get('subCategories'), (cat) ->
                        cat.name == eventTarget.data('name')
                    )
            else if $('.sub-category.selected', $el).length == 1
                $el.removeClass('selected')
                $('.sub-category.selected', $el).removeClass('selected')

            # switch to the selected category
            # if it has changed
            if not $el.hasClass("selected") or subCategory
                $el.siblings().each () ->
                    self = $(@)
                    self.removeClass 'selected'
                    $('.sub-category', self).removeClass 'selected'

                $el.addClass "selected"

                if subCategory
                    eventTarget.siblings().removeClass 'selected'
                    eventTarget.addClass 'selected'

                    # If subCategory leads with "|", its an additional filter on the category
                    if subCategory.get('name').charAt(0) == "|"
                        category += subCategory.get('name')
                    # Else, subCategory is a category
                    else
                        category = subCategory.get('name')

                # Set Hero image
                # Check if subcategory has hero image specified
                if subCategory and subCategory.get("desktopHeroImage") and subCategory.get("mobileHeroImage")
                    desktopHeroImage = subCategory.get("desktopHeroImage")
                    mobileHeroImage = subCategory.get("mobileHeroImage")
                # else check if category has hero image specified
                else if view.model.get("desktopHeroImage") and view.model.get("mobileHeroImage")
                    desktopHeroImage = view.model.get("desktopHeroImage")
                    mobileHeroImage = view.model.get("mobileHeroImage")
                
                if App.layoutEngine and desktopHeroImage and mobileHeroImage
                    App.heroArea.show(new App.core.HeroAreaView(
                        "desktopHeroImage": desktopHeroImage
                        "mobileHeroImage": mobileHeroImage
                    ))

                App.navigate(category,
                    trigger: true
                )
            return @