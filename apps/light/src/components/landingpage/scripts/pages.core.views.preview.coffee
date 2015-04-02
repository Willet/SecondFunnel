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
            @setElement(@$el.children())
            return

        onShow: ->
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


    class module.ProductCollectionView extends Marionette.CollectionView
        itemView: module.ProductView

        initialize: (products) ->
            @collection = new module.ProductCollection(products)
            return


    ###
    A Shop The Look

    @constructor
    @type {Layout}
    ###
    class module.ExpandedContent extends Marionette.Layout
        regions:
            productInfo: ".product-info"

        events:
            "click .stl-look .stl-item": (event) ->
                $el = @$el
                $ev = $(event.target)
                $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
                
                $targetEl.addClass("selected").siblings().removeClass "selected"
                index = $targetEl.data("index")
                product = @model.get("tagged-products")[index]
                productModel = new module.Product(product)
                productInstance = new module.ProductView(
                    model: productModel
                )
                if App.support.mobile()
                    $('body').scrollTo(".cell.info", 500)
                @productInfo.show(productInstance)

                App.vent.trigger('tracking:product:thumbnailClick', productModel)
                return
        
        onBeforeRender: ->
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

            if @model.get("tagged-products") and @model.get("tagged-products").length > 1
                @model.set("tagged-products", _.sortBy(@model.get("tagged-products"), (obj) ->
                    -1 * parseFloat((obj.price or "$0").substr(1), 10)
                ))

            # templates use this as obj.image.url
            @model.set("image", image)
            return

        initialize: ->
            @$el.attr
                id: "preview-#{@model.cid}"
                class: "preview-container"
            return

        close: ->
            # See NOTE in onShow
            unless App.support.isAnAndroid()
                $(document.body).removeClass("no-scroll")

            @$(".stick-bottom").waypoint("destroy")
            return

        resizeContainer: ->
            shrinkContainer = =>
                =>
                    unless App.support.mobile()
                        $container = @$el.closest(".fullscreen")
                        $containedItem = @$el.closest(".content")
                        if --imageCount isnt 0
                            return

                        # no container to shrink
                        unless $container?.length
                            return
                        if @model.get("template") is "image" and @model.get("images")?.length > 0
                            $lookImage = @$el.find(".look-image")
                            unless $lookImage.is("img")
                                imageUrl = App.utils.getResizedImage(@model.get("images")[0].url, 
                                    ## parameters are rounded to nearest 100th, ensure w/h >= than look image container's
                                    width: $lookImage.width()*1.3,
                                    height: $lookImage.height()*1.3
                                )
                                $lookImage.css("background-image", "url(#{imageUrl})")
                        $container.css(
                            top: "0"
                            bottom: "0"
                            left: "0"
                            right: "0"
                        )
                        heightReduction = ($window.height() - $containedItem.outerHeight()) / 2
                        widthReduction = ($container.outerWidth() - $containedItem.outerWidth()) / 2
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

        # Disable scrolling body when preview is shown
        onShow: ->
            if @model.get("tagged-products")?.length > 0
                productInstance = new module.ProductView(
                    model: new module.Product(@model.get("tagged-products")[0])
                )
                @productInfo.show(productInstance)
                @$el.find(".stl-item").filter("[data-index=0]").addClass("selected")
            else if @model.get("template") == "product"
                productInstance = new module.ProductView(
                    model: new module.Product(@model.attributes)
                )
                @productInfo.show(productInstance)
            unless App.support.mobile()
                @$el.closest(".fullscreen").addClass("loading-images")
            @resizeContainer()


    ###
    Contents inside a PreviewWindow.

    Content is displayed using a cascading level of templates, which
    increases in specificity.

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

            template = @options.model.get("template")
            contentOpts = model: @options.model
            contentInstance = undefined
            contentInstance = new module.PreviewContent(contentOpts)

            # remember if $.fn.swapWith is called so the feed can be swapped back
            contentInstance.on("feed:swapped", =>
                @triggerMethod("feed:swapped")
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

            @listenTo(App.vent, "rotate", (width) =>
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
                @content.currentView.resizeContainer()
                if @content.currentView?.productInfo?.currentView
                    productRegion = @content.currentView.productInfo
                    productRegion.show(productRegion.currentView,
                        forceShow: true
                    )
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


        # state-keeping for restoring feed previously swapped out
        onFeedSwapped: ->
            @feedSwapped = true
            return

