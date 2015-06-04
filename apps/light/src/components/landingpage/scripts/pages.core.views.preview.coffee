"use strict"

imagesLoaded = require('imagesLoaded')
swipe = require('jquery-touchswipe')
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

                # Over-write addUrlTrackingParameters for each customer
                url = App.utils.addUrlTrackingParameters( $target.attr('href') )
                App.utils.openUrl(url)
                # Stop propogation to avoid double-opening url
                return false

        initialize: ->
            @numberOfImages = @model.get('images')?.length or 0
            @galleryIndex = 0
            return

        onRender: ->
            # Get rid of that pesky wrapping-div
            @$el = @$el.children() # NOTE 1st child will be come element, all other children will be dropped
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
    @type {Layout}
    ###
    class module.ExpandedContent extends Marionette.Layout
        regions:
            productInfo: ".product-info"
            carouselRegion: ".carousel-region"
            similarProducts: ".similar-products"

        events:
            "click .stl-look .stl-item": (event) ->
                $el = @$el
                $ev = $(event.target)
                $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
                
                @taggedProductIndex = $targetEl.data("index")
                
                if App.support.mobile()
                    $('body').scrollTo(".cell.info", 500)
                product = @renderView()

                App.vent.trigger('tracking:product:thumbnailClick', product)
                return

        initialize: ->
            @$el.attr
                id: "preview-#{@model.cid}"
                class: "preview-container"
            @_currentIndex = -1 # Track which product is being displayed

            # Product pop-up
            if @model.get("template") == "product"
                @product = new module.Product(@model.attributes)
                @taggedProductIndex = -1
                    
            # Content pop-up
            else
                # Content is contained in .look-image-container, loaded by template
                # Load up zeroth tagged product
                @taggedProductIndex = 0

            if @model.get("tagged-products") and @model.get("tagged-products").length > 1
                # order tagged-products by price
                @model.set("tagged-products", _.sortBy(@model.get("tagged-products"), (obj) ->
                    -1 * parseFloat((obj.price or "$0").substr(1), 10)
                ))
                @taggedProducts = (new module.Product(product) for product in @model.get('tagged-products'))
            else
                @taggedProducts = []
            return
        
        onBeforeRender: ->
            # orient image
            if @model.get("sizes")?.master
                width = @model.get("sizes").master.width
                height = @model.get("sizes").master.height
                if Math.abs((height-width)/width) <= 0.02
                    @model.set("orientation", "square")
                else if width > height
                    @model.set("orientation", "landscape")
                else
                    @model.set("orientation", "portrait")
            # Need to get an appropriate sized image
            image = $.extend(true, {}, @model.get("defaultImage").attributes)
            image = new module.Image(image)
            if App.support.mobile()
                image.url = image.height($window.height())
            else
                image = image.height(App.utils.getViewportSized(true), true)

            # templates use this as obj.image.url
            @model.set("image", image)
            return

        # Updating the current view with product or tagged product
        # Returns product that is currently displayed
        renderView: () ->
            if @taggedProductIndex is not @_currentIndex
                if -1 < @taggedProductIndex < @taggedProducts.length
                    @_currentIndex = @taggedProductIndex
                    @carouselRegion.currentView.selectItem(@taggedProductIndex)
                    product = @taggedProducts[@taggedProductIndex]
                else
                    @_currentIndex = @taggedProductIndex = -1
                    @carouselRegion.currentView.deselectItems()
                    if @product?
                        product = @product

            if product
                productInstance = new module.ProductView(
                    model: product
                )
                @productInfo.show(productInstance)
                @$el.find('.info').show()
            else
                # Neither product or tagged product
                @productInfo.empty()
                @$el.find('.info').hide()
            # Return model of product being displayed
            return product

        # Returns a callback that sizes the preview container, making the featured area sized
        # to the viewport & allowing the overflow area to continue below the fold.
        # Meant to be called when all images finish loading
        shrinkContainerCallback: ->
            =>
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
                
                # must wait for all images to load
                if --@_imageCount isnt 0
                    return

                # All images are loaded to frame content, render it now
                @renderView()

                ### THIS CODE SHOULD EXIST SOMEWHERE ELSE ###
                if @model.get("type") is "image" or @model.get("type") is "gif"
                    if @lookProductIndex > -1
                        @$el.find(".look-thumbnail").show()
                    else
                        @$el.find(".look-thumbnail").hide()

                $container.css(
                    top: "0"
                    bottom: "0"
                    left: "0"
                    right: "0"
                )
                # Reset feature and container height
                $containedItem.css(
                    'height': '100%'
                    'max-height': '640px'
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
                    maxHeightValue = 'none'
                    heightReduction =  10
                    widthReduction = ($window.width() - $containedItem.outerWidth()) / 2
                else
                    # Content fits in window, center it
                    heightValue = '100%'
                    maxHeightValue = 640
                    heightReduction = ($window.height() - $containedItem.outerHeight()) / 2
                    widthReduction = ($window.width() - $containedItem.outerWidth()) / 2
                    if heightReduction <= 0 # String because jQuery checks for falsey values
                        heightReduction = "0"
                    if widthReduction <= 0 # String because jQuery checks for falsey values
                        widthReduction = "0"
                if App.support.mobile()
                    heightReduction = widthReduction = 0
                    maxHeightValue = 'none'
                    
                $container.css(
                    left: widthReduction
                    right: widthReduction
                )
                $containedItem.css(
                    'height': heightValue
                    'max-height': maxHeightValue
                    'margin-top': heightReduction
                    'margin-bottom': heightReduction
                )
                $container.removeClass("loading-images")
                @updateScrollCta()
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
            unless App.support.mobile()
                @$el.closest(".fullscreen").addClass("loading-images")

            # Initialize carousel
            if not _.isEmpty(@taggedProducts)
                carouselInstance = new module.CarouselView(
                    items: @model.get('tagged-products')
                    attrs:
                        'lookImageSrc': @model.get('images')[0].url
                        'lookName': @model.get('name')
                )
                @carouselRegion.show(carouselInstance)

                # Add some logic here to decide if carouselview or similarproductsview
                    #similarProductsInstance = new module.SimilarProductsView(@model.get("tagged-products"))
                    #@similarProducts.show(similarProductsInstance)

            @resizeContainer()

        close: ->
            # See NOTE in onShow
            unless App.support.mobile()
                $(document.body).removeClass("no-scroll")

            @$(".stick-bottom").waypoint("destroy")
            return


    ###
    Contents inside a PreviewWindow

    @constructor
    @type {Layout}
    ###
    class module.PreviewContent extends module.ExpandedContent

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

            #  NOTE: Previously, it was thought that adding `no-scroll`
            #  to android devices was OK, because no problems were observed
            #  on some device.
            #
            #  Turns out, that was wrong.
            #
            #  It seems like no-scroll prevent scrolling on *some* android
            #  devices, but not others.
            #
            #  So, for now, only add no-scroll if the device is NOT an android.
            #
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
    @type {Layout}
    ###
    class module.PreviewWindow extends Marionette.Layout
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
                    App.previewArea.close()
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
            @content.close()
            @close()
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
                if @content.currentView?.resizeContainer()
                    @content.currentView.resizeContainer()
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

        onClose: ->
            # hide this, then restore discovery.
            if @feedSwapped
                @$el.swapWith(App.discoveryArea.$el.parent())

                # handle results that got loaded while the discovery
                # area has an undefined height.
                App.feed.layout(App.discovery)
                App.feed.masonry.resize()
            return
