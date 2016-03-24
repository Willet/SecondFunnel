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

    class module.ProductView extends Marionette.LayoutView
        template: "#product_info_template"
        templates: ->
            templateRules = [
                # supported contexts: options (App.options), data (@mdoel.attributes)
                "#<%= data.parentTemplate %>_info_template"
                "#image_info_template"
                "#product_info_template"
            ]
            unless App.support.mobile()
                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            return templateRules


        events:
            'click .item': (ev) ->
                $selectedItem = $(ev.target)
                @galleryIndex = $selectedItem.data("index")
                @scrollImages(@mainImage.width()*@galleryIndex)
                @updateGallery()

                @triggerMethod('click:imageView')
                return

            'click .gallery-swipe-left, .gallery-swipe-right': (ev) ->
                $target = $(ev.currentTarget)
                unless $target.hasClass("grey")
                    if $target.hasClass("gallery-swipe-left")
                        @galleryIndex = Math.max(@galleryIndex - 1, 0)
                    else
                        @galleryIndex = Math.min(@galleryIndex + 1, @numberOfImages - 1)
                    @scrollImages(@mainImage.width()*@galleryIndex)
                    @updateGallery()

                    @triggerMethod('click:imageView')
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
                url = $target.attr('href')

                if $target.hasClass('find-store')
                    @triggerMethod('click:findStore')
                else
                    @triggerMethod('click:buy')

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
                url = $target.attr('href')

                @triggerMethod('click:moreInfo')
                App.utils.openUrl(url)
                # Stop propogation to avoid double-opening url
                return false

            'click .back': (ev) ->
                @triggerMethod('click:back')

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
            @updateGallery()
            if @numberOfImages > 1
                @scrollImages(@mainImage.width()*@galleryIndex, 0)
                @mainImage.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
            else
                @$el.find(".item").hide() # Hide all gallery dots
            return

        replaceImages: ->
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

            for imageEl, i in @$el.find(".main-image .image")
                $image = $(imageEl)
                # find image from id
                image = _.findWhere(@model.get('images'), id: $image.data('id'))
                if image
                    imageUrl = image.resizeForDimens(maxWidth, maxHeight)
                
                if imageUrl?
                    if $image.is("img")
                        $image.attr("src", imageUrl)
                    else if $image.is("div")
                        $image.css("background-image", "url('#{imageUrl}')")
                else
                    console.warn("Can't get resized image for %O", @)
            return

        resizeProductImages: ->
            productImages = @$el.find(".main-image .image")
            if productImages.length > 0 and productImages.first().is("div")
                # Let the browser execute the resizing window callbacks
                # otherwise, container height is 0 & images are resized to 0 height.
                setTimeout((=> @replaceImages()), 1)
            else
                imagesLoaded(productImages, (=> @replaceImages()))
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
            if @numberOfImages > 1
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
            else
                @leftArrow.addClass("grey")
                @rightArrow.addClass("grey")
            return


    ###
    View for product thumbnails in a preview or hero area
    
    @constructor
    @type {ItemView}
    ###
    class module.ProductThumbnailsView extends module.CarouselView
        className: "thumbnails-container"
        template: "#product_thumbnails_template"
        getTemplate: -> return @template

        onRender: -> return

        selectItem: (index) ->
            @$el.find(".stl-item").filter("[data-index=#{index}]")
                .addClass("selected").siblings().removeClass("selected")

        deselectItems: () ->
            @$el.find(".stl-item").removeClass("selected")


    ###
    Similar product should have a tile-id attribute to allow continuous browsing
    ###
    class module.SimilarProductView extends Marionette.ItemView
        type: "SimilarProductView"
        tagName: "div"
        className: "tile product"
        id: -> return @model.cid
        template: "#similar_product_template"

        initialize: ->
            @$el.attr(
                "data-id": @model.get('id')
                "data-sku": @model.get('sku')
            )
        triggers:
            "click": "click" # trigger parentview


    ###
    Similar products look like tiles in a feed

    Options:
        template - expose parent template name to similar products template
    ###
    class module.SimilarProductsView extends Marionette.CompositeView
        type: "SimilarProductsView"
        childView: module.SimilarProductView
        childViewContainer: ".tiles"
        template: "#similar_products_template"

        initialize: (options) ->
            @collection = new module.ProductCollection(options['products'])

            if options.template
                @templateHelpers =
                    parentTemplate: options.template

        childEvents:
            "click": (childView) ->
                @triggerMethod('click:similarProduct', childView.model.get('id'))
                #if @model.get('sku', false)
                    # open tile in hero area
                    #if App.option("page:tiles:openTileInHero", false)
                    #    App.router.navigate("tile/#{String(@model.get('tile-id'))}", trigger: true)
                    # open tile in popup
                    #else
                    #    App.router.navigate("preview/#{String(@model.get('tile-id'))}", trigger: true)
                    #App.router.navigate("sku/#{String(@model.get('sku'))}", trigger: true)
                #else
                    # go to PDP
                    #App.utils.openUrl(@model.get("url"))


    ###
    Shop The Image or Shop The Product container

    @constructor
    @type {LayoutView}
    ###
    class module.ExpandedContent extends Marionette.LayoutView
        ###
        A container for viewing a tile.  If the tile has a product attribute,
        it is treated as a product view (product featured, tagged products in 
        thumbnails carousel).  If the tile does not, it is treated as a content view (content
        featured, tagged products in thumbnails carousel).
        ###
        id: -> return "preview-#{@model.cid}"
        className: "preview-container"
        regions:
            productInfo: ".product-info"
            productThumbnails: ".product-thumbnails"
            similarProducts: ".similar-products"

        ui:
            # merge .product-info into .info, .product-thumbnails into .shop
            productInfo: ".info" # region
            productThumbnails: ".shop" # region
            similarProducts: ".similar-products" # region
            lookImage: ".look-image-container" # convert to region?
            lookThumbnail: ".look-thumbnail"
            lookProductCarousel: ".look-product-carousel" # mobile only, contains lookImage and productInfo

        defaultOptions:
            # productThumbnails: show thumbnails carousel below products / images
            showThumbnails: true
            # previewFeed: have an overflowing tile feed in the pop-up instead of thumbnails
            previewFeed: false
            # featureSingleItem: display only one thing (image, product, etc) at a time on desktop
            featureSingleItem: false
            # showLookThumbnail: show look thumbnail in carousel when tagged product selected
            showLookThumbnail: true
            # when a preview has overflow, what percentage of the viewport should the feature take up
            overflowFeaturePercent: '80%'

        events:
            "click @ui.lookThumbnail": (event) ->
                # Look thumbnail is generally only visible/clickable on mobile
                # when it is in the thumbnail carousel
                @taggedProductIndex = -1
                @updateContent()
                return

            "click .stl-look .stl-item": (event) ->
                $ev = $(event.target)
                $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
                @taggedProductIndex = $targetEl.data("index")

                unless @ui.lookThumbnail.is(':visible')
                    @productThumbnails.currentView.index = Math.min(
                        $('.stl-look').children(':visible').length - 1,
                        @productThumbnails.currentView.index + 1
                    )
                if App.support.mobile()
                    # Scroll up to product view
                    $('body').scrollTo(".cell.info", 500)

                @updateContent()

                App.vent.trigger('tracking:product:thumbnailClick',
                    @getTrackingData(@model.get("taggedProducts")[@taggedProductIndex]))
                return

        # Attach tracking info to child events - attach correct product
        # When Behaviors can read LayoutView childEvents, this can be replaced with
        # module.behavior.childProductViewTracking
        childEvents:
            "click:imageView": (childView) ->
                App.vent.trigger("tracking:product:imageView", @getTrackingData(childView.model))
            "click:moreInfo": (childView) ->
                App.vent.trigger("tracking:product:moreInfoClick", @getTrackingData(childView.model))
            "click:findStore": (childView) ->
                App.vent.trigger("tracking:product:findStoreClick", @getTrackingData(childView.model))
            "click:buy": (childView) ->
                App.vent.trigger("tracking:product:buyClick", @getTrackingData(childView.model))
            "click:similarProduct": (childView, productId) ->
                @taggedProductIndex = _.findIndex(@taggedProducts, 
                                                  (prod) -> return prod.get('id') is productId)
                @resizeContainer()
                @$el.animate(scrollTop: 0, 1000)
                App.vent.trigger("tracking:product:thumbnailClick",
                                 @getTrackingData(@taggedProducts[@taggedProductIndex]))
            "click:back": (childView) ->
                # Reload featured content/product
                @taggedProductIndex = -1
                if @options.previewFeed
                    @resizeContainer() # will call updateContent
                else
                    @updateContent()
                return

        getTrackingData: (product) ->
            return _.extend({}, @model.toJSON(), product: product)

        initialize: (options) ->
            # Order of priority for display options:
            # view options > model display options > default options
            optionsOptions = _.pick(options, _.keys(@defaultOptions))
            modelOptions = if @model.options? \
                           then _.pick(@model.options, _.keys(@defaultOptions)) \
                           else {}
            @options = _.extend({}, @defaultOptions, modelOptions, optionsOptions)
            # preview feed takes precedence over product thumbnails
            if @options.previewFeed
                @options.showThumbnails = false

            # Track which tagged product is being displayed
            @taggedProductIndex = @_currentIndex = undefined

            @product = @model.get('product') # could be undefined
            @taggedProducts = @model.get('taggedProducts') or []
            # order taggedProducts by price
            if @taggedProducts.length > 1
                @taggedProducts = _.sortBy(
                    @taggedProducts,
                    (obj) -> return -1 * parseFloat((obj.price or "$0").substr(1), 10)
                )
            return
        
        onBeforeRender: ->
            # Need to get an appropriate sized image
            if @model.get("defaultImage")?
                image = @model.get("defaultImage")
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
                
                # Get new resized image
                # TODO: delegated to a view for the look image
                if @model.get('template') isnt 'product'
                    if App.support.mobile()
                        image.height($window.height())
                    else
                        image.height(App.utils.getViewportSized(true))
            return

        updateContent: ->
            # Update the current view if its changed
            if @_currentIndex isnt @taggedProductIndex
                @_currentIndex = @taggedProductIndex
                if @taggedProductIndex is -1
                    if @product
                        # Featured product (ex: product tile)
                        @showProduct(@product)
                        @ui.lookImage.hide() # hide image
                    else
                        # Featured content (ex: image tile)
                        @showImage()

                    @ui.lookThumbnail.hide()

                    if @productThumbnails.hasView()
                        @productThumbnails.currentView.deselectItems()
                        if App.support.mobile()
                            @productThumbnails.currentView.index = Math.max(
                                0,
                                @productThumbnails.currentView.index - 1
                            )
                            @productThumbnails.currentView.calculateDistance()
                else
                    # Show tagged product
                    @showProduct(@taggedProducts[@taggedProductIndex])
                    if @options.featureSingleItem or App.support.mobile()
                        @ui.lookImage.hide() # hide image

                    if @options.showLookThumbnail or App.support.mobile()
                        # Some themes use have other links back to the main content/product
                        @ui.lookThumbnail.show()

                    if @productThumbnails.hasView()
                        @productThumbnails.currentView.selectItem(@taggedProductIndex)
                        if App.support.mobile()
                            @productThumbnails.currentView.calculateDistance()
            return

        ###
        Sizes the preview container, making the featured area sized
        to the viewport & allowing the overflow area to continue below the fold.
        Meant to be called when all images finish loading
        ###
        shrinkContainerCallback: ->
            # All images are loaded to frame content, render it now
            @updateContent()

            $window = $(window)
            $container = @$el.closest(".fullscreen")
            $containedItem = @$el.closest(".content")
            # Content that will be sized to the viewport
            $feature = if not $containedItem.find(".feature").length \
                       then $containedItem.find(".preview-container") \
                       else $containedItem.find(".feature").first()
            # Content that will run below the fold
            $overflow = $containedItem.find(".overflow")

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
                if not @productInfo.hasView() and not @productThumbnails.hasView()
                    # shrink wrap to content
                    # ex: collection tile -> single image with preview feed.
                    # There must be a better way to decide when to shrink-to-content vs scale-content
                    $feature.css('height', 'auto')
                else
                    $overflow.hide()
                    # Leave 25% of the viewport for the overflow to start
                    $feature.css('height', @options.overflowFeaturePercent)
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
                heightReduction = widthReduction = "0"
                
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

        resizeContainer: ->
            # shrinks container once main image product thumbnails are loaded
            imagesLoaded($("img.main-image, img.image", @$el),(=> @shrinkContainerCallback()))
            return

        # Disable scrolling body when preview is shown
        onShow: ->
            if @product
                # Product is featured (ex: product pop-up)
                @taggedProductIndex = -1
            else
                # Content is featured (ex: image pop-up)
                # Note: Content is contained in .look-image-container, loaded by template
                @taggedProductIndex = (if App.support.mobile() or @options.featureSingleItem \
                                       then -1 else 0)

            if App.support.mobile()
                if App.utils.landscape()
                    @$el.closest(".previewContainer").addClass("landscape")
                else
                    @$el.closest(".previewContainer").removeClass("landscape")
                @$el.find('.info').hide() # hide tagged product
                # enable swiping of thumbnails
                @ui.lookProductCarousel?.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
            else
                @$el.closest(".previewContainer").removeClass("landscape")
                # will be removed by shrinkCallback
                @$el.closest(".fullscreen").addClass("loading-images")
            
            if @taggedProducts.length
                if @options.previewFeed
                    @showSimilarProducts()
                    @ui.productThumbnails.hide()
                else if @options.showThumbnails
                    @showThumbnails()
                    @ui.similarProducts.hide()
                    # can replace with sibling selectors .shop:empty ~ .info
                    # when .product-info merged into .shop
                    @ui.productInfo.addClass('tagged')
                    if App.support.mobile()
                        @ui.lookProductCarousel?.addClass('tagged')
                        
            else
                # templates may not implement these if no tagged products
                @ui.productThumbnails?.hide()
                @ui.similarProducts?.hide()

            @resizeContainer()

            # If this is in a hero area, enable some of it to stick as scroll down(?)
            if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
                $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                    offset: "bottom-in-view"
                    direction: "up"
                )
            return

        showProduct: (product)->
            # A hook to customize product display
            @$el.find('.info').show() # display product before rendering
            product.set(parentTemplate: @model.get('template'))
            productInstance = new module.ProductView(
                model: product
            )
            @productInfo.show(productInstance)

        showImage: ->
            # A hook to customize image display
            # image will be displayed in .look-image-container, rendered by template
            @productInfo.empty()
            @ui.lookImage.show() # show image
            @$el.find('.info').hide() # hide product

        showThumbnails: ->
            # A hook to customize the thumbnails initialization
            if @taggedProducts.length > 1 or \
               (App.support.mobile() and @taggedProducts.length > 0)
                # Initialize carousel if this is mobile with tagged product
                # or desktop/tablet with more than one product
                thumbnailsInstance = new module.ProductThumbnailsView(
                    items: @taggedProducts
                    attrs:
                        'lookImageSrc': @model.get('defaultImage').url
                        'lookName': @model.get('defaultImage').get('name')
                        'orientation': @model.get('defaultImage').get('orientation')
                )
                @productThumbnails.show(thumbnailsInstance)
                @ui.lookThumbnail.hide()
            return

        showSimilarProducts: ->
            # A hook to customize the pop-up feed initialization
            if @taggedProducts.length > 0
                similarProductsInstance = new module.SimilarProductsView(
                    products: @taggedProducts
                    template: @model.get('template')
                )
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
                            @productThumbnails.currentView.index = Math.min(
                                $('.stl-look').children().length - 1,
                                @productThumbnails.currentView.index + 1
                            )
                    # swipe from first product to content
                    else if index is -1 and App.support.mobile()
                        @productThumbnails.currentView.index = Math.max(
                            0,
                            @productThumbnails.currentView.index - 1
                        )
                else if direction is 'left'
                    index++
                    # swipe from last product to content
                    if index is @taggedProducts.length
                        index = -1
                        if App.support.mobile()
                            @productThumbnails.currentView.index = Math.max(
                                0, 
                                @productThumbnails.currentView.index - 1
                            )
                    else if index is 0 and App.support.mobile()
                        @productThumbnails.currentView.index = Math.min(
                            $('.stl-look').children(':visible').length - 1,
                            @productThumbnails.currentView.index + 1
                        )
                @taggedProductIndex = index
                @updateContent()
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

        templateHelpers: ->
            return showFeed: @options.previewFeed

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
                # supported contexts: options -> App.options, data -> model.attributes
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

        defaultOptions:
            # Toggle content scroll
            scrollable: false

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
            if options.scrollable is undefined
                options.scrollable = Marionette.getOption(@options.model, 'previewFeed') \
                                     and not _.isEmpty(@options.model.get('taggedProducts'))
            @options = _.extend({}, @defaultOptions, options)
            return

        onMissingTemplate: ->
            @destroy()
            return

        templateHelpers: ->
            scrollable: @getOption('scrollable')

        onShow: ->
            # cannot declare display:table in marionette class.
            heightMultiplier = (if App.utils.portrait() then 1 else 2)
            @$el.css
                display: "table"
                height: (if App.support.mobile() then heightMultiplier * $window.height() else "")

            contentOpts = model: @options.model
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

            @_isMobilePreview = App.support.mobile() # track window state

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
                if @content.hasView()
                    if @_isMobilePreview is not App.support.mobile()
                        # rotation changed between mobile & desktop width
                        @_isMobilePreview = App.support.mobile()
                        # desktop & mobile have different templates, so switch between them
                        @content.show(@content.currentView,
                            forceShow: true
                        )
                    else
                        @content.currentView.resizeContainer()
                        if @content.currentView.productInfo?.hasView()
                            productRegion = @content.currentView.productInfo
                            productRegion.show(productRegion.currentView,
                                forceShow: true
                            )
                        if @content.currentView.productThumbnails?.hasView()
                            productThumbnails = @content.currentView.productThumbnails
                            productThumbnails.show(productThumbnails.currentView,
                                forceShow: true
                            )
                return
            )

            @listenTo(App.vent, "window:resize", () =>
                if @content.hasView()
                    if @_isMobilePreview is not App.support.mobile()
                        @_isMobilePreview = App.support.mobile()
                        # desktop & mobile have different templates, so switch between them
                        @content.show(@content.currentView,
                            forceShow: true
                        )
                    else
                        @content.currentView.resizeContainer()
                return
            )
            @image_load = imagesLoaded(@$el)
            @listenTo(@image_load, 'always', =>
                @positionWindow()
            )
            return

        positionWindow: ->
            windowMiddle = $window.scrollTop() + $window.height() / 2
            if App.windowMiddle
                windowMiddle = App.windowMiddle
            if App.windowHeight and App.support.mobile()
                @$el.css("height", App.windowHeight)
            @$el.css("top", Math.max(windowMiddle - (@$el.height() / 2), 0))

        onDestroy: ->
            # hide this, then restore discovery.
            if @feedSwapped
                @$el.swapWith(App.discoveryArea.$el.parent())

                # handle results that got loaded while the discovery
                # area has an undefined height.
                App.feed.layout(App.discovery)
                App.feed.masonry.resize()
            return
