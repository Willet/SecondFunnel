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
            else if @galleryIndex is @numberOfImages - 1
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

    module.ExpandedContent.prototype.events =
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
            @gallery.show(productInstance)  

            if $el.parents("#hero-area").length
                # this is a featured content area
                App.options.heroGalleryIndex = index
                App.options.heroGalleryIndexPage = 0
            productInstance = new module.ProductView(
                model: productModel
            )
            @gallery.show(productInstance)            
            return

        'click .stl-swipe-down, .stl-swipe-up': (ev) ->
            stlItems = @$el.find(".stl-item")
            stlContainer = @$el.find(".stl-look-container")
            containerHeight = stlContainer.offset().top + stlContainer.height()
            index = undefined
            margin = 0
            for item, i in stlItems
                itemHeight = $(item).offset().top + $(item).height()
                ## Find first visible item ##
                if itemHeight < containerHeight
                    index = i
                    if ev.target.className is "stl-swipe-up"
                        margin = 30 unless index is 0 ## 30px padding ##
                    else
                        margin = stlContainer.height()*(-1)
                    break
            unless index is undefined
                upArrow = @$el.find(".stl-swipe-up")
                downArrow = @$el.find(".stl-swipe-down")
                upArrow.hide()
                downArrow.hide()
                $(stlItems[index]).animate({"marginTop": margin}, 250, "swing", =>
                    ## TODO: May want to turn this into a private method? ##
                    lastItemHeight = stlItems.last().offset().top + stlItems.last().height()
                    firstItemHeight = stlItems.first().offset().top + stlItems.first().height()
                    if firstItemHeight > stlContainer.offset().top then upArrow.hide() else upArrow.show()
                    if lastItemHeight < stlContainer.offset().top + stlContainer.height() then downArrow.hide() else downArrow.show()
                )
            return

        'click .stl-swipe-left, .stl-swipe-right': (ev) ->
            stlItems = @$el.find(".stl-item")
            stlContainer = @$el.find(".stl-look-container")
            containerWidth = stlContainer.offset().left + stlContainer.width()
            index = undefined
            margin = 0
            for item, i in stlItems
                itemWidth = $(item).offset().left + $(item).width()
                if itemWidth < containerWidth
                    index = i
                    if ev.target.className is "stl-swipe-left"
                        margin = 15 unless index is 0
                    else
                        margin = stlContainer.width()*(-1)
                    break
            unless index is undefined
                leftArrow = @$el.find(".stl-swipe-left")
                rightArrow = @$el.find(".stl-swipe-right")
                leftArrow.hide()
                rightArrow.hide()
                $(stlItems[index]).animate({"marginLeft": margin}, 250, "swing", =>
                    lastItemWidth = stlItems.last().offset().left + stlItems.last().width()
                    firstItemWidth = stlItems.first().offset().left + stlItems.first().width()
                    if firstItemWidth > stlContainer.offset().left then leftArrow.hide() else leftArrow.show()
                    if lastItemWidth < stlContainer.offset().left + stlContainer.width() then rightArrow.hide() else rightArrow.show()
                )
            return

    module.ExpandedContent::arrangeStlItemsVertical = ($element) ->
        upArrow = $element.find(".stl-swipe-up")
        downArrow = $element.find(".stl-swipe-down")
        stlItems = $element.find(".stl-item")
        stlContainer = $element.find(".stl-look-container")
        containerHeight = stlContainer.offset().top + stlContainer.height()
        for item, i in stlItems
            itemHeight = $(item).offset().top + $(item).height()
            if itemHeight > (containerHeight - 20) ## position of down arrow at 20px ##
                unless $(item).offset().top is (stlContainer.offset().top + stlContainer.height() + 20)
                    $(item).css(
                        ## position of arrow + padding ##
                        "margin-top": stlContainer.offset().top + stlContainer.height() - $(item).offset().top + 50
                    )
                containerHeight += stlContainer.height()    
        lastItemHeight = stlItems.last().offset().top + stlItems.last().height()
        firstItemHeight = stlItems.first().offset().top + stlItems.first().height()
        if firstItemHeight > stlContainer.offset().top then upArrow.hide() else upArrow.show()
        if lastItemHeight < stlContainer.offset().top + stlContainer.height() then downArrow.hide() else downArrow.show()
        return

    module.ExpandedContent::arrangeStlItemsHorizontal = ($element) ->
        leftArrow = $element.find(".stl-swipe-left")
        rightArrow = $element.find(".stl-swipe-right")
        stlItems = $element.find(".stl-item")
        stlContainer = $element.find(".stl-look")
        containerWidth = stlContainer.offset().left + stlContainer.width()
        for item, i in stlItems
            itemWidth = $(item).offset().left + $(item).width()
            if itemWidth > (containerWidth - 15)
                unless $(item).offset().left is (stlContainer.offset().left + stlContainer.width() + 15)
                    $(item).css(
                        "margin-left": stlContainer.offset().left + stlContainer.width() - $(item).offset().left + 45
                    )
                stlContainer.css(
                    "text-align": "left"
                )
                containerWidth += stlContainer.width()
        lastItemWidth = stlItems.last().offset().left + stlItems.last().width()
        firstItemWidth = stlItems.first().offset().left + stlItems.first().width()
        if firstItemWidth > stlContainer.offset().left then leftArrow.hide() else leftArrow.show()
        if lastItemWidth < stlContainer.offset().left + stlContainer.width() then rightArrow.hide() else rightArrow.show()
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
                    unless tileType == "product"
                        if (orientation == "landscape" and numImages > 1) or orientation == "portrait"
                            tableHeight = if container.height() then container.height() else containedItem.height()
                        else
                            tableHeight = (if container.width() then container.width() else containedItem.width())*0.496
                        table.css(
                            height: tableHeight
                        )

                    # loading hero area
                    unless container and container.length
                        if orientation == "landscape"
                            $element.find('#hero-area')
                            @arrangeStlItemsHorizontal($element)
                        else
                            @arrangeStlItemsVertical($element)
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
                    if heightReduction <= 0 or App.support.mobile() # String because jQuery checks for falsey values
                        heightReduction = "0"
                    widthReduction -= containedItem.outerWidth()
                    widthReduction /= 2
                    if widthReduction <= 0 or App.support.mobile() # String because jQuery checks for falsey values
                        widthReduction = "0"
                    container.css(
                        top: heightReduction
                        bottom: heightReduction
                        left: widthReduction
                        right: widthReduction
                    )
                    if orientation == "landscape"
                        @arrangeStlItemsHorizontal($element)
                    else
                        @arrangeStlItemsVertical($element)
                return

        imageCount = $("img.main-image, img.image", @$el).length
        tileType = @model.get("template")
        orientation = @model.get("orientation")
        if @model.get("sizes")?.master
            width = @model.get("sizes").master.width
            height = @model.get("sizes").master.height
            if Math.abs((height-width)/width) <= 0.02
                orientation = "square"
            else if width > height
                orientation = "landscape"

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
        if App.support.mobile() and @model.get("tagged-products")?.length > 0
            productsInstance = new module.ProductCollectionView(@model.get("tagged-products"))
            @gallery.show(productsInstance)
        else if @model.get("tagged-products")?.length > 0
            productInstance = new module.ProductView(
                model: new module.Product(@model.get("tagged-products")[0])
            )
            @gallery.show(productInstance)
        @resizeContainer()

        if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
            $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                offset: "bottom-in-view"
                direction: "up"
            )
        return
