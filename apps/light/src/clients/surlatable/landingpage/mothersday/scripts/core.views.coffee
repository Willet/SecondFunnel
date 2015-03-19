'use strict'

# @module core.views

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.ProductView::initialize = ->
        @numberOfImages = @model.get('images')?.length or 0
        # Add one for the recipe slide
        unless @model.get('type') is "product" or not App.support.mobile()
            @numberOfImages++
        @galleryIndex = 0
        return

    _.extend module.ProductView.prototype.events =
        "click .main-image .image": (event) ->
            $image = $(event.target)
            $image.toggleClass("full-image")
            return

    # For Sur La Table, the "content" image is the best looking product image
    # Re-order the product images so that image is first
    # For desktop, hide it because the pop-up will show the content image
    # For mobile, we will show the product image in leui of showing the content image
    _.extend module.ExpandedContent.prototype, 
        reorderProductImages: ->
            try 
                imageUrl = @model.attributes.url
                prodImages = @model.attributes['tagged-products'][0].images
            catch err
                # One of the required objects in the accessor chains doesn't exist
                return
            if imageUrl and prodImages
                matchImgObj = _.find prodImages, (imgObj) ->
                    # Remove Cloudinary url API operations before doing url comparison
                    # .../upload/c_fit,q_75,w_700/v... -> .../upload/v...
                    baseImgUrl = imgObj.url.replace /(upload)(.*)(\/v)/, "$1$3"
                    return  (baseImgUrl == imageUrl)

                if matchImgObj
                    # prodImages is a reference, will modify product images in place
                    matchImgObjIndex = prodImages.indexOf(matchImgObj)
                    matchImgObj = prodImages.splice(matchImgObjIndex, 1)[0]
                    # Add back as 1st piece of content on mobile because there
                    # is only one gallery on mobile
                    if App.support.mobile()
                        prodImages.unshift(matchImgObj);
            @resizeContainer()

    module.ExpandedContent.prototype.events =
        "click .look-thumbnail": (event) ->
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @stlIndex = Math.max(@stlIndex - 1, 0)
            @lookProductIndex = -1
            if App.support.mobile() and App.utils.landscape()
                @arrangeStlItemsVertical()
            else
                @arrangeStlItemsHorizontal()
            return

        "click .stl-look .stl-item": (event) ->
            $ev = $(event.target)
            $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
            @lookProductIndex = $targetEl.data("index")
            @updateCarousel()
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
        if @model.get("type") is "image" or @model.get("type") is "gif"
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
        if @model.get("type") is "image" or @model.get("type") is "gif"
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
        if App.utils.landscape()
            @$el.closest(".previewContainer").addClass("landscape")
        else
            @$el.closest(".previewContainer").removeClass("landscape")
        @lookThumbnail = @$el.find('.look-thumbnail')
        @lookThumbnail.hide()
        @$el.find('.info').hide()
        if App.support.mobile()
            @$el.find(".look-product-carousel").swipe(
                triggerOnTouchEnd: true,
                swipeStatus: _.bind(@swipeStatus, @),
                allowPageScroll: 'vertical'
            )
        if @model.get("tagged-products")?.length > 0
            @stlIndex = 0
            @lookProductIndex = -1
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
        if @lookProductIndex < 0
            if @lookThumbnail.is(":visible")
                @stlIndex = Math.max(0, @stlIndex - 1)
            @lookThumbnail.hide()
            @$el.find('.info').hide()
            @$el.find('.look-image-container').show()
            @$el.find('.stl-item').removeClass("selected")
            @$el.find('.title-banner .title').html("Classic Carrot Cake Recipe")
            if App.support.mobile() and App.utils.landscape()
                @arrangeStlItemsVertical()
            else
                @arrangeStlItemsHorizontal()
        else
            @$el.find(".stl-item").filter("[data-index=#{@lookProductIndex}]")
                .addClass("selected").siblings().removeClass("selected")
            if @model.get("type") is "product"
                product = new module.Product(@model.attributes)
            else
                product = new module.Product(@model.get("tagged-products")[@lookProductIndex])
            productInstance = new module.ProductView(
                model: product
            )
            @lookThumbnail.show()
            @$el.find('.info').show()
            @$el.find('.look-image-container').hide()
            @$el.find('.title-banner .title').html(productInstance.model.get('title') or productInstance.model.get('name'))
            @productInfo.show(productInstance)
            unless @lookThumbnail.is(":visible")
                @stlIndex = Math.min($(".stl-look").children(":visible").length - 1, @stlIndex + 1)
            if App.support.mobile() and App.utils.landscape()
                @arrangeStlItemsVertical()
            else
                @arrangeStlItemsHorizontal()
        return

    ###
    View responsible for the Sur La Table Hero Area
    This Hero's are special in that they use the same background images
    and overlay with text: GIFTS for ____ (ex: The Chef, Him)
    
    @constructor
    @type {Layout}
    ###
    class module.SLTHeroAreaView extends Marionette.Layout
        model: module.Tile
        className: "previewContainer"
        template: "#hero_template"
        regions:
            content: ".content"

        generateHeroArea: ->
            category = App.intentRank.currentCategory() || App.option('page:home:category')
            catObj = App.categories.findModelByName(category)

            # If category can't be found, default to 'The Chef'
            if not catObj? then catObj = displayName: 'The Chef'

            tile =
                desktopHeroImage: "/static/light/surlatable/landingpage/default/images/slt-hero-desktop.png"
                mobileHeroImage: "/static/light/surlatable/landingpage/default/images/slt-hero-desktop.png"
                title: "<span class='spaced'>GIFTS</span> <span class='for'>for #{catObj.displayName}</span>"
            
            if @model? and @model.destroy then @model.destroy()
            @model = new module.Tile(tile)
            return @

        loadHeroArea: ->
            @generateHeroArea()
            # If view is already visible, update with new category
            if not @.isClosed
                App.heroArea.show @

        initialize: ->
            if App.intentRank.currentCategory and App.categories
                @generateHeroArea()
            else
                # placeholder to stop error
                @model = new module.Tile()
                App.vent.once('intentRankInitialized', =>
                    @loadHeroArea()
                )
            @listenTo App.vent, "change:category", =>
                @loadHeroArea()
            return @

            
