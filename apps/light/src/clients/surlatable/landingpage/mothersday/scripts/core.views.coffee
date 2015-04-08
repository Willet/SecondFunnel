'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    class module.CarouselView extends Marionette.ItemView
        template: "#carousel_template"

        events:
            'click .carousel-swipe-left, .carousel-swipe-right, .carousel-swipe-up, .carousel-swipe-down': (ev) ->
                if $(ev.target).hasClass("carousel-swipe-left")
                    @scrollHorizontal("left")
                else if $(ev.target).hasClass("carousel-swipe-right")
                    @scrollHorizontal("right")
                else if $(ev.target).hasClass("carousel-swipe-up")
                    @scrollVertical("up")
                else
                    @scrollVertical("down")
                return

        serializeData: ->
            data = {
                items: @items,
                index: @index,
                attrs: @attrs
            }
            return data

        initialize: (data) ->
            @attrs = data['attrs'] or []
            @index = data['index'] or 0
            @items = data['items'] or []
            return

        onRender: ->
            @setElement(@$el.children())
            return

        onShow: ->
            @container = @$el.find(".carousel-container")
            @leftArrow = @$el.find(".carousel-swipe-left")
            @rightArrow = @$el.find(".carousel-swipe-right")
            @upArrow = @$el.find(".carousel-swipe-up")
            @downArrow = @$el.find(".carousel-swipe-down")
            @slide = @$el.find(".carousel-slide")
            @slide.swipe(
                triggerOnTouchEnd: true,
                swipeStatus: _.bind(@swipeStatus, @)
                allowPageScroll: 'auto'
            )
            @arrangeCarousel()
            return

        swipeStatus: (event, phase, direction, distance, fingers, duration) ->
            if phase is 'end'
                if App.utils.portrait()
                    # flip direction for 'natural' scroll
                    direction = if direction is 'left' then 'right' else 'left'
                    @scrollHorizontal(direction)
                else
                    direction = if direction is 'up' then 'down' else 'up'
                    @scrollVertical(direction)
            return @

        updateCarousel: (distance, orientation, duration=300) ->
            updateArrows = =>
                $items = @slide.children(":visible")
                if orientation is "landscape"
                    if Math.round($items.first().offset().left) >= Math.round(@container.offset().left)
                        @leftArrow.hide()
                    else
                        @leftArrow.show()
                    if Math.round($items.last().offset().left + $items.last().width()) <= Math.round(@container.offset().left + @container.width())
                        @rightArrow.hide()
                    else
                        @rightArrow.show()
                else
                    if Math.round($items.first().offset().top) >= Math.round(@container.offset().top)
                        @upArrow.hide()
                    else
                        @upArrow.show()
                    if Math.round($items.last().offset().top + $items.last().outerHeight()) <= Math.round(@container.offset().top + @container.height())
                        @downArrow.hide()
                    else
                        @downArrow.show()
                return
            # Small random number added to ensure transitionend is triggered.
            distance += Math.random() / 1000
            if orientation is "landscape"
                translate3d = 'translate3d(' + distance + 'px, 0px, 0px)'
                translate = 'translateX(' + distance + 'px)'
            else
                translate3d = 'translate3d(0px, ' + distance + 'px, 0px)'
                translate = 'translateY(' + distance + 'px)'
                if @index is 0
                    height: "88%"
                    top: "0"
                else
                    height = "80%"
                    top = @upArrow.height()
                @container.css(
                    "height": height
                    "top": top
                )
            @slide.css(
                '-webkit-transition-duration': (duration / 1000).toFixed(1) + 's',
                'transition-duration': (duration / 1000).toFixed(1) + 's',
                '-webkit-transform': translate3d,
                '-ms-transform': translate,
                'transform': translate3d
            ).one('webkitTransitionEnd msTransitionEnd transitionend', updateArrows)
            if duration is 0
                updateArrows()
            return

        scrollHorizontal: (direction) ->
            $container = @container
            $items = @slide.children(":visible")
            distance = @slide.offset().left
            if direction is 'left'
                leftMostItem = $items[@index]
                unless leftMostItem is undefined
                    # number of pixels needed to move leftmost item to the end of carousel
                    difference = @container.width()
                    index = _.findIndex($items, (item) ->
                        # true if item is visible after moving leftmost item
                        return ($(item).width() + $(item).offset().left + difference) > $container.offset().left
                    )
            else
                index = _.findIndex($items, (item) ->
                    # true if item is only partially visible
                    return ($(item).width() + $(item).offset().left) > ($container.width() + $container.offset().left)
                )
            if index > -1
                @index = index
                distance -= $($items.get(@index)).offset().left
                @updateCarousel(distance, "landscape")
            return

        scrollVertical: (direction) ->
            $container = @container
            $items = @slide.children(":visible")
            distance = @slide.offset().top
            if direction is "up"
                topMostItem = $items[@index]
                unless topMostItem is undefined
                    # number of pixels needed to move leftmost item to the end of carousel (while still being partially visible)
                    difference = @container.height() * 0.60
                    index = _.findIndex($items, (item) ->
                        # true if item is visible after moving leftmost item
                        return ($(item).outerHeight() + $(item).offset().top + difference) > $container.offset().top
                    )
            else
                index = _.findIndex($items, (item) ->
                    # true if item is only partially visible
                    return ($(item).outerHeight() + $(item).offset().top) > ($container.height() + $container.offset().top)
                )
            if index > -1
                @index = index
                distance -= $($items[@index]).offset().top
                @updateCarousel(distance, "portrait")

        arrangeHorizontal: ->
            @upArrow.hide()
            @downArrow.hide()
            @container.css(
                "height": "95%"
                "top": "0"
            )
            $items = @slide.children(":visible")
            totalItemWidth = 0
            for item in $items
                totalItemWidth += $(item).outerWidth()
            if totalItemWidth <= @container.width()
                @leftArrow.hide()
                @rightArrow.hide()
                distance = 0
            else
                distance = @slide.offset().left - $($items.get(@index)).offset().left
            @updateCarousel(distance, "landscape", 0)
            return

        arrangeVertical: ->
            @leftArrow.hide()
            @rightArrow.hide()
            height = "88%"
            top = "0"
            # Making room for up arrow
            unless @index is 0
                height = "80%"
                top = @upArrow.height()
            @container.css(
                "height": height
                "top": top
            )
            distance = @slide.offset().top - $(@slide.children(":visible").get(@index)).offset().top
            @updateCarousel(distance, "portrait", 0)
            return

        arrangeCarousel: ->
            calculateDistance = =>
                if --imageCount isnt 0
                    return
                if App.support.mobile() and App.utils.landscape()
                    @arrangeVertical()
                else
                    @arrangeHorizontal()
                return

            imageCount = $("img", @$el).length
            # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
            $("img", @$el).one("load", calculateDistance).each ->
                if @complete
                    # Without the timeout the box may not be rendered. This lets the onShow method return
                    setTimeout (=>
                        $(@).load()
                        return
                    ), 1
                return
            return

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

    _.extend(module.ExpandedContent.prototype.regions,
        carouselRegion: ".carousel-region"
    )

    module.ExpandedContent.prototype.events =
        "click .look-thumbnail, .back-to-recipe": (event) ->
            @$el.find('.look-thumbnail').hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @carouselRegion.currentView.index = Math.max(@carouselRegion.currentView.index - 1, 0)
            @lookProductIndex = -1
            @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))
            if App.support.mobile()
                if App.utils.landscape()
                    @carouselRegion.currentView.arrangeVertical()
                else
                    @carouselRegion.currentView.arrangeHorizontal()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            @lookProductIndex = $targetEl.data("index")
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

                if @productInfo.currentView is undefined
                    @updateCarousel()
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
                # DOM elements must be visible before calling functions below
                $container.removeClass("loading-images")
                @updateScrollCta()
                return

        imageCount = $("img.main-image, img.image", @$el).length

        # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
        $("img.main-image, img.image", @$el).one("load", shrinkContainer()).each ->
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
        carouselInstance = new module.CarouselView(
            items: @model.get('tagged-products'),
            attrs: { 'lookImageSrc': @model.get('images')[0].url }
        )
        @carouselRegion.show(carouselInstance)
        @$el.find('.look-thumbnail').hide()
        @$el.find('.info').hide()
        if @model.get("tagged-products")?.length > 0
            @lookProductIndex = -1
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
            # delegate swipe to product view to swipe through images
            unless (direction is 'left' and productImageIndex is numberOfImages) or (direction is 'right' and productImageIndex is 0)
                @productInfo.currentView.swipeStatus(event, phase, direction, distance, fingers, duration)
                return
        if phase is 'end'
            if direction is 'right'
                @lookProductIndex--
                if @lookProductIndex < -1
                    @lookProductIndex = @$el.find(".stl-look").children(":visible").length - 1
            else if direction is 'left'
                @lookProductIndex++
                if @lookProductIndex is @model.get("tagged-products")?.length
                    @lookProductIndex = -1
            @updateCarousel()
        return @

    module.ExpandedContent::updateCarousel = ->
        if @lookProductIndex < 0
            if @$el.find('.look-thumbnail').is(":visible")
                @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
            @$el.find('.look-thumbnail').hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @$el.find('.stl-item').removeClass("selected")
            @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))
            if App.support.mobile()
                if App.utils.landscape()
                    @carouselRegion.currentView.arrangeVertical()
                else
                    @carouselRegion.currentView.arrangeHorizontal()
        else
            @$el.find(".stl-item").filter("[data-index=#{@lookProductIndex}]")
                .addClass("selected").siblings().removeClass("selected")
            @$el.find('.info').show()
            @$el.find('.look-image-container').hide()
            if @model.get("type") is "product"
                product = new module.Product(@model.attributes)
            else if @model.get("tagged-products").length > 0
                product = new module.Product(@model.get("tagged-products")[@lookProductIndex])
            unless product is undefined
                product.set("recipe-name", @model.get('name') or @model.get('title'))
                productInstance = new module.ProductView(
                    model: product
                )
                @$el.find('.title-banner .title').html(productInstance.model.get('title') or productInstance.model.get('name'))
                @productInfo.show(productInstance)
            unless @$el.find('.look-thumbnail').is(":visible")
                @carouselRegion.currentView.index = Math.min($(".stl-look").children(":visible").length - 1, @carouselRegion.currentView.index + 1)
            @$el.find('.look-thumbnail').show()
            if App.support.mobile()
                if App.utils.landscape()
                    @carouselRegion.currentView.arrangeVertical()
                else
                    @carouselRegion.currentView.arrangeHorizontal()
        return

    module.ExpandedContent::close = ->
        # See NOTE in onShow
        unless App.support.isAnAndroid()
            $(document.body).removeClass("no-scroll")

        @$(".stick-bottom").waypoint("destroy")
        $(".recipe").off()
        return
