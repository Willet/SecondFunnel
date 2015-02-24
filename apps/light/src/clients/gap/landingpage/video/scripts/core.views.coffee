"use strict"

swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    class module.ProductCollection extends Backbone.Collection
        model: module.Product

    class module.ProductView extends Marionette.ItemView
        template: "#product_info_template"

        events:
            'click .product-swipe-left, .product-swipe-right': (ev) ->
                if ev.target.className is 'product-swipe-left'
                    @galleryIndex = Math.max(@galleryIndex - 1, 0)
                else 
                    @galleryIndex = Math.min(@galleryIndex + 1, @numberOfImages - 1)
                @scrollImages(@mainImage.width()*@galleryIndex)
                @updateGallery()
                return

        initialize: ->
            @numberOfImages = @model.get('images')?.length or 0
            @galleryIndex = 0
            return

        onRender: ->
            @setElement(@$el.children())

        onShow: ->
            @leftArrow = @$el.find('.product-swipe-left')
            @rightArrow = @$el.find('.product-swipe-right')
            @mainImage = @$el.find('.main-image')
            if @numberOfImages > 1
                @updateGallery()
                @mainImage.swipe(
                        triggerOnTouchEnd: true,
                        swipeStatus: _.bind(@swipeStatus, @),
                        allowPageScroll: 'vertical'
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
            @$el.find('.item')
                .removeClass('selected')
                .eq(@galleryIndex)
                .addClass('selected')
            if @galleryIndex is 0
                @leftArrow.hide()
                @rightArrow.show()
            else if @galleryIndex is @numberOfImages - 1
                @leftArrow.show()
                @rightArrow.hide()
            else
                @leftArrow.show()
                @rightArrow.show()
            return

    class module.ProductCollectionView extends Marionette.CollectionView
        itemView: module.ProductView

        initialize: (products) ->
            @collection = new module.ProductCollection(products)
            return

    module.HeroContent.prototype.events =
        'click #more-button': ->
            numDefaultThumbnails = 1
            @$("#more-button").attr("style", "display: none;")
            table = @$(".thumbnail-table>tbody")[0]
            thumbnailTemplate = "<td><div class='thumbnail-item' data-index='<%- i %>'>
                    <div class='thumbnail-image<% if (thumbnail.youtubeId) { %> playing<% } %>' style='background-image: url(\"<%= thumbnail.url %>\");'></div>
                    <p>Episode <%= i + 1 %> <br><%= thumbnail.date %></p>
                </div></td>"
            if table
                for thumbnail, i in @model.get('thumbnails') when i >= numDefaultThumbnails
                    thumbnailElem = _.template(thumbnailTemplate, { "thumbnail" : thumbnail, "i" : i })
                    table.insertRow(-1).innerHTML = thumbnailElem
            return

        'click .thumbnail-item': (ev) ->
            $ev = $(ev.target)
            if not $ev.hasClass('thumbnail-item')
                $ev = $ev.parent('.thumbnail-item')
            try
                i = $ev.data('index')
                thumbnails = @model.get('thumbnails')
                youtubeId = thumbnails[i]['youtubeId']
            catch error
                return
            finally
                unless youtubeId?
                    return

            App.vent.trigger("tracking:videoClick", youtubeId)

            # Youtube player may not yet be initialized
            player = @video?.currentView?.player
            if player?.cueVideoById
                @video.currentView.player.cueVideoById(String(youtubeId))?.playVideo()
            else
                App.vent.once('tracking:videoPlay', (videoId, event) ->
                    event.target.cueVideoById(String(youtubeId))?.playVideo()
                )

    App.vent.once('tracking:videoFinish', (videoId, event) ->
        event.target.cuePlaylist(
            "listType": "list"
            "list": "PLGlQfj8yOxeh5TYm3LbIkSwUh9RMxJFwi"
        )
    )

    module.ExpandedContent.prototype.regions =
        productInfo: ".product-info"

    module.ExpandedContent.prototype.events =
        "click .look-image": (event) ->
            image = @lookImage.find(".look-image-container")
            image.toggleClass("full-image")
            return

        "click .look-thumbnail": (event) ->
            @lookImage.show()
            @lookThumbnail.hide()
            @productDetails.hide()
            return

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
            @productInfo.show(productInstance)  

            if $el.parents("#hero-area").length
                # this is a featured content area
                App.options.heroGalleryIndex = index
                App.options.heroGalleryIndexPage = 0
            productInstance = new module.ProductView(
                model: productModel
            )
            @productInfo.show(productInstance)
            if App.support.mobile()
                @lookImage.hide()
                @lookThumbnail.show()
                @productDetails.show()
            return

        'click .stl-swipe-down, .stl-swipe-up': (ev) ->
            stlItems = @$el.find(".stl-item")
            stlContainer = @$el.find(".stl-look")
            containerHeight = stlContainer.offset().top + stlContainer.height()
            if ev.target.className is "stl-swipe-up"
                @stlGalleryIndex--
                distance = if @stlGalleryIndex > 0 then 30 + stlContainer.height*@stlGalleryIndex*(-1) else 0 ## 30px padding ##
            else        
                @stlGalleryIndex++
                distance = stlContainer.height()*@stlGalleryIndex*(-1)
            upArrow = @$el.find(".stl-swipe-up")
            downArrow = @$el.find(".stl-swipe-down")
            @updateStlGalleryPosition(distance)
            if @stlGalleryIndex is 0 then upArrow.hide() else upArrow.show()
            if @stlGalleryIndex is @stlGalleryCount then downArrow.hide() else downArrow.show()
            return

        'click .stl-swipe-left, .stl-swipe-right': (ev) ->
            stlItems = @$el.find(".stl-item")
            stlContainer = @$el.find(".stl-look")
            if ev.target.className is "stl-swipe-left"
                @stlGalleryIndex--
                distance = stlContainer.outerWidth()*@stlGalleryIndex*(-1)
            else    
                @stlGalleryIndex++
                distance = stlContainer.outerWidth()*@stlGalleryIndex*(-1)
            leftArrow = @$el.find(".stl-swipe-left")
            rightArrow = @$el.find(".stl-swipe-right")
            @updateStlGalleryPosition(distance)
            if @stlGalleryIndex is 0 then leftArrow.hide() else leftArrow.show()
            if @stlGalleryIndex is @stlGalleryCount then rightArrow.hide() else rightArrow.show()
            return

    module.ExpandedContent::updateStlGalleryPosition = (distance) ->
        if @model.get('orientation') is "landscape"
            translate3d = 'translate3d(' + distance + 'px, 0px, 0px)'
            translate = 'translateX(' + distance + 'px)'
        else
            translate3d = 'translate3d(0px, ' + distance + 'px, 0px)'
            translate = 'translateY(' + distance + 'px)'
        @$el.find('.stl-look').css(
            '-webkit-transition-duration': '0.3s',
            'transition-duration': '0.3s',
            '-webkit-transform': translate3d,
            '-ms-transform': translate,
            'transform': translate3d
        )
        return

    module.ExpandedContent::arrangeStlItemsVertical = ->
        @stlGalleryIndex = 0
        @stlGalleryCount = 0
        upArrow = @$el.find(".stl-swipe-up")
        downArrow = @$el.find(".stl-swipe-down")
        stlItems = @$el.find(".stl-item")
        stlContainer = @$el.find(".stl-look")
        containerHeight = stlContainer.offset().top + stlContainer.height()
        for item, i in stlItems
            itemHeight = $(item).offset().top + $(item).height()
            if itemHeight > (containerHeight - 15) ## position of down arrow at 15px ##
                unless $(item).offset().top is (containerHeight + 15)
                    $(item).css(
                        ## position of arrow + padding ##
                        "margin-top": containerHeight - $(item).offset().top + 45
                    )
                downArrow.show()
                @stlGalleryCount++
                containerHeight += stlContainer.height()    
        @updateStlGalleryPosition(0)
        upArrow.hide()
        return

    module.ExpandedContent::arrangeStlItemsHorizontal = ->
        @stlGalleryIndex = 0
        @stlGalleryCount = 0
        leftArrow = @$el.find(".stl-swipe-left")
        rightArrow = @$el.find(".stl-swipe-right")
        stlItems = @$el.find(".stl-item")
        stlContainer = $element.find(".stl-look")
        containerWidth = stlContainer.offset().left + stlContainer.outerWidth()
        for item, i in stlItems
            itemWidth = $(item).offset().left + $(item).width()
            if itemWidth > (containerWidth - 15)
                unless $(item).offset().left is (containerWidth + 15)
                    $(item).css(
                        "margin-left": containerWidth - $(item).offset().left + 30
                    )
                stlContainer.css(
                    "text-align": "left"
                )
                rightArrow.show()
                @stlGalleryCount++
                containerWidth += stlContainer.outerWidth()
        @updateStlGalleryPosition(0)
        leftArrow.hide()
        return

    module.ExpandedContent::resizeContainer = ->
        ###
        Returns a callback that sizes the preview container.
        ###
        shrinkContainer = ($element) =>
            =>
                unless App.support.mobile()
                    table = $element.find(".table")
                    container = $element.closest(".fullscreen")
                    containedItem = $element.closest(".content")
                    # must wait for all images to load
                    if --imageCount isnt 0
                        return

                    tableHeight = undefined
                    numImages = $element.find("img.image").length
                    unless @model.get("template") == "product"
                        if (@model.get("orientation") == "landscape" and numImages > 1) or @model.get("orientation") == "portrait"
                            tableHeight = if container.height() then container.height() else containedItem.height()
                        else
                            tableHeight = (if container.width() then container.width() else containedItem.width())*0.496
                        table.css(
                            height: tableHeight
                        )

                    # loading hero area
                    unless container and container.length
                        if @model.get("orientation") == "landscape"
                            @arrangeStlItemsHorizontal()
                        else
                            @arrangeStlItemsVertical()
                        return
                    container.css(
                        top: "0"
                        bottom: "0"
                        left: "0"
                        right: "0"
                    )

                    heightReduction = $(window).height()
                    widthReduction = $(window).width()
                    heightReduction -= containedItem.outerHeight()
                    heightReduction /= 2 # Split over top and bottom
                    if heightReduction <= 0 # String because jQuery checks for falsey values
                        heightReduction = "0"
                    widthReduction -= containedItem.outerWidth()
                    widthReduction /= 2
                    if widthReduction <= 0 # String because jQuery checks for falsey values
                        widthReduction = "0"
                    container.css(
                        top: heightReduction
                        bottom: heightReduction
                        left: widthReduction
                        right: widthReduction
                    )
                    if @model.get("orientation") == "landscape"
                        @arrangeStlItemsHorizontal()
                    else
                        @arrangeStlItemsVertical()
                return

        imageCount = $("img.main-image, img.image", @$el).length

        # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
        $("img.main-image, img.image", @$el).one("load", shrinkContainer(@$el)).each ->
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
            @lookImage = @$el.find('.look-image')
            @lookThumbnail = @$el.find('.look-thumbnail')
            @productDetails = @$el.find('.info')
            @lookThumbnail.hide()
            @productDetails.hide()
            if App.utils.landscape()
                @$el.closest(".previewContainer").addClass("landscape")
            else
                @$el.closest(".previewContainer").removeClass("landscape")
        if @model.get("sizes")?.master
            width = @model.get("sizes").master.width
            height = @model.get("sizes").master.height
            if Math.abs((height-width)/width) <= 0.02
                @model.attributes.orientation = "square"
            else if width > height
                @model.attributes.orientation = "landscape"
            else
                @model.attributes.orientation = "portrait"
        if @model.get("tagged-products")?.length > 0
            productInstance = new module.ProductView(
                model: new module.Product(@model.get("tagged-products")[0])
            )
            @productInfo.show(productInstance)
        @resizeContainer()

        if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
            $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                offset: "bottom-in-view"
                direction: "up"
            )
        return
