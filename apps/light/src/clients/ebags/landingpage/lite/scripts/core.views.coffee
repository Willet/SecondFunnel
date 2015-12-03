'use strict'

# @module core.views

char_limit = 300
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::onBeforeRender = ->
        linkName = "More on #{@model.get('name') or @model.get('title')} »"
        inlineLink = "<a href='#{@model.get('url')}'>#{linkName}</a>"
        if @model.get("description")
            truncatedDescription = _.truncate(@model.get("description"), char_limit, true, true)
            @model.set("truncatedDescription", truncatedDescription + " " + inlineLink)
        return

    module.ProductView::replaceImages = ->
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

        for imageEl, i in @$el.find(".main-image .hi-res")
            $image = $(imageEl)
            $cachedImage = $image.parent()

            # find image from id
            image = _.findWhere(@model.get('images'), id: $cachedImage.data('id'))
            imageUrl = image.resizeForDimens(maxWidth, maxHeight)

            if $image.is("img")
                $image.attr("src", imageUrl)
            else if $image.is("div")
                $image.css("background-image", "url('#{imageUrl}')")
        return

    module.ProductView::resizeProductImages = ->
        productImages = @$el.find(".main-image .hi-res")
        if productImages.length > 0 and productImages.first().is("div")
            # Let the browser execute the resizing window callbacks
            # otherwise, container height is 0 & images are resized to 0 height.
            setTimeout((=> @replaceImages()), 1)
        else
            imagesLoaded(productImages, (=> @replaceImages()))
        return

    _.extend(module.ProductView::events, 
        "click .main-image .hi-res": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent::shrinkContainerCallback = ->
        # Fits content to window, doesn't support overflow content
        $table = @$el.find(".table")
        $container = @$el.closest(".fullscreen")
        $containedItem = @$el.closest(".content")

        @updateContent()

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
