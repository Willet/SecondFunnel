'use strict'

# @module core.views

char_limit = 243
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::onShow = _.wrap(module.ProductView::onShow, (onShow) ->
        if App.support.mobile()
            # Add one for description slide unless it's a product popup
            # in portrait mode without tagged products
            if @model.get('type') is "product" and App.utils.portrait() \
                    and _.isEmpty(@model.get('taggedProducts'))
                @numberOfImages = @model.get('images').length
            else
                @numberOfImages = @model.get('images').length + 1
        onShow.call(@)
        return
    )

    module.ProductView::onBeforeRender = ->
        linkName = "More on #{@model.get('name') or @model.get('title')} »"
        inlineLink = "<a href='#{@model.get('cj_link') or @model.get('url')}'>#{linkName}</a>"
        if @model.get("description")
            truncatedDescription = _.truncate(@model.get("description"), char_limit, true, true)
            @model.set("truncatedDescription", truncatedDescription + " " + inlineLink)
        return

    module.ProductView::replaceImages = ->
        unless App.support.mobile()
            $container = @$el.find(".main-image-container")
            if $container.is(":visible")
                maxWidth = $container.width()*1.3
                maxHeight = $container.height()*1.3
            else
                maxWidth = App.option("minImageWidth") or 300
                maxHeight = App.option("minImageHeight") or 300
            for image, i in @$el.find(".main-image .hi-res")
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

    module.ProductView::resizeProductImages = ->
        productImages = @$el.find(".main-image .hi-res")
        if productImages.length > 0 and productImages.first().is("div")
            @replaceImages()
        else
            imagesLoaded(productImages, (=> @replaceImages()))
        return

    _.extend(module.ProductView::events, 
        "click .main-image .hi-res": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return
    )

    module.ExpandedContent::events =
        "click @ui.lookThumbnail, .back-to-recipe": (event) ->
            # Hide products, show content
            @taggedProductIndex = -1
            @updateContent()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            product = @taggedProducts[$targetEl.data("index")]
            url = product.get('cj_link') or product.get('url')
            ### Uncomment to enable switching view to product ###
            #@taggedProductIndex = $targetEl.data("index")
            #if App.support.mobile() and not @ui.lookThumbnail.is(':visible')
            #    @productThumbnails.currentView.index = Math.min($(".stl-look").children(':visible').length - 1, @productThumbnails.currentView.index + 1)
            #product = @updateContent()
            App.vent.trigger('tracking:product:thumbnailClick', product)
            App.utils.openUrl(url)
            return

    # SLT shows one piece of content at a time
    _.extend(module.ExpandedContent::defaultViewOptions, featureSingleItem: true)

    module.ExpandedContent::updateScrollCta = ->
        $recipe = @$el.find(".recipe")
        unless $recipe.length is 0
            if ($recipe[0].scrollHeight - $recipe.scrollTop()) is $recipe.outerHeight()
                $recipe.siblings(".scroll-cta").hide()
            else
                $recipe.siblings(".scroll-cta").show()
        return

    module.ExpandedContent::shrinkContainerCallback = _.wrap(
        module.ExpandedContent::shrinkContainerCallback,
        (shrinkContainerCallback) ->
            # Patch shrinkContainerCallback to enble recipe scrolling when images are loaded
            shrinkContainerCallback.call(@)
            $(".recipe").scroll(=>
                @updateScrollCta()
                return
            )
    )

    module.ExpandedContent::updateContent = _.wrap(
        module.ExpandedContent::updateContent,
        (updateContent) ->
            updateContent.call(@)
            # set name of pop-up to currently visible 
            if @productInfo.hasView()
                currentProduct = @productInfo.currentView.model
                title = currentProduct.get('title') or currentProduct.get('name')
                @$el.find('.title-banner .title').html(title)
            return
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

    module.ExpandedContent::destroy = _.wrap(module.ExpandedContent::destroy, (destroy) ->
        $(".recipe").off()
        destroy.call(@)
        return
    )

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

    class module.SLTHeroAreaView extends Marionette.LayoutView
        ###
        View responsible for the Sur La Table Hero Area
        This Hero's are special in that if there is no hero image specified,
        an overlay with the category name is used (ex: The Chef, Top 25)
        ###
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
