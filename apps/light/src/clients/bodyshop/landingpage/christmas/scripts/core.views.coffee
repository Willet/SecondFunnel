'use strict'

# @module core.views

char_limit = 350
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
        inlineLink = "<span class='more-link'><a href='#{@model.get('url')}'>#{linkName}</a></span>"
        @model.set("truncatedDescription", "#{@model.get("description")} #{inlineLink}")
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
            $cachedImage = $image.parents(".image-holder")

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

    # SLT shows one piece of content at a time
    _.extend(module.ExpandedContent::defaultOptions, featureSingleItem: true)

    module.ExpandedContent::showImage = _.wrap(
        module.ExpandedContent::showImage,
        (showImage) ->
            image = @model.get('defaultImage')
            if not _.isEmpty(image.get('tagged-products'))
                # show image with its tagged product details
                @showProduct(image.get('tagged-products')[0])
            else
                # image will be displayed in .look-image-container, rendered by template
                showImage.call(@)
    )

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

    _.extend(module.CategoryView::events,
        "mouseover": (event) ->
            if not App.support.mobile()
                App.heroArea.currentView.updateCategoryHeroImages(@model.get("name"))
        "mouseout": (event) ->
            if not App.support.mobile()
                App.heroArea.currentView.updateCategoryHeroImages(App.intentRank.currentCategory())
    )

    module.CategoryCollectionView::onShow = ->
        # Enable sticky category bar
        sticky = App.option("page:stickyCategories")
        if App.support.mobile()
            if (_.isBoolean(sticky) and sticky) or \
                    (_.isString(sticky) and sticky == 'mobile-only')
                $('.navbar').waypoint('sticky')
        else
            if (_.isBoolean(sticky) and sticky) or \
                    (_.isString(sticky) and sticky == 'desktop-only')
                @$el.parent().waypoint('sticky')
            else if sticky == 'mobile-only' and App.support.mobile()
                @$el.parent().waypoint('sticky')
        return @

    # Image Tile's are a replacement Image for the product tagged on the image
    # If a need to repurpose Image Tiles arrises, this logic can be 
    # gated by the attribute `productShot` instead of setting it.
    module.ImageTile::initialize = ->
        super
        image = @get('defaultImage')
        if not _.isEmpty(image.get('tagged-products'))
            product = new module.Product(image.get('tagged-products')[0])
            product.set(
                contentShot: true
                defaultImage: image
                images: [image]
            )
            image.set(
                productShot: true
                'tagged-products': [product]
            )

    module.ImageTileView::templateHelpers = ->
        image = @model.get('defaultImage')
        if not _.isEmpty(image.get('tagged-products'))
            # mimic product tile
            return product: image.get('tagged-products')[0]

