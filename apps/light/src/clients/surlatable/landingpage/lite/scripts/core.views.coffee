'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')
Modernizr = require('modernizr')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::onShow = ->
        if App.support.mobile()
            # Add one for description slide unless it's a product popup in portrait mode without tagged products
            if @model.get('type') is "product" and App.utils.portrait() and _.isEmpty(@model.get('tagged-products'))
                @numberOfImages = @model.get('images').length
            else
                @numberOfImages = @model.get('images').length + 1
        @galleryIndex = Math.min(@galleryIndex, @numberOfImages - 1)
        @leftArrow = @$el.find('.gallery-swipe-left')
        @rightArrow = @$el.find('.gallery-swipe-right')
        @mainImage = @$el.find('.main-image')
        @resizeProductImages()
        if @numberOfImages > 1
            @scrollImages(@mainImage.width()*@galleryIndex, 0)
            @updateGallery()
            if App.support.mobile() and @model.get('type') is "product"
                @mainImage.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
        return

    module.ProductView::onBeforeRender = ->
        linkName = "More on #{@model.attributes.name or @model.attributes.title} »"
        inlineLink = "<a href='#{@model.attributes.cj_link or @model.attributes.url}'>#{linkName}</a>"
        if @model.get("description")
            truncatedDescription = _.truncate(@model.get("description"), char_limit, true, true)
            @model.set("truncated_description", truncatedDescription + " " + inlineLink)
        return

    module.ProductView::resizeProductImages = ->
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
                    $cachedImage = $(image).parent()
                    if $cachedImage.is("img")
                        imageUrl = App.utils.getResizedImage($cachedImage.attr("src"),
                            width: maxWidth,
                            height: maxHeight
                        )
                        $(image).attr("src", imageUrl)
                    else if $cachedImage.is("div")
                        imageUrl = $cachedImage.css("background-image").replace('url(','').replace(')','')
                        imageUrl = App.utils.getResizedImage(imageUrl,
                            width: maxWidth,
                            height: maxHeight
                        )
                        $(image).css("background-image", "url('#{imageUrl}')")
            return
        productImages = @$el.find(".main-image .hi-res")
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

    _.extend(module.ProductView.prototype.events, 
        "click .main-image .hi-res": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent.prototype.events =
        "click .look-thumbnail, .back-to-recipe": (event) ->
            @taggedProductIndex = -1
            @renderView()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            product = @taggedProducts[$targetEl.data("index")]
            url = product.get('cj_link') or product.get('url')
            ### Uncomment to enable switching view to product ###
            #@taggedProductIndex = $targetEl.data("index")
            #if App.support.mobile() and not @$el.find('.look-thumbnail').is(':visible')
            #    @carouselRegion.currentView.index = Math.min($(".stl-look").children(':visible').length - 1, @carouselRegion.currentView.index + 1)
            #product = @renderView()
            App.vent.trigger('tracking:product:thumbnailClick', product)
            App.utils.openUrl(url)
            return

    module.ExpandedContent::updateScrollCta = ->
        $recipe = @$el.find(".recipe")
        unless $recipe.length is 0
            if ($recipe[0].scrollHeight - $recipe.scrollTop()) is $recipe.outerHeight()
                $recipe.siblings(".scroll-cta").hide()
            else
                $recipe.siblings(".scroll-cta").show()
        return

    # Patch shrinkContainerCallback to enble recipe scrolling when images are loaded
    module.ExpandedContent::coreShrinkContainerCallback = module.ExpandedContent::shrinkContainerCallback
    module.ExpandedContent::shrinkContainerCallback = ->
        cb = @coreShrinkContainerCallback()
        return =>
            cb(arguments)
            # must wait for all images to load
            if @_imageCount is 0
                $(".recipe").scroll(=>
                    @updateScrollCta()
                    return
                )
            return

    # Patch onShow
    module.ExpandedContent::coreOnShow = module.ExpandedContent::onShow
    module.ExpandedContent::onShow = ->
        if App.support.mobile()
            if App.utils.landscape()
                @$el.closest(".previewContainer").addClass("landscape")
            else
                @$el.closest(".previewContainer").removeClass("landscape")
            if @model.get('type') is "image" or @model.get('type') is "gif"
                @$el.find(".look-product-carousel").swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
        else
            @$el.closest(".previewContainer").removeClass("landscape")

        @coreOnShow()

        if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
            $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                offset: "bottom-in-view"
                direction: "up"
            )
        return

    module.ExpandedContent::swipeStatus = (event, phase, direction, distance, fingers, duration) ->
        productImageIndex = @productInfo.currentView?.galleryIndex or 0
        numberOfImages = (@productInfo.currentView?.numberOfImages - 1) or 0
        index = @_taggedProductIndex # local copy to modify
        if @taggedProductIndex > -1
            # delegate swipe to ProductView to swipe through images
            unless (direction is 'left' and productImageIndex is numberOfImages) or (direction is 'right' and productImageIndex is 0)
                @productInfo.currentView.swipeStatus(event, phase, direction, distance, fingers, duration)
                return
        if phase is 'end'
            if direction is 'right'
                index--
                # swipe from recipe to last product
                if index < -1
                    index = @taggedProducts.length - 1
                    if App.support.mobile()
                        @carouselRegion.currentView.index = Math.min($('.stl-look').children().length - 1, @carouselRegion.currentView.index + 1)
                # swipe from first product to recipe
                else if index is -1 and App.support.mobile()
                    @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
            else if direction is 'left'
                index++
                # swipe from last product to recipe
                if index is @taggedProducts.length
                    index = -1
                    if App.support.mobile()
                        @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
                else if index is 0 and App.support.mobile()
                    @carouselRegion.currentView.index = Math.min($('.stl-look').children(':visible').length - 1, @carouselRegion.currentView.index + 1)
            @taggedProductIndex = index
            @renderView()
        return @

    module.ExpandedContent::renderView = () ->
        # Tagged product selected
        if -1 < @taggedProductIndex < @taggedProducts.length
            @_currentIndex = @taggedProductIndex

            product = @taggedProducts[@taggedProductIndex]
            if not @product
                # Recipes have "back to recipe" links
                product.set("recipe-name", @model.get('name') or @model.get('title'))

            @$el.find('.info').show()
            @$el.find('.look-image-container').hide()
            if App.support.mobile() then @$el.find('.look-thumbnail').show()
            
            @carouselRegion.currentView?.selectItem(@taggedProductIndex)
            if App.support.mobile() and @taggedProducts.length > 0 and @carouselRegion.currentView?
                if App.utils.landscape()
                    @carouselRegion.currentView.calculateVerticalPosition()
                else
                    @carouselRegion.currentView.calculateHorizontalPosition()
        
        # Main content selected
        else
            @_currentIndex = @taggedProductIndex = -1
            # Product popup
            if @product?
                product = @product
                @$el.find('.info').show()
                @$el.find('.look-image-container').hide()
            # Image popup
            else
                @$el.find('.info').hide()
                @$el.find('.look-image-container').show()
                @$el.find('.title-banner .title').html(@model.get('name') or @model.get('title'))

            if App.support.mobile() then @$el.find('.look-thumbnail').hide()
            
            @carouselRegion.currentView?.deselectItems()
            if App.support.mobile() and @carouselRegion.currentView?
                @carouselRegion.currentView.index = Math.max(0, @carouselRegion.currentView.index - 1)
                if App.utils.landscape()
                    @carouselRegion.currentView.calculateVerticalPosition()
                else
                    @carouselRegion.currentView.calculateHorizontalPosition()

        if product
            productInstance = new module.ProductView(
                model: product
            )
            @productInfo.show(productInstance)
            @$el.find('.title-banner .title').html(productInstance.model.get('title') or productInstance.model.get('name'))
        return product

    module.ExpandedContent::close = ->
        # See NOTE in onShow
        unless App.support.mobile()
            $(document.body).removeClass("no-scroll")

        @$(".stick-bottom").waypoint("destroy")
        $(".recipe").off()
        @$el.find(".look-product-carousel").swipe("destroy")
        return

    module.CategoryCollectionView::onShow = ->
        # Enable sticky category bar
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

    ###
    View responsible for the Sur La Table Hero Area
    This Hero's are special in that if there is no hero image specified,
    an overlay with the category name is used (ex: The Chef, Top 25)
    
    @constructor
    @type {LayoutView}
    ###
    class module.SLTHeroAreaView extends Marionette.LayoutView
        model: module.Tile
        className: "previewContainer"
        template: "#hero_template"
        regions:
            content: ".content"

        generateHeroArea: ->
            category = App.intentRank.currentCategory() || App.option('page:home:category')
            catObj = App.categories.findModelByName(category)

            # If category can't be found, default to 'Gifts'
            if not catObj? then catObj = displayName: 'Gifts'

            tile =
                desktopHeroImage: catObj.desktopHeroImage or ""
                mobileHeroImage: catObj.mobileHeroImage or ""
                title: "#{catObj.title or catObj.displayName}"
            
            if @model? and @model.destroy then @model.destroy()
            @model = new module.Tile(tile)
            return @

        loadHeroArea: ->
            @generateHeroArea()
            # If view is already visible, update with new category
            if not @.isDestroyed
                @.render()

        initialize: (options) ->
            if App.intentRank.currentCategory and App.categories
                @generateHeroArea()
            else
                # placeholder to stop error
                @model = new module.Tile()
                App.vent.once('intentRankInitialized', =>
                    @loadHeroArea()
                )
            @listenTo(App.vent, "change:category", =>
                @loadHeroArea()
            )
            return @
