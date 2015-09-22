'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::coreOnShow = module.ProductView::onShow
    module.ProductView::onShow = ->
        if App.support.mobile()
            # Add one for description slide unless it's a product popup
            # in portrait mode without tagged products
            if @model.get('type') is "product" and App.utils.portrait() \
                    and _.isEmpty(@model.get('taggedProducts'))
                @numberOfImages = @model.get('images').length
            else
                @numberOfImages = @model.get('images').length + 1
        @coreOnShow()
        return
    
    module.ProductView::onBeforeRender = ->
        linkName = "More on #{@model.get('name') or @model.get('title')} »"
        inlineLink = "<a href='#{@model.get('cj_link') or @model.get('url')}'>#{linkName}</a>"
        if @model.get("description")
            truncatedDescription = _.truncate(@model.get("description"), char_limit, true, true)
            @model.set("truncated_description", truncatedDescription + " " + inlineLink)
        return

    module.ProductView::resizeProductImages = ->
        replaceImages = =>
            unless App.support.mobile()
                unless --productImageCount is 0 or productImages.first().is("div")
                    return
                $container = @$el.find(".main-image-container")
                if $container.is(":visible")
                    maxWidth = $container.width()*1.3
                    maxHeight = $container.height()*1.3
                else
                    maxWidth = App.option("minImageWidth") or 300
                    maxHeight = App.option("minImageHeight") or 300
                for image, i in productImages
                    $cachedImage = $(image).parent()
                    if $cachedImage.is("img")
                        imageUrl = App.utils.getResizedImage($cachedImage.attr("src"),
                            width: maxWidth,
                            height: maxHeight
                        )
                        $(image).attr("src", imageUrl)
                    else if $cachedImage.is("div")
                        imageUrl = $cachedImage.css("background-image").replace('url(','').replace(')','')
                        imageUrl = App.utils.getResizedImage(imageUrl,
                            width: maxWidth,
                            height: maxHeight
                        )
                        $(image).css("background-image", "url('#{imageUrl}')")
            return
        productImages = @$el.find(".main-image .hi-res")
        productImageCount = productImages.length
        if productImageCount > 0 and productImages.first().is("div")
            replaceImages()
        else
            productImages.one("load", replaceImages).each( ->
                if @complete
                    setTimeout( =>
                        $(@).load()
                        return
                    , 1)
                return
            )
        return

    _.extend(module.ProductView.prototype.events, 
        "click .main-image .hi-res": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent.prototype.events =
        "click .look-thumbnail, .back-to-recipe": (event) ->
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
            #if App.support.mobile() and not @$el.find('.look-thumbnail').is(':visible')
            #    @carouselRegion.currentView.index = Math.min($(".stl-look").children(':visible').length - 1, @carouselRegion.currentView.index + 1)
            #product = @updateContent()
            App.vent.trigger('tracking:product:thumbnailClick', product)
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

    module.ExpandedContent::coreShrinkContainerCallback = module.ExpandedContent::shrinkContainerCallback
    module.ExpandedContent::shrinkContainerCallback = ->
        # Patch shrinkContainerCallback to enble recipe scrolling when images are loaded
        cb = @coreShrinkContainerCallback()
        return =>
            cb(arguments)
            # must wait for all images to load
            if @_imageCount is 0
                $(".recipe").scroll(=>
                    @updateScrollCta()
                    return
                )
            return

    module.ExpandedContent::updateContent = ->
        ###
        SLT pop-ups are primarily product tiles
        ###
        if @taggedProductIndex < 0
            # Show content
            @_currentIndex = @taggedProductIndex = -1
            # Product popup
            if @product?
                product = @product
                @$el.find('.info').show()
                @$el.find('.look-image-container').hide()
            # Image popup
            else
                @$el.find('.info').hide()
                @$el.find('.look-image-container').show()
                @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))

            if App.support.mobile() then @$el.find('.look-thumbnail').hide()
            
            @carouselRegion.currentView?.deselectItems()
            if App.support.mobile() and @carouselRegion.hasView()
                @carouselRegion.currentView.index = Math.max(
                    0,
                    @carouselRegion.currentView.index - 1
                )
                @carouselRegion.currentView.calculateDistance()
        else
            # Show tagged product
            @_currentIndex = @taggedProductIndex

            product = @taggedProducts[@taggedProductIndex]
            if not @product
                # Recipes have "back to recipe" links
                product.set("recipe-name", @model.get('name') or @model.get('title'))

            @$el.find('.info').show()
            @$el.find('.look-image-container').hide()
            if App.support.mobile() then @$el.find('.look-thumbnail').show()
            
            @carouselRegion.currentView?.selectItem(@taggedProductIndex)
            if App.support.mobile() and @taggedProducts.length > 0 and @carouselRegion.currentView?
                @carouselRegion.currentView.calculateDistance()

        if product
            productInstance = new module.ProductView(
                model: product
            )
            @productInfo.show(productInstance)
            @$el.find('.title-banner .title').html(productInstance.model.get('title') or productInstance.model.get('name'))
        return product

    module.ExpandedContent::coreDestroy = module.ExpandedContent::destroy
    module.ExpandedContent::destroy = ->
        $(".recipe").off()
        @coreDestroy()
        return

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
