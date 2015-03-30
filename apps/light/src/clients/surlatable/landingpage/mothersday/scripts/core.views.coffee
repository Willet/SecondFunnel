'use strict'

# @module core.views

char_limit = 243

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
        "click .main-image .image": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent.prototype.events =
        "click .look-thumbnail, .back-to-recipe": (event) ->
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @stlIndex = Math.max(@stlIndex - 1, 0)
            @lookProductIndex = -1
            @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))
            if App.support.mobile()
                if App.utils.landscape()
                    @arrangeStlItemsVertical()
                else
                    @arrangeStlItemsHorizontal()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            @lookProductIndex = $targetEl.data("index")
            @updateCarousel()
            return

        'click .stl-swipe-down, .stl-swipe-up': (ev) ->
            $stlContainer = @$el.find(".stl-look-container")
            stlItems = @$el.find(".stl-look").children(":visible")
            distance = @$el.find(".stl-look").offset().top
            if $(ev.target).hasClass("stl-swipe-up")
                topMostItem = stlItems[@stlIndex]
                unless topMostItem is undefined
                    # number of pixels needed to move leftmost item to the end of carousel
                    difference = $stlContainer.height()
                    @stlIndex = _.findIndex(stlItems, (item) ->
                        # true if item is visible after moving leftmost item
                        return ($(item).outerHeight() + $(item).offset().top + difference) > $stlContainer.offset().top
                    )
                    distance -= $(stlItems[@stlIndex]).offset().top
            else
                @stlIndex = _.findIndex(stlItems, (item) ->
                    # true if item is only partially visible
                    return ($(item).outerHeight() + $(item).offset().top) > ($stlContainer.height() + $stlContainer.offset().top)
                )
                distance -= $(stlItems[@stlIndex]).offset().top
            @updateStlGalleryPosition(distance, "portrait")
            return

        'click .stl-swipe-left, .stl-swipe-right': (ev) ->
            $stlContainer = @$el.find(".stl-look-container")
            stlItems = @$el.find(".stl-look").children(":visible")
            distance = @$el.find(".stl-look").offset().left
            if $(ev.target).hasClass("stl-swipe-left")
                leftMostItem = stlItems[@stlIndex]
                unless leftMostItem is undefined
                    # number of pixels needed to move leftmost item to the end of carousel
                    difference = $stlContainer.width()
                    @stlIndex = _.findIndex(stlItems, (item) ->
                        # true if item is visible after moving leftmost item
                        return ($(item).width() + $(item).offset().left + difference) > $stlContainer.offset().left
                    )
                    distance -= $(stlItems[@stlIndex]).offset().left
            else
                @stlIndex = _.findIndex(stlItems, (item) ->
                    # true if item is only partially visible
                    return ($(item).width() + $(item).offset().left) > ($stlContainer.width() + $stlContainer.offset().left)
                )
                distance -= $(stlItems[@stlIndex]).offset().left
            @updateStlGalleryPosition(distance, "landscape")
            return

    module.ExpandedContent::updateScrollCta = ->
        $recipe = @$el.find(".recipe")
        unless $recipe.length is 0
            if ($recipe[0].scrollHeight - $recipe.scrollTop()) is $recipe.outerHeight()
                $recipe.siblings(".scroll-cta").hide()
            else
                $recipe.siblings(".scroll-cta").show()
        return

    module.ExpandedContent::updateStlGalleryPosition = (distance, orientation, duration=300) ->
        updateStlArrows = =>
            stlItems = $stlLook.children(":visible")
            if orientation is "landscape"
                @upArrow.hide()
                @downArrow.hide()
                if stlItems.first().offset().left >= $stlContainer.offset().left
                    @leftArrow.hide()
                else
                    @leftArrow.show()
                if stlItems.last().offset().left + stlItems.last().width() <= $stlContainer.offset().left + $stlContainer.width()
                    @rightArrow.hide()
                else
                    @rightArrow.show()
            else
                @leftArrow.hide()
                @rightArrow.hide()
                if stlItems.first().offset().top >= $stlContainer.offset().top
                    @upArrow.hide()
                else
                    @upArrow.show()
                if stlItems.last().offset().top + stlItems.last().outerHeight() <= $stlContainer.offset().top + $stlContainer.height()
                    @downArrow.hide()
                else
                    @downArrow.show()
            return
        $stlContainer = @$el.find(".stl-look-container")
        $stlLook = @$el.find(".stl-look")
        height = "88%"
        top = "0"
        # Small random number added to ensure transitionend is triggered.
        distance += Math.random() / 1000
        if orientation is "landscape"
            translate3d = 'translate3d(' + distance + 'px, 0px, 0px)'
            translate = 'translateX(' + distance + 'px)'
        else
            translate3d = 'translate3d(0px, ' + distance + 'px, 0px)'
            translate = 'translateY(' + distance + 'px)'
            unless @stlIndex is 0
                height = "80%"
                top = @upArrow.height()
        if orientation is "portrait"
            $stlContainer.css(
                "height": height
                "top": top
            )
        $stlLook.css(
            '-webkit-transition-duration': (duration / 1000).toFixed(1) + 's',
            'transition-duration': (duration / 1000).toFixed(1) + 's',
            '-webkit-transform': translate3d,
            '-ms-transform': translate,
            'transform': translate3d
        ).one('webkitTransitionEnd msTransitionEnd transitionend', updateStlArrows)
        if duration is 0
            updateStlArrows()
        return

    module.ExpandedContent::arrangeStlItemsVertical = ->
        if @model.get("type") is "image" or @model.get("type") is "gif"
            @leftArrow.hide()
            @rightArrow.hide()
            if @model.get("tagged-products")?.length > 0 or App.support.mobile()
                height = "88%"
                top = "0"
                # Making room for up arrow
                unless @stlIndex is 0
                    height = "80%"
                    top = @upArrow.height()
                @$el.find(".stl-look-container").css(
                    "height": height
                    "top": top
                )
                $stlLook = @$el.find(".stl-look")
                distance = $stlLook.offset().top - $($stlLook.children(":visible")[@stlIndex]).offset().top
                @updateStlGalleryPosition(distance, "portrait", 0)
        return

    module.ExpandedContent::arrangeStlItemsHorizontal = ->
        if @model.get("type") is "image" or @model.get("type") is "gif"
            @upArrow.hide()
            @downArrow.hide()
            @$el.find(".stl-look-container").css(
                "height": "95%"
                "top": "0"
            )
            if @model.get("tagged-products")?.length > 0 or App.support.mobile()
                $stlLook = @$el.find(".stl-look")
                stlItems = $stlLook.children(":visible")
                totalItemWidth = 0
                for item in stlItems
                    totalItemWidth += $(item).outerWidth()
                if totalItemWidth <= @$el.find(".stl-look-container").width()
                    @leftArrow.hide()
                    @rightArrow.hide()
                    distance = 0
                else
                    distance = $stlLook.offset().left - $(stlItems[@stlIndex]).offset().left
                @updateStlGalleryPosition(distance, "landscape", 0)
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
                if App.support.mobile()
                    if App.utils.portrait()
                        @arrangeStlItemsHorizontal()
                    else
                        @arrangeStlItemsVertical()
                    return

                # loading hero area
                unless $container?.length
                    if @model.get("orientation") is "landscape"
                        @arrangeStlItemsHorizontal()
                    else
                        @arrangeStlItemsVertical()
                    return
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
                @arrangeStlItemsHorizontal()
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
        if App.support.mobile() and App.utils.landscape()
            @$el.closest(".previewContainer").addClass("landscape")
        else
            @$el.closest(".previewContainer").removeClass("landscape")
            unless App.support.mobile()
                @$el.closest(".fullscreen").addClass("loading-images")
        @lookThumbnail = @$el.find('.look-thumbnail')
        @lookThumbnail.hide()
        @$el.find('.info').hide()
        if @model.get("tagged-products")?.length > 0
            @stlIndex = 0
            @lookProductIndex = -1
            @leftArrow = @$el.find('.stl-swipe-left')
            @rightArrow = @$el.find('.stl-swipe-right')
            @upArrow = @$el.find(".stl-swipe-up")
            @downArrow = @$el.find(".stl-swipe-down")
        @resizeContainer()

        if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
            $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                offset: "bottom-in-view"
                direction: "up"
            )
        return

    module.ExpandedContent::updateCarousel = ->
        if @lookProductIndex < 0
            if @lookThumbnail.is(":visible")
                @stlIndex = Math.max(0, @stlIndex - 1)
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @$el.find('.stl-item').removeClass("selected")
            @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))
            if App.support.mobile()
                if App.utils.landscape()
                    @arrangeStlItemsVertical()
                else
                    @arrangeStlItemsHorizontal()
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
            unless @lookThumbnail.is(":visible")
                @stlIndex = Math.min($(".stl-look").children(":visible").length - 1, @stlIndex + 1)
            @lookThumbnail.show()
            if App.support.mobile()
                if App.utils.landscape()
                    @arrangeStlItemsVertical()
                else
                    @arrangeStlItemsHorizontal()
        return

    module.ExpandedContent::close = ->
        # See NOTE in onShow
        unless App.support.isAnAndroid()
            $(document.body).removeClass("no-scroll")

        @$(".stick-bottom").waypoint("destroy")
        $(".recipe").off()
        return
