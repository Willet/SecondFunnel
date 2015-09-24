"use strict"

imagesLoaded = require('imagesLoaded')
swipe = require('jquery-touchswipe')
Modernizr = require('modernizr')
require("jquery-scrollto")
require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky

module.exports = (module, App, Backbone, Marionette, $, _) ->
    $window = $(window)
    $document = $(document)

    class module.ProductView extends Marionette.ItemView
        template: "#product_info_template"
        templates: ->
            templateRules = [
                # supported contexts: options, data
                "#<%= data.type %>_info_template"
                "#image_info_template"
                "#product_info_template"
            ]
            unless App.support.mobile()
                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            templateRules


        events:
            'click .item': (ev) ->
                $selectedItem = $(ev.target)
                @galleryIndex = $selectedItem.data("index")
                @scrollImages(@mainImage.width()*@galleryIndex)
                @updateGallery()

                App.vent.trigger("tracking:product:imageView", @model)
                return

            'click .gallery-swipe-left, .gallery-swipe-right': (ev) ->
                $target = $(ev.target)
                unless $target.hasClass("grey")
                    if $target.hasClass("gallery-swipe-left")
                        @galleryIndex = Math.max(@galleryIndex - 1, 0)
                    else
                        @galleryIndex = Math.min(@galleryIndex + 1, @numberOfImages - 1)
                    @scrollImages(@mainImage.width()*@galleryIndex)
                    @updateGallery()

                    App.vent.trigger("tracking:product:imageView", @model)
                return

            'click .buy': (ev) ->
                $evTarget = $(ev.target)
                if $evTarget.is("a")
                    $target = $evTarget
                else if $evTarget.children("a").length
                    $target = $evTarget.children("a")
                else if $evTarget.parents("a").length
                    $target = $evTarget.parents("a")
                else
                    return false

                if $target.hasClass('find-store')
                    App.vent.trigger('tracking:product:findStoreClick', @model)
                else
                    App.vent.trigger('tracking:product:buyClick', @model)

                App.utils.openUrl(url)
                # Stop propogation to avoid double-opening url
                return false

            'click .description': (ev) ->
                # Assumes 'Read more' in the description goes to product page
                $evTarget = $(ev.target)
                if $evTarget.is("a")
                    $target = $evTarget
                else if $evTarget.children("a").length
                    $target = $evTarget.children("a")
                else
                    return false

                App.vent.trigger('tracking:product:moreInfoClick', @model)
                App.utils.openUrl(url)
                # Stop propogation to avoid double-opening url
                return false

        initialize: ->
            @numberOfImages = @model.get('images')?.length or 0
            @galleryIndex = 0
            return

        onRender: ->
            # Get rid of that pesky wrapping-div
            @$el = @$el.children() # NOTE 1st child will become element, all other children will be dropped
            @$el.unwrap() # Unwrap the element to prevent infinitely nesting elements during re-render
            @setElement(@$el)
            return

        onShow: ->
            @leftArrow = @$el.find('.gallery-swipe-left')
            @rightArrow = @$el.find('.gallery-swipe-right')
            @mainImage = @$el.find('.main-image')
            @resizeProductImages() # Parent elements must be completely sized before this fires
            if @numberOfImages > 1
                @scrollImages(@mainImage.width()*@galleryIndex, 0)
                @updateGallery()
                @mainImage.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
            return

        resizeProductImages: ->
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
                        if $(image).is("img")
                            imageUrl = App.utils.getResizedImage($(image).attr("src"),
                                width: maxWidth,
                                height: maxHeight
                            )
                            $(image).attr("src", imageUrl)
                        else if $(image).is("div")
                            imageUrl = $(image).css("background-image").replace('url(','').replace(')','')
                            imageUrl = App.utils.getResizedImage(imageUrl,
                                width: maxWidth,
                                height: maxHeight
                            )
                            $(image).css("background-image", "'url(#{imageUrl})'")
                return
            productImages = @$el.find(".main-image .image")
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

        swipeStatus: (event, phase, direction, distance, fingers, duration) ->
            focusWidth = @mainImage.width()
            offset = focusWidth * @galleryIndex

            if phase is 'move'
                if direction is 'left'
                    @scrollImages(distance + offset, duration)
                else if direction is 'right'
                    @scrollImages(offset - distance, duration)
            else if phase is 'end'
                if direction is 'right'
                    @galleryIndex = Math.max(@galleryIndex - 1, 0)
                else if direction is 'left'
                    @galleryIndex = Math.min(@galleryIndex + 1, @numberOfImages - 1)
                @scrollImages(focusWidth * @galleryIndex, duration)
                @updateGallery()
            else if phase is 'cancel'
                @scrollImages(focusWidth * @galleryIndex, duration)
            return @

        scrollImages: (distance, duration = 250) ->
            distance *= -1
            if App.support.isLessThanIe9()
                @mainImage.css(
                    'position': 'relative',
                    'left': distance
                )
            else
                @mainImage.css(
                    '-webkit-transition-duration': (duration / 1000).toFixed(1) + 's',
                    'transition-duration': (duration / 1000).toFixed(1) + 's',
                    '-webkit-transform': 'translate3d(' + distance + 'px, 0px, 0px)',
                    '-ms-transform': 'translateX(' + distance+ 'px)',
                    'transform': 'translate3d(' + distance + 'px, 0px, 0px)'
                )
            return

        updateGallery: ->
            @$el.find(".item")
                .removeClass("selected")
                .filter("[data-index=#{@galleryIndex}]")
                .addClass("selected")
            if @galleryIndex is 0
                @leftArrow.addClass("grey")
                @rightArrow.removeClass("grey")
            else if @galleryIndex is @numberOfImages - 1
                @leftArrow.removeClass("grey")
                @rightArrow.addClass("grey")
            else
                @leftArrow.removeClass("grey")
                @rightArrow.removeClass("grey")
            return


    ###
    Similar products look like tiles in a feed
    Should have a tile-id attribute to allow continuous browsing
    ###
    class module.SimilarProductsView extends Marionette.ItemView
        template: "#similar_products_template"

        events:
            "click .tile": (event) ->
                id = $(event.currentTarget).data("id")
                product = @collection.get(id)
                if product.get('tile-id', false)
                    # open tile in hero area
                    if App.option("page:tiles:openTileInHero", false)
                        App.router.navigate("tile/#{String(product.get('tile-id'))}", trigger: true)
                    # open tile in popup
                    else
                        App.router.navigate("preview/#{String(product.get('tile-id'))}", trigger: true)
                else
                    # go to PDP
                    App.utils.openUrl(product.get("url"))

        initialize: (products) ->
            @collection = new module.ProductCollection()
            for product in products
                product.template = 'product'
                @collection.add(new module.SimilarProduct(product))
            return


    ###
    Shop The Image or Shop The Product container

    @constructor
    @type {LayoutView}
    ###
    class module.ExpandedContent extends Marionette.LayoutView
        ###
        A container for viewing a tile.  If the tile has a product attribute,
        it is treated as a product view (product featured, tagged products in 
        carousel).  If the tile does not, it is treated as a content view (content
        featured, tagged products in carousel).
        ###
        regions:
            productInfo: ".product-info"
            carouselRegion: ".carousel-region"
            similarProducts: ".similar-products"

        events:
            "click .look-thumbnail": (event) ->
                # Look thumbnail is generally only visible/clickable on mobile
                # when it is in the carousel
                @taggedProductIndex = -1
                @updateContent()
                return

            "click .stl-look .stl-item": (event) ->
                $ev = $(event.target)
                $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
                @taggedProductIndex = $targetEl.data("index")

                unless @$el.find('.look-thumbnail').is(':visible')
                    @carouselRegion.currentView.index = Math.min(
                        $('.stl-look').children(':visible').length - 1,
                        @carouselRegion.currentView.index + 1
                    )
                if App.support.mobile()
                    # Scroll up to product view
                    $('body').scrollTo(".cell.info", 500)

                @updateContent()

                App.vent.trigger('tracking:product:thumbnailClick',
                                 @model.get("taggedProducts")[@taggedProductIndex])
                return

        initialize: ->
            @$el.attr
                id: "preview-#{@model.cid}"
                class: "preview-container"
            @_currentIndex = -1 # Track which product is being displayed

            # Product pop-up
            if @model.get("product")
                @product = @model.get("product")
                @taggedProductIndex = -1
                    
            # Content pop-up
            else
                # Content is contained in .look-image-container, loaded by template
                # Load up zeroth tagged product
                @taggedProductIndex = 0

            if @model.get("taggedProducts")?.length > 0
                # order taggedProducts by price
                if @model.get("taggedProducts")?.length > 1
                    @model.set("taggedProducts", _.sortBy(@model.get("taggedProducts"), (obj) ->
                        -1 * parseFloat((obj.price or "$0").substr(1), 10)
                    ))
            @taggedProducts = @model.get('taggedProducts') or []
            return
        
        onBeforeRender: ->
            # Need to get an appropriate sized image
            image = @model.get("defaultImage") or @model.get("image")
            
            if image?
                # orient image
                if image.get("sizes")?.master
                    width = image.get("sizes").master.width
                    height = image.get("sizes").master.height
                    if Math.abs((height-width)/width) <= 0.02
                        @model.set("orientation", "square")
                    else if width > height
                        @model.set("orientation", "landscape")
                    else
                        @model.set("orientation", "portrait")
                
                if App.support.mobile()
                    image.url = image.height($window.height())
                else
                    image = image.height(App.utils.getViewportSized(true), true)
            return

        # Update the current view
        # If taggedProductIndex < 0, then hide products
        updateContent: ->
            if App.support.mobile() and @taggedProductIndex < 0
                # only one thing visible at a time on mobile
                # Show content
                @_currentIndex = @taggedProductIndex = -1
                @$el.find('.look-thumbnail').hide()
                @$el.find('.info').hide()
                @$el.find('.look-image-container').show()
                @$el.find(".stl-item").removeClass("selected")
                @carouselRegion.currentView?.calculateDistance()
            else
                # Show tagged product
                @_currentIndex = @taggedProductIndex
                if @carouselRegion.hasView()
                    @$el.find(".stl-item").filter("[data-index=#{@taggedProductIndex}]")
                        .addClass("selected").siblings().removeClass("selected")
                productInstance = new module.ProductView(
                    model: @taggedProducts[@taggedProductIndex]
                )
                @productInfo.show(productInstance)
                if App.support.mobile()
                    @$el.find('.look-thumbnail').show()
                    @$el.find('.info').show()
                    @$el.find('.look-image-container').hide()
                    @carouselRegion.currentView?.calculateDistance()
            if @model.get("type") is "image" or @model.get("type") is "gif"
                if @taggedProductIndex > -1
                    @$el.find(".look-thumbnail").show()
                else
                    @$el.find(".look-thumbnail").hide()
            return

        ###
        Returns a callback that sizes the preview container, making the featured area sized
        to the viewport & allowing the overflow area to continue below the fold.
        Meant to be called when all images finish loading
        ###
        shrinkContainerCallback: ->
            =>
                # must wait for all images to load
                if --@_imageCount isnt 0
                    return
                
                $window = $(window)
                $container = @$el.closest(".fullscreen")
                $containedItem = @$el.closest(".content")
                # Content that will be sized to the viewport
                $feature = $containedItem.find(".feature") 
                if _.isEmpty($containedItem.find(".feature"))
                    $feature = $containedItem.find(".preview-container")
                else
                    $feature = $containedItem.find(".feature")
                # Content that will run below the fold
                $overflow = $containedItem.find(".overflow")

                # All images are loaded to frame content, render it now
                if not @productInfo.hasView()
                    @updateContent()

                $container.css(
                    top: "0"
                    bottom: "0"
                    left: "0"
                    right: "0"
                )
                # Reset feature and container height
                $containedItem.css(
                    'height': '100%'
                )
                $feature.css('height', '100%')

                # Popup sizing works by the featured area filling up as much room as the container will let it
                # In order to support overlowing content, need to let the featured content expand in the
                # constrained container, lock in the size, then let the container expand to fit the overflow content
                if _.some($overflow.map(-> return $(@).outerHeight()))
                    # Content overflows (one or more .overflow elements have non-zero height)
                    $overflow.hide()
                    # Lock in featured content height
                    $feature.css('height', $feature.outerHeight())
                    # Reveal overflow
                    $overflow.show()
                    heightValue = 'auto'
                    heightReduction =  10
                    widthReduction = ($window.width() - $containedItem.outerWidth()) / 2
                else
                    # Content fits in window, center it
                    heightValue = '100%'
                    heightReduction = ($window.height() - $containedItem.outerHeight()) / 2
                    widthReduction = ($window.width() - $containedItem.outerWidth()) / 2
                    if heightReduction <= 0 # String because jQuery checks for falsey values
                        heightReduction = "0"
                    if widthReduction <= 0 # String because jQuery checks for falsey values
                        widthReduction = "0"
                if App.support.mobile()
                    heightReduction = widthReduction = 0
                    
                $container.css(
                    left: widthReduction
                    right: widthReduction
                )
                $containedItem.css(
                    'height': heightValue
                    'margin-top': heightReduction
                    'margin-bottom': heightReduction
                )
                $container.removeClass("loading-images")
                return

        # shrinks container to images once images are loaded
        resizeContainer: ->
            @_imageCount = $("img.main-image, img.image", @$el).length

            # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
            $("img.main-image, img.image", @$el).one("load", @shrinkContainerCallback()).each(->
                if @complete
                    # Without the timeout the box may not be rendered. This lets the onShow method return
                    setTimeout((=>
                        $(@).load()
                        return
                    ), 1)
                return
            )
            return

        # Disable scrolling body when preview is shown
        onShow: ->
            if App.support.mobile()
                if App.utils.landscape()
                    @$el.closest(".previewContainer").addClass("landscape")
                else
                    @$el.closest(".previewContainer").removeClass("landscape")
                @$el.find('.info').hide()
                @$el.find(".look-product-carousel")?.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
            else
                @$el.closest(".previewContainer").removeClass("landscape")
                # will be removed by shrinkCallback
                @$el.closest(".fullscreen").addClass("loading-images")

            if @model.get('options')?.previewFeed
                @showSimilarProducts()
            else
                @showThumbnails()
            @resizeContainer()

            if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
                $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                    offset: "bottom-in-view"
                    direction: "up"
                )
            return

        showThumbnails: ->
            # A hook to customize the thumbnails initialization
            if @taggedProducts.length > 1 or \
               (App.support.mobile() and @taggedProducts.length > 0)
                # Initialize carousel if this is mobile with tagged product
                # or desktop/tablet with more than one product
                carouselInstance = new module.CarouselView(
                    items: @taggedProducts
                    attrs:
                        'lookImageSrc': @model.get('defaultImage').url
                        'lookName': @model.get('defaultImage').get('name')
                        'orientation': @model.get('defaultImage').get('orientation')
                )
                @carouselRegion.show(carouselInstance)
                @$el.find('.look-thumbnail').hide()
            return

        showSimilarProducts: ->
            # A hook to customize the pop-up feed initialization
            if @taggedProducts.length > 2 or \
               (App.support.mobile() and @taggedProducts.length > 0)
                similarProductsInstance = new module.SimilarProductsView(@taggedProducts)
                @similarProducts.show(similarProductsInstance)

        swipeStatus: (event, phase, direction, distance, fingers, duration) ->
            # Control gallery swiping
            # Allow swiping from content through products, in a cycle
            productImageIndex = @productInfo.currentView?.galleryIndex or 0
            numberOfImages = (@productInfo.currentView?.numberOfImages - 1) or 0
            index = @taggedProductIndex # local copy to modify
            if @taggedProductIndex > -1
                # delegate swipe to ProductView to swipe through images
                # unless going beyond last / first image
                unless (direction is 'left' and productImageIndex is numberOfImages) or \
                       (direction is 'right' and productImageIndex is 0)
                    @productInfo.currentView.swipeStatus(event, phase, direction,
                                                         distance, fingers, duration)
                    return
            if phase is 'end'
                if direction is 'right'
                    index--
                    # swipe from content to last product
                    if index < -1
                        index = @taggedProducts.length - 1
                        if App.support.mobile()
                            @carouselRegion.currentView.index = Math.min(
                                $('.stl-look').children().length - 1,
                                @carouselRegion.currentView.index + 1
                            )
                    # swipe from first product to content
                    else if index is -1 and App.support.mobile()
                        @carouselRegion.currentView.index = Math.max(
                            0,
                            @carouselRegion.currentView.index - 1
                        )
                else if direction is 'left'
                    index++
                    # swipe from last product to content
                    if index is @taggedProducts.length
                        index = -1
                        if App.support.mobile()
                            @carouselRegion.currentView.index = Math.max(
                                0, 
                                @carouselRegion.currentView.index - 1
                            )
                    else if index is 0 and App.support.mobile()
                        @carouselRegion.currentView.index = Math.min(
                            $('.stl-look').children(':visible').length - 1,
                            @carouselRegion.currentView.index + 1
                        )
                @taggedProductIndex = index
                @renderView()
            return @

        destroy: ->
            unless App.support.mobile()
                $(document.body).removeClass("no-scroll")

            @$(".stick-bottom").waypoint("destroy")
            @$el.find(".look-product-carousel").swipe("destroy")
            return


    class module.PreviewContent extends module.ExpandedContent
        # Content inside a PreviewWindow or HeroAreaView
        template: "#tile_preview_template"
        templates: ->
            templateRules = [
                # supported contexts: options, data
                "#<%= options.store.slug %>_<%= data.template %>_mobile_preview_template"
                "#<%= data.template %>_mobile_preview_template"
                "#<%= options.store.slug %>_<%= data.template %>_preview_template"
                "#<%= data.template %>_preview_template"
                "#product_mobile_preview_template"
                "#product_preview_template"
                "#tile_mobile_preview_template" # fallback
                "#tile_preview_template" # fallback
            ]
            unless App.support.mobile()

                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            templateRules

        onRender: ->
            # hide discovery, then show this window as a page.
            if App.support.mobile()
                @trigger("swap:feed", @$el) # out of scope
                @trigger("feed:swapped")
            App.vent.trigger("previewRendered", @)
            return


        # Disable scrolling body when preview is shown
        onShow: ->
            super

            unless App.support.mobile()
                width = Marionette.getOption(@, "width")
                if width
                    @$(".content").css("width", width + "px")
                else if App.support.mobile()
                    @$el.width($window.width()) # assign width

                # if it's a real preview, add no-scroll
                unless @$el.parents("#hero-area").length
                    @trigger("scroll:disable")
            return


    ###
    Container view for a PreviewContent object.

    @constructor
    @type {LayoutView}
    ###
    class module.PreviewWindow extends Marionette.LayoutView
        tagName: "div"
        className: "previewContainer"
        template: "#preview_container_template"
        templates: ->
            templateRules = [
                # supported contexts: options, data
                "#<%= options.store.slug %>_<%= data.template %>_mobile_preview_container_template"
                "#<%= data.template %>_mobile_preview_container_template"
                "#<%= options.store.slug %>_<%= data.template %>_preview_container_template"
                "#<%= data.template %>_preview_container_template"
                "#product_mobile_preview_container_template"
                "#product_preview_container_template"
                "#mobile_preview_container_template" # fallback
                "#preview_container_template" # fallback
            ]
            unless App.support.mobile()

                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            return templateRules

        regions:
            content: ".template.target"

        events:
            "click .close, .mask": ->
                # If we have been home then it's safe to use back()
                if App.initialPage == ''
                    Backbone.history.history.back()
                else
                    App.previewArea.empty()
                    category = App.intentRank.currentCategory()
                    route = if category then "category/#{category}" else ""
                    App.router.navigate(route,
                        trigger: false
                        replace: true
                    )
                return

        initialize: (options) ->
            @options = options
            return

        onMissingTemplate: ->
            @destroy()
            return

        templateHelpers: ->

        # return {data: $.extend({}, this.options, {template: this.template})};
        onRender: ->
            heightMultiplier = undefined

            # cannot declare display:table in marionette class.
            heightMultiplier = (if App.utils.portrait() then 1 else 2)
            @$el.css
                display: "table"
                height: (if App.support.mobile() then heightMultiplier * $window.height() else "")

            contentOpts = model: @options.model
            contentInstance = undefined
            contentInstance = new module.PreviewContent(contentOpts)

            # remember if $.fn.swapWith is called so the feed can be swapped back
            contentInstance.on("feed:swapped", =>
                @feedSwapped = true
                return
            )

            contentInstance.on("swap:feed", ($el) ->
                App.discoveryArea.$el.parent().swapWith($el)
                return
            )

            contentInstance.on("scroll:disable", ->
                $(document.body).addClass("no-scroll")
                return
            )

            @content.show(contentInstance)
            App.previewLoadingScreen.hide()

            @listenTo(App.vent, "window:rotate", (width) =>
                # On change in orientation, we want to rerender our layout
                # this is automatically unbound on close, so we don't have to clean
                heightMultiplier = (if App.utils.portrait() then 1 else 2)
                @$el.css(
                    height: (if App.support.mobile() then heightMultiplier * $window.height() else "")
                )
                if App.utils.landscape()
                    @$el.closest(".previewContainer").addClass("landscape")
                else
                    @$el.closest(".previewContainer").removeClass("landscape")
                if @content.currentView?
                    @content.currentView.resizeContainer()
                    # Refactor to use region.currentView.render
                    if @content.currentView.productInfo?.currentView
                        productRegion = @content.currentView.productInfo
                        productRegion.show(productRegion.currentView,
                            forceShow: true
                        )
                    if @content.currentView.carouselRegion?.currentView
                        carouselRegion = @content.currentView.carouselRegion
                        carouselRegion.show(carouselRegion.currentView,
                            forceShow: true
                        )
                return
            )

            @listenTo(App.vent, "window:resize", () =>
                @content.currentView?.resizeContainer()
                return
            )
            return

        positionWindow: ->
            windowMiddle = $window.scrollTop() + $window.height() / 2
            if App.windowMiddle
                windowMiddle = App.windowMiddle
            if App.windowHeight and App.support.mobile()
                @$el.css("height", App.windowHeight)
            @$el.css("top", Math.max(windowMiddle - (@$el.height() / 2), 0))

        onShow: ->
            @image_load = imagesLoaded(@$el)
            @listenTo(@image_load, 'always', =>
                @positionWindow()
            )
            return

        onDestroy: ->
            # hide this, then restore discovery.
            if @feedSwapped
                @$el.swapWith(App.discoveryArea.$el.parent())

                # handle results that got loaded while the discovery
                # area has an undefined height.
                App.feed.layout(App.discovery)
                App.feed.masonry.resize()
            return
