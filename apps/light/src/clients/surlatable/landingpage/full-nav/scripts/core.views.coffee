'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::onShow = _.wrap(module.ProductView::onShow, (onShow) ->
        if App.support.mobile()
            # Add one for description slide unless it's a product popup
            # in portrait mode without tagged products
            if @model.get('type') is "product" and App.utils.portrait() \
                    and _.isEmpty(@model.get('taggedProducts'))
                @numberOfImages = @model.get('images').length
            else
                @numberOfImages = @model.get('images').length + 1
        onShow.call(@)
        return
    )

    module.ProductView::onBeforeRender = ->
        linkName = "More on #{@model.get('name') or @model.get('title')} »"
        inlineLink = "<a href='#{@model.get('cjLink') or @model.get('url')}'>#{linkName}</a>"
        if @model.get("description")
            truncatedDescription = _.truncate(@model.get("description"), char_limit, true, true)
            @model.set("truncatedDescription", truncatedDescription + " " + inlineLink)
        return

    module.ProductView::replaceImages = ->
        $container = @$el.find(".main-image-container")
        if $container.is(":visible")
            if App.support.mobile()
                maxWidth = $container.width()
                maxHeight = $container.height()
            else
                maxWidth = $container.width()*1.3
                maxHeight = $container.height()*1.3
        else
            maxWidth = App.option("minImageWidth") or 300
            maxHeight = App.option("minImageHeight") or 300

        for imageEl, i in @$el.find(".main-image .hi-res")
            $image = $(imageEl)
            $cachedImage = $image.parent()

            # find image from id
            image = _.findWhere(@model.get('images'), id: $cachedImage.data('id'))
            imageUrl = image.resizeForDimens(maxWidth, maxHeight)

            if $image.is("img")
                $image.attr("src", imageUrl)
            else if $image.is("div")
                $image.css("background-image", "url('#{imageUrl}')")
        return

    module.ProductView::resizeProductImages = ->
        productImages = @$el.find(".main-image .hi-res")
        if productImages.length > 0 and productImages.first().is("div")
            # Let the browser execute the resizing window callbacks
            # otherwise, container height is 0 & images are resized to 0 height.
            setTimeout((=> @replaceImages()), 1)
        else
            imagesLoaded(productImages, (=> @replaceImages()))
        return

    _.extend(module.ProductView.prototype.events, 
        "click .main-image .hi-res": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent.prototype.events =
        "click @ui.lookThumbnail, .back-to-recipe": (event) ->
            # Hide products, show content
            @taggedProductIndex = -1
            @updateContent()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            product = @taggedProducts[$targetEl.data("index")]
            url = product.get('cj_link') or product.get('url')
            ### Uncomment to enable switching view to product ###
            #@taggedProductIndex = $targetEl.data("index")
            #if App.support.mobile() and not @ui.lookThumbnail.is(':visible')
            #    @productThumbnails.currentView.index = Math.min($(".stl-look").children(':visible').length - 1, @prodcutThumbnails.currentView.index + 1)
            #product = @updateContent()
            App.vent.trigger('tracking:product:thumbnailClick', @getTrackingData(product))
            App.utils.openUrl(url)
            return

    module.ExpandedContent::updateScrollCta = ->
        $recipe = @$el.find(".recipe")
        unless $recipe.length is 0
            if ($recipe[0].scrollHeight - $recipe.scrollTop()) is $recipe.outerHeight()
                $recipe.siblings(".scroll-cta").hide()
            else
                $recipe.siblings(".scroll-cta").show()
        return

    module.ExpandedContent::shrinkContainerCallback = _.wrap(
        module.ExpandedContent::shrinkContainerCallback,
        (shrinkContainerCallback) ->
            # Patch shrinkContainerCallback to enble recipe scrolling when images are loaded
            shrinkContainerCallback.call(@)
            $(".recipe").scroll(=>
                @updateScrollCta()
                return
            )
    )

    module.ExpandedContent::updateContent = _.wrap(
        module.ExpandedContent::updateContent,
        (updateContent) ->
            updateContent.call(@)
            # set name of pop-up to currently visible 
            if @productInfo.hasView()
                currentProduct = @productInfo.currentView.model
                title = currentProduct.get('title') or currentProduct.get('name')
                @$el.find('.title-banner .title').html(title)
            return
    )

    module.ExpandedContent::showThumbnails = ->
        # SLT thumbnails are always across the bottom
        if @taggedProducts.length > 0 or \
           (App.support.mobile() and @taggedProducts.length > 0)
            # Initialize carousel if this has tagged products
            thumbnailsInstance = new module.ProductThumbnailsView(
                items: @taggedProducts
                attrs:
                    'lookImageSrc': @model.get('defaultImage').url
                    'lookName': @model.get('defaultImage').get('name')
                    'orientation': 'landscape'
            )
            @productThumbnails.show(thumbnailsInstance)
            @ui.lookThumbnail.hide()
        return

    module.ExpandedContent::destroy = _.wrap(module.ExpandedContent::destroy, (destroy) ->
        $(".recipe").off()
        destroy.call(@)
        return
    )

    module.CategoryCollectionView::onShow = ->
        # Enable sticky category bar
        sticky = App.option("page:stickyCategories")
        if _.isString(sticky)
            if sticky == 'desktop-only' and not App.support.mobile()
                @$el.parent().waypoint('sticky',
                    offset: '-111px'
                )
            else if sticky == 'mobile-only' and App.support.mobile()
                @$el.parent().waypoint('sticky',
                    offest: '-111px'
                )
        else if _.isBoolean(sticky) and sticky
            @$el.parent().waypoint('sticky',
                offest: '-111px'
            )

        return @
