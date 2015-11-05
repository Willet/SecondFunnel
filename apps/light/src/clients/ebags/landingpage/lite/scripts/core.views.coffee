'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::initialize = _.wrap(
        module.ProductView::initialize, (initialize) ->
            initialize.call(@)
            if App.support.mobile()
                @numberOfImages += 1 # add slot of description
            return
    )

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

    _.extend(module.ExpandedContent::events,
        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            product = @taggedProducts[$targetEl.data("index")]
            ### Uncomment to enable switching view to product ###
            #@taggedProductIndex = $targetEl.data("index")
            #if App.support.mobile() and not @ui.lookThumbnail.is(':visible')
            #    @productThumbnails.currentView.index = Math.min($(".stl-look").children(':visible').length - 1, @productThumbnails.currentView.index + 1)
            #product = @updateContent()
            App.vent.trigger('tracking:product:thumbnailClick', @getTrackingData(product))
            App.utils.openUrl(product.get("url"))
            return
    )

    # SLT shows one piece of content at a time
    _.extend(module.ExpandedContent::defaultOptions, featureSingleItem: true)

    module.ExpandedContent::showThumbnails = ->
        # SLT thumbnails are always across the bottom
        if @taggedProducts.length > 0
            # Initialize carousel if this has tagged products
            thumbnailsInstance = new module.ProductThumbnailsView(
                items: @taggedProducts
                attrs:
                    'lookImageSrc': @model.get('defaultImage').url
                    'lookName': @model.get('defaultImage').get('name')
                    'orientation': 'landscape'
            )
            @productThumbnails.show(thumbnailsInstance)
            @ui.lookThumbnail.hide()
        return

    module.CategoryCollectionView::onShow = ->
        # Enable sticky category bar
        # Has an offset for the category thumbnails
        sticky = App.option("page:stickyCategories")
        if _.isString(sticky)
            if sticky == 'desktop-only' and not App.support.mobile()
                @$el.parent().waypoint('sticky',
                    offset: '-113px' # 111px thumbnail + 1px + 1px borders
                )
            else if sticky == 'mobile-only' and App.support.mobile()
                @$el.parent().waypoint('sticky',
                    offset: '-113px' # 111px thumbnail + 1px + 1px borders
                )
        else if _.isBoolean(sticky) and sticky
            @$el.parent().waypoint('sticky',
                offset: '-113px' # 111px thumbnail + 1px + 1px borders
            )

        return @
