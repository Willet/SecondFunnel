"use strict"

swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.CarouselView::calculateDistanceOnLoad = ->
        calculateDistance = =>
            if --imageCount isnt 0
                return
            if App.support.mobile()
                if App.utils.landscape()
                    @calculateVerticalPosition()
                else
                    @calculateHorizontalPosition()
            else if @attrs['type'] is "herovideo"
                @calculateHorizontalPosition()
            else if @attrs['orientation'] is "landscape"
                @calculateHorizontalPosition()
            else if @attrs['orientation'] is "portrait"
                @calculateVerticalPosition()
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

    module.CarouselView::calculateHorizontalPosition = (direction='none') ->
        $container = @container
        $items = @slide.children(":visible")
        if direction is 'left'
            leftMostItem = $items[@index]
            unless leftMostItem is undefined
                # number of pixels needed to move leftmost item to the end of carousel
                difference = @container.width()
                index = _.findIndex($items, (item) ->
                    # true if item is visible after moving leftmost item
                    return Math.round($(item).width() + $(item).offset().left + difference) > Math.round($container.offset().left)
                )
        else if direction is "right"
            index = _.findIndex($items, (item) ->
                # true if item is only partially visible
                return Math.round($(item).width() + $(item).offset().left) > Math.round($container.width() + $container.offset().left)
            )
        else
            # reposition only if items overflow
            totalItemWidth = _.reduce($items, (sum, item) ->
                return sum + $(item).outerWidth()
            , 0)
            if totalItemWidth > @container.width()
                if @attrs['type'] is "herovideo"
                    distance = (@slide.offset().left + @slide.width()) - ($($items.get(@index)).offset().left + $($items.get(@index)).width())
                else
                    distance = @slide.offset().left - $($items.get(@index)).offset().left
            else
                distance = 0
            @updateCarousel(distance, "landscape", 0)
            return
        if index > -1
            @index = index
            if direction is "right" and @attrs['type'] is "herovideo"
                distance = (@slide.offset().left + @slide.width()) - ($($items.get(@index)).offset().left + $($items.get(@index)).width())
            else
                distance = @slide.offset().left - $($items.get(@index)).offset().left
            @updateCarousel(distance, "landscape")
        return

    module.ExpandedContent.prototype.events =
        "click .look-image": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
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
                    @updateContent()
                if @model.get("type") is "image" or @model.get("type") is "gif"
                    if @taggedProductIndex > -1
                        @$el.find(".look-thumbnail").show()
                    else
                        @$el.find(".look-thumbnail").hide()
                if App.support.mobile()
                    return
                tableHeight = undefined
                numProducts = @taggedProducts.length
                if @model.get("template") is "image" or @model.get("template") is "gif"
                    if (@model.get("orientation") is "landscape" and numProducts > 1) or @model.get("orientation") is "portrait"
                        tableHeight = if $container.height() then $container.height() else $containedItem.height()
                    else
                        tableHeight = (if $container.width() then $container.width() else $containedItem.width())*0.496
                    $table.css(
                        height: tableHeight
                    )
                    if @model.get("template") is "image" and @model.get("images")?.length > 0
                        $lookImage = @$el.find(".look-image")
                        imageUrl = App.utils.getResizedImage(@model.get("images")[0].url, 
                            width: $lookImage.width()*1.3,
                            height: $lookImage.height()*1.3
                        )
                        $lookImage.css("background-image", "url(#{imageUrl})")
                # loading hero area
                unless $container?.length
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
                $container.removeClass("loading-images")
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
        if not _.isEmpty(@taggedProducts) or App.support.mobile()
            # @stlIndex = 0
            carouselInstance = new module.CarouselView(
                items: @taggedProducts
                attrs:
                    'lookImageSrc': @model.get('defaultImage').url
                    'orientation': @model.get('defaultImage').get('orientation')
                    'landscape':
                        'height': '95%'
                    'portrait':
                        'fullHeight': '95%'
                        'reducedHeight': '90%'
            )
            @carouselRegion.show(carouselInstance)
            @$el.find('.look-thumbnail').hide()
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

    module.HeroContent.prototype.events =
        'click #more-button': ->
            numDefaultThumbnails = 1
            @$("#more-button").attr("style", "display: none;")
            table = @$(".thumbnail-table>tbody")[0]
            thumbnailTemplate = _.template("<td><div class='thumbnail-item' data-index='<%- i %>'>
                    <div class='thumbnail-image<% if (thumbnail.youtubeId) { %> playing<% } %>' style='background-image: url(\"<%= thumbnail.url %>\");'></div>
                    <p>Episode <%= i + 1 %> <br><%= thumbnail.date %></p>
                </div></td>")
            if table
                for thumbnail, i in @model.get('thumbnails') when i >= numDefaultThumbnails
                    thumbnailElem = thumbnailTemplate({ "thumbnail" : thumbnail, "i" : i })
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

    module.HeroContent::onShow = ->
        video = @model.get('video')
        if video?
            videoInstance = new module.YoutubeVideoView(video)
            @video.show(videoInstance)
        unless App.support.mobile()
            @leftArrow = @$el.find('.hero-swipe-left')
            @rightArrow = @$el.find('.hero-swipe-right')
            carouselInstance = new module.CarouselView(
                index: @model.get('thumbnails').length - 1,
                items: @model.get('thumbnails'),
                attrs:
                    'type': @model.get('type')
            )
            @carouselRegion.show(carouselInstance)
        return

    App.vent.once('tracking:videoFinish', (videoId, event) ->
        event.target.cuePlaylist(
            "listType": "list"
            "list": "PLGlQfj8yOxeh5TYm3LbIkSwUh9RMxJFwi"
        )
    )
