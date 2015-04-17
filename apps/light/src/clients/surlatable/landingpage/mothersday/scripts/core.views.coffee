'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::onShow = ->
        if App.support.mobile()
            # Add one for description slide unless it's a product popup in portrait mode
            if @model.get('type') is "product" and App.utils.portrait()
                @numberOfImages = @model.get('images').length
            else
                @numberOfImages = @model.get('images').length + 1
        @galleryIndex = Math.min(@galleryIndex, @numberOfImages - 1)
        @leftArrow = @$el.find('.gallery-swipe-left')
        @rightArrow = @$el.find('.gallery-swipe-right')
        @mainImage = @$el.find('.main-image')
        @resizeProductImages()
        if @numberOfImages > 1
            @scrollImages(@mainImage.width()*@galleryIndex, 0)
            @updateGallery()
            if App.support.mobile() and @model.get('type') is "product"
                @mainImage.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
        return

    module.ProductView::onBeforeRender = ->
        inlineLink = "More on #{@model.attributes.name or @model.attributes.title} »"
        if @model.attributes.cj_link is undefined
            inlineLink = "<a href=#{@model.attributes.url}>#{inlineLink}</a>"
        else
            inlineLink = "<a href=#{@model.attributes.cj_link}>#{inlineLink}</a>"
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
            @$el.find('.look-thumbnail').hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @lookProductIndex = -1
            @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))
            if App.support.mobile()
                @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
                if App.utils.landscape()
                    @carouselRegion.currentView.calculateVerticalPosition()
                else
                    @carouselRegion.currentView.calculateHorizontalPosition()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            @lookProductIndex = $targetEl.data("index")
            if App.support.mobile() and not @$el.find('.look-thumbnail').is(':visible')
                @carouselRegion.currentView.index = Math.min($(".stl-look").children(':visible').length - 1, @carouselRegion.currentView.index + 1)
            @updateCarousel()
            product = new App.core.Product(@model.get("tagged-products")[@lookProductIndex])
            App.vent.trigger('tracking:product:thumbnailClick', product)
            return

    module.ExpandedContent::updateScrollCta = ->
        $recipe = @$el.find(".recipe")
        unless $recipe.length is 0
            if ($recipe[0].scrollHeight - $recipe.scrollTop()) is $recipe.outerHeight()
                $recipe.siblings(".scroll-cta").hide()
            else
                $recipe.siblings(".scroll-cta").show()
        return

    module.ExpandedContent::resizeContainer = ->
        ###
        Returns a callback that sizes the preview container.
        ###
        shrinkContainer = =>
            =>
                $table = @$el.find(".table")
                $container = @$el.closest(".fullscreen")
                $containedItem = @$el.closest(".content")
                # must wait for all images to load
                if --imageCount isnt 0
                    return

                # product view must be initialized after elements load so that the banner can be updated
                if @productInfo.currentView is undefined
                    @updateCarousel()

                if @model.get("type") is "image" or @model.get("type") is "gif"
                    if @lookProductIndex > -1
                        @$el.find(".look-thumbnail").show()
                    else
                        @$el.find(".look-thumbnail").hide()
                $(".recipe").scroll( =>
                    @updateScrollCta()
                    return
                )
                $container.css(
                    top: "0"
                    bottom: "0"
                    left: "0"
                    right: "0"
                )

                heightReduction = ($(window).height() - $containedItem.outerHeight()) / 2
                widthReduction = ($(window).width() - $containedItem.outerWidth()) / 2
                if heightReduction <= 0 # String because jQuery checks for falsey values
                    heightReduction = "0"
                if widthReduction <= 0 # String because jQuery checks for falsey values
                    widthReduction = "0"
                $container.css(
                    top: heightReduction
                    bottom: heightReduction
                    left: widthReduction
                    right: widthReduction
                )
                $container.removeClass("loading-images")
                @updateScrollCta()
                return

        imageCount = $("img.load-image", @$el).length

        # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
        $("img.load-image", @$el).one("load", shrinkContainer()).each ->
            if @complete
                # Without the timeout the box may not be rendered. This lets the onShow method return
                setTimeout (=>
                    $(@).load()
                    return
                ), 1
            return

        return

    module.ExpandedContent::onShow = ->
        if App.support.mobile()
            if App.utils.landscape()
                @$el.closest(".previewContainer").addClass("landscape")
            else
                @$el.closest(".previewContainer").removeClass("landscape")
            if @model.get('type') is "image" or @model.get('type') is "gif"
                @$el.find(".look-product-carousel").swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
        else
            @$el.closest(".previewContainer").removeClass("landscape")
            @$el.closest(".fullscreen").addClass("loading-images")
        @$el.find('.info').hide()
        if @model.get("tagged-products")?.length > 0
            @lookProductIndex = -1
            carouselInstance = new module.CarouselView(
                items: @model.get('tagged-products'),
                attrs: { 'lookImageSrc': @model.get('images')[0].url }
            )
            @carouselRegion.show(carouselInstance)
        @$el.find('.look-thumbnail').hide()
        @resizeContainer()

        if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
            $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                offset: "bottom-in-view"
                direction: "up"
            )
        return

    module.ExpandedContent::swipeStatus = (event, phase, direction, distance, fingers, duration) ->
        productImageIndex = @productInfo.currentView?.galleryIndex or 0
        numberOfImages = (@productInfo.currentView?.numberOfImages - 1) or 0
        if @lookProductIndex > -1
            # delegate swipe to ProductView to swipe through images
            unless (direction is 'left' and productImageIndex is numberOfImages) or (direction is 'right' and productImageIndex is 0)
                @productInfo.currentView.swipeStatus(event, phase, direction, distance, fingers, duration)
                return
        if phase is 'end'
            if direction is 'right'
                @lookProductIndex--
                # swipe from recipe to last product
                if @lookProductIndex < -1
                    @lookProductIndex = @model.get('tagged-products').length - 1
                    if App.support.mobile()
                        @carouselRegion.currentView.index = Math.min($('.stl-look').children().length - 1, @carouselRegion.currentView.index + 1)
                # swipe from first product to recipe
                else if @lookProductIndex is -1 and App.support.mobile()
                    @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
            else if direction is 'left'
                @lookProductIndex++
                # swipe from last product to recipe
                if @lookProductIndex is @model.get('tagged-products')?.length
                    @lookProductIndex = -1
                    if App.support.mobile()
                        @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
                else if @lookProductIndex is 0 and App.support.mobile()
                    @carouselRegion.currentView.index = Math.min($('.stl-look').children(':visible').length - 1, @carouselRegion.currentView.index + 1)
            @updateCarousel()
        return @

    module.ExpandedContent::updateCarousel = ->
        if @lookProductIndex < 0
            @$el.find('.look-thumbnail').hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @$el.find('.stl-item').removeClass("selected")
            @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))
            if App.support.mobile() and @model.get("tagged-products")?.length > 0
                if App.utils.landscape()
                    @carouselRegion.currentView.calculateVerticalPosition()
                else
                    @carouselRegion.currentView.calculateHorizontalPosition()
        else
            @$el.find(".stl-item").filter("[data-index=#{@lookProductIndex}]")
                .addClass("selected").siblings().removeClass("selected")
            @$el.find('.info').show()
            @$el.find('.look-image-container').hide()
            @$el.find('.look-thumbnail').show()
            if @model.get("type") is "product"
                product = new module.Product(@model.attributes)
            else if @model.get("tagged-products")?.length > 0
                product = new module.Product(@model.get("tagged-products")[@lookProductIndex])
            unless product is undefined
                product.set("recipe-name", @model.get('name') or @model.get('title'))
                productInstance = new module.ProductView(
                    model: product
                )
                @$el.find('.title-banner .title').html(productInstance.model.get('title') or productInstance.model.get('name'))
                @productInfo.show(productInstance)
            if App.support.mobile() and @model.get("tagged-products")?.length > 0
                if App.utils.landscape()
                    @carouselRegion.currentView.calculateVerticalPosition()
                else
                    @carouselRegion.currentView.calculateHorizontalPosition()
        return

    module.ExpandedContent::close = ->
        # See NOTE in onShow
        unless App.support.isAnAndroid()
            $(document.body).removeClass("no-scroll")

        @$(".stick-bottom").waypoint("destroy")
        $(".recipe").off()
        @$el.find(".look-product-carousel").swipe("destroy")
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
