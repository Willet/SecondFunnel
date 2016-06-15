"use strict"

swipe = require('jquery-touchswipe')
Modernizr = require('modernizr')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    _.extend(module.ExpandedContent.prototype.events,
        "click .look-image": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent::shrinkContainerCallback = (forceUpdate=false) ->
        # Fits content to window, doesn't support overflow content
        $table = @$el.find(".table")
        $container = @$el.closest(".fullscreen")
        $containedItem = @$el.closest(".content")

        @updateContent(forceUpdate)

        if @model.get("type") is "image" or @model.get("type") is "gif"
            if @taggedProductIndex > -1
                @ui.lookThumbnail.show()
            else
                @ui.lookThumbnail.hide()
        
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
                imageUrl =  @model.get("images")[0].resizeForDimens($lookImage.width()*1.3,
                                                                    $lookImage.height()*1.3)
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

    module.ExpandedContent::showThumbnails = ->
        if @taggedProducts.length > 1 or \
           (App.support.mobile() and @taggedProducts.length > 0)
            # Make room for arrows
            thumbnailsInstance = new module.ProductThumbnailsView(
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
            @productThumbnails.show(thumbnailsInstance)
            @ui.lookThumbnail.hide()
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

    App.vent.once('tracking:videoFinish', (videoId, event) ->
        event.target.cuePlaylist(
            "listType": "list"
            "list": "PLGlQfj8yOxeh5TYm3LbIkSwUh9RMxJFwi"
        )
    )
