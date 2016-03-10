"use strict"

swipe = require('jquery-touchswipe')
Modernizr = require('modernizr')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    ###
    A container tile that has no onclick or onhover

    @constructor
    @type {TileView}
    ###
    class module.ContainerTileView extends module.TileView
        onHover: (ev) ->
            return

        onClick: (ev) ->
            return


    class module.GiftcardTileView extends module.ContainerTileView
        template: "#giftcard_tile_template"

        onClick: (ev) ->
            url = App.utils.addUrlTrackingParameters( @model.get("redirectUrl") )
            window.open url, App.utils.openInWindow()
            return


    class module.TumblrTileView extends module.ContainerTileView
        template: "#tumblr_tile_template"

        onClick: (ev) ->
            url = App.utils.addUrlTrackingParameters( @model.get("redirectUrl") )
            window.open url, App.utils.openInWindow()
            return


    class module.BannerTileView extends module.TileView
        template: "#banner_tile_template"

        onClick: (ev) ->
            url = App.utils.addUrlTrackingParameters( @model.get("redirectUrl") )
            window.open url, App.utils.openInWindow()
            return


    _.extend(module.ExpandedContent.prototype.events,
        "click .look-image": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent::shrinkContainerCallback = ->
            $table = @$el.find(".table")
            $container = @$el.closest(".fullscreen")
            $containedItem = @$el.closest(".content")

            if @productInfo.currentView is undefined
                @updateContent()
            if @model.get("type") is "image" or @model.get("type") is "gif"
                if @lookProductIndex > -1
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
                    imageUrl = @model.get("images")[0].resizeForDimens($lookImage.width()*1.3,
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
