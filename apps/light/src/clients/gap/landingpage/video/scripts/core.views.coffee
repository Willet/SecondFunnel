"use strict"

swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::onShow = ->
        @leftArrow = @$el.find('.gallery-swipe-left')
        @rightArrow = @$el.find('.gallery-swipe-right')
        @mainImage = @$el.find('.main-image')
        @resizeProductImages()
        if @numberOfImages > 1
            @scrollImages(@mainImage.width()*@galleryIndex, 0)
            @updateGallery()
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
        "click .look-image": (event) ->
            $image = @$el.find(".look-image-container")
            $image.toggleClass("full-image")
            return

        "click .look-thumbnail": (event) ->
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @stlIndex = Math.max(@stlIndex - 1, 0)
            @lookProductIndex = -1
            if App.utils.landscape() then @arrangeStlItemsVertical() else @arrangeStlItemsHorizontal()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            @lookProductIndex = $targetEl.data("index")
            @updateCarousel()
            App.vent.trigger('tracking:stlItemClick', @model.get("tagged-products")[@lookProductIndex])
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
        height = "95%"
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
                height = "90%"
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
        @leftArrow.hide()
        @rightArrow.hide()
        if @model.get("tagged-products")?.length > 1 or App.support.mobile()
            if App.support.mobile() or @model.orientation is "landscape"
                height = "95%"
                top = "0"
                unless @stlIndex is 0
                    height = "90%"
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
        @upArrow.hide()
        @downArrow.hide()
        if @model.get("tagged-products")?.length > 1 or App.support.mobile()
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
                if App.support.mobile()
                    if App.utils.portrait()
                        @arrangeStlItemsHorizontal()
                    else
                        @arrangeStlItemsVertical()
                    return

                tableHeight = undefined
                numProducts = @model.get("tagged-products").length
                if @model.get("template") is "image" or @model.get("template") is "gif"
                    if (@model.get("orientation") is "landscape" and numProducts > 1) or @model.get("orientation") is "portrait"
                        tableHeight = if $container.height() then $container.height() else $containedItem.height()
                    else
                        tableHeight = (if $container.width() then $container.width() else $containedItem.width())*0.496
                    $table.css(
                        height: tableHeight
                    )
                    if @model.get("template") is "image" and @model.get("images")?.length > 0
                        size = @model.get("sizes")?.master
                        $lookImage = @$el.find(".look-image")
                        imageUrl = App.utils.getResizedImage(@model.get("url", ""), 
                            width: Math.min(size?.width or 0, ($lookImage.width()*1.5)),
                            height: Math.min(size?.height or 0, ($lookImage.height()*1.5))
                        )
                        $lookImage.css("background-image", "url(#{imageUrl})")

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
                if @model.get("orientation") is "landscape"
                    @arrangeStlItemsHorizontal()
                else
                    @arrangeStlItemsVertical()
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
            @lookThumbnail = @$el.find('.look-thumbnail')
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find(".look-product-carousel").swipe(
                triggerOnTouchEnd: true,
                swipeStatus: _.bind(@swipeStatus, @),
                allowPageScroll: 'vertical'
            )
        if @model.get("tagged-products")?.length > 0
            @stlIndex = 0
            @lookProductIndex = if App.support.mobile() then -1 else 0
            @leftArrow = @$el.find('.stl-swipe-left')
            @rightArrow = @$el.find('.stl-swipe-right')
            @upArrow = @$el.find(".stl-swipe-up")
            @downArrow = @$el.find(".stl-swipe-down")
        if @model.get("sizes")?.master
            width = @model.get("sizes").master.width
            height = @model.get("sizes").master.height
            if Math.abs((height-width)/width) <= 0.02
                @model.set("orientation", "square")
            else if width > height
                @model.set("orientation", "landscape")
            else
                @model.set("orientation", "portrait")
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
        if @lookProductIndex >= 0
            unless (direction is 'left' and productImageIndex is numberOfImages) or (direction is 'right' and productImageIndex is 0)
                @productInfo.currentView.swipeStatus(event, phase, direction, distance, fingers, duration)
                return
        if phase is 'end'
            if direction is 'right'
                @lookProductIndex--
                if (@lookProductIndex < -1 and App.support.mobile()) or (@lookProductIndex < 0 and not App.support.mobile())
                    @lookProductIndex = @$el.find(".stl-look").children(":visible").length - 1
            else if direction is 'left'
                @lookProductIndex++
                if @lookProductIndex is @model.get("tagged-products")?.length
                    @lookProductIndex = if App.support.mobile() then -1 else 0
            @updateCarousel()
        return @

    module.ExpandedContent::updateCarousel = ->
        if App.support.mobile() and @lookProductIndex < 0
            if @lookThumbnail.is(":visible")
                @stlIndex = Math.max(0, @stlIndex - 1)
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @$el.find(".stl-item").removeClass("selected")
            if App.utils.landscape() then @arrangeStlItemsVertical() else @arrangeStlItemsHorizontal()
        else
            @$el.find(".stl-item").filter("[data-index=#{@lookProductIndex}]")
                .addClass("selected").siblings().removeClass("selected")
            productInstance = new module.ProductView(
                model: new module.Product(@model.get("tagged-products")[@lookProductIndex])
            )
            @productInfo.show(productInstance)
            if App.support.mobile()
                unless @lookThumbnail.is(":visible")
                    @stlIndex = Math.min($(".stl-look").children(":visible").length - 1, @stlIndex + 1)
                @lookThumbnail.show()
                @$el.find('.info').show()
                @$el.find('.look-image-container').hide()
                if App.utils.landscape() then @arrangeStlItemsVertical() else @arrangeStlItemsHorizontal()
        return
