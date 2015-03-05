"use strict"

imagesLoaded = require('imagesLoaded')
swipe = require('jquery-touchswipe')
require("jquery-scrollto")
require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky

module.exports = (module, App, Backbone, Marionette, $, _) ->
    $window = $(window)
    $document = $(document)

    class module.ProductView extends Marionette.ItemView
        template: "#product_info_template"
        templates: ->
            templateRules = [
                # supported contexts: options, data
                "#<%= data.type %>_info_template"
                "#image_info_template"
                "#product_info_template"
            ]
            unless App.support.mobile()
                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            templateRules


        events:
            'click .item': (ev) ->
                $selectedItem = $(ev.target)
                @galleryIndex = $selectedItem.data("index")
                @scrollImages(@mainImage.width()*@galleryIndex)
                @updateGallery()
                return

            'click .gallery-swipe-left, .gallery-swipe-right': (ev) ->
                $target = $(ev.target)
                unless $target.hasClass("grey")
                    if $target.hasClass("gallery-swipe-left")
                        @galleryIndex = Math.max(@galleryIndex - 1, 0)
                    else
                        @galleryIndex = Math.min(@galleryIndex + 1, @numberOfImages - 1)
                    @scrollImages(@mainImage.width()*@galleryIndex)
                    @updateGallery()
                return

            'click .buy': (ev) ->
                $target = if $(ev.target).is("a") then $(ev.target) else $(ev.target).children("a")
                if $target.hasClass('find-store')
                    App.vent.trigger('tracking:product:findStore', @model)
                else if $target.hasClass('in-store') or $target.hasClass('button')
                    App.vent.trigger('tracking:product:buyOnline', @model)

                # Over-write addUrlTrackingParameters for each customer
                url = App.utils.addUrlTrackingParameters( $target.attr('href') )
                App.utils.openUrl(url)
                # Stop propogation to avoid double-opening url
                return false

        initialize: ->
            @numberOfImages = @model.get('images')?.length or 0
            @galleryIndex = 0
            return

        onRender: ->
            @setElement(@$el.children())
            return

        onShow: ->
            @leftArrow = @$el.find('.gallery-swipe-left')
            @rightArrow = @$el.find('.gallery-swipe-right')
            @mainImage = @$el.find('.main-image')
            if @numberOfImages > 1
                @scrollImages(@mainImage.width()*@galleryIndex, 0)
                @updateGallery()
                @mainImage.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @),
                    allowPageScroll: 'vertical'
                )
            return

        swipeStatus: (event, phase, direction, distance, fingers, duration) ->
            focusWidth = @mainImage.width()
            offset = focusWidth * @galleryIndex

            if phase is 'move'
                if direction is 'left'
                    @scrollImages(distance + offset, duration)
                else if direction is 'right'
                    @scrollImages(offset - distance, duration)
            else if phase is 'end'
                if direction is 'right'
                    @galleryIndex = Math.max(@galleryIndex - 1, 0)
                else if direction is 'left'
                    @galleryIndex = Math.min(@galleryIndex + 1, @numberOfImages - 1)
                @scrollImages(focusWidth * @galleryIndex, duration)
                @updateGallery()
            else if phase is 'cancel'
                @scrollImages(focusWidth * @galleryIndex, duration)
            return @

        scrollImages: (distance, duration = 250) ->
            distance *= -1
            if App.support.isLessThanIe9()
                @mainImage.css(
                    'position': 'relative',
                    'left': distance
                )
            else
                @mainImage.css(
                    '-webkit-transition-duration': (duration / 1000).toFixed(1) + 's',
                    'transition-duration': (duration / 1000).toFixed(1) + 's',
                    '-webkit-transform': 'translate3d(' + distance + 'px, 0px, 0px)',
                    '-ms-transform': 'translateX(' + distance+ 'px)',
                    'transform': 'translate3d(' + distance + 'px, 0px, 0px)'
                )
            return

        updateGallery: ->
            @$el.find(".item")
                .removeClass("selected")
                .filter("[data-index=#{@galleryIndex}]")
                .addClass("selected")
            if @galleryIndex is 0
                @leftArrow.addClass("grey")
                @rightArrow.removeClass("grey")
            else if @galleryIndex is @numberOfImages - 1
                @leftArrow.removeClass("grey")
                @rightArrow.addClass("grey")
            else
                @leftArrow.removeClass("grey")
                @rightArrow.removeClass("grey")
            return


    class module.ProductCollectionView extends Marionette.CollectionView
        itemView: module.ProductView

        initialize: (products) ->
            @collection = new module.ProductCollection(products)
            return


    ###
    View responsible for Youtube videos in heros / previews
    
    @constructor
    @type {ItemView}
    ###
    class module.YoutubeVideoView extends Marionette.ItemView
        template: "#youtube_video_template"

        # default options
        defaultPlayerOptions:
            showinfo: 0
            autoplay: 1
            playsinline: 1
            enablejsapi: 1
            controls: 0
            modestbranding: 1
            rel: 0
            origin: window.location.origin

        # Multiple YouTube videos can be queued to load after the API loads
        @loadOnYouTubeAPIReady = []
        @onYouTubeAPIReady = () =>
            _.each(@loadOnYouTubeAPIReady, (cb) ->
                cb()
            )

        initialize: (video) ->
            @model = video
            @playerOptions = _.extend({}, @defaultPlayerOptions, video.get('options', {}))

        trackVideoState: (event) ->
            playerUrlParams = $.deparam(App.utils.urlParse(@player.getVideoUrl())?.search?.substr(1))
            videoId = if playerUrlParams then playerUrlParams.v else undefined

            switch event.data
                when window.YT.PlayerState.PLAYING
                    App.vent.trigger('tracking:videoPlay', videoId, event)
                when window.YT.PlayerState.ENDED
                    App.vent.trigger('tracking:videoFinish', videoId, event)

        loadYouTubePlayer: () ->
            @player = new window.YT.Player(@playerId,
                videoId: @model.get('original-id')
                events:
                    'onPlayerReady': (ev) => @trackVideoState(ev)
                    'onStateChange': (ev) => @trackVideoState(ev)
                playerVars: @playerOptions
            )

        onShow: () ->
            @playerId = "yt-container-#{@cid}"
            div = @$el.find('div.yt-placeholder').attr('id', @playerId)
            if not div?
                @$el.append($("<div>", {'id': @playerId }))
            # If the YouTube API hasn't loaded yet, queue up this video to load
            if not window.YT?.Player?
                if not window.onYouTubeIframeAPIReady
                    window.onYouTubeIframeAPIReady = @constructor.onYouTubeAPIReady
                @constructor.loadOnYouTubeAPIReady.push(=> @loadYouTubePlayer())
            else
                @loadYouTubePlayer()
            return
            

        onBeforeDestroy: () ->
            App.vent.trigger('tracking:videoStopped', @model.get('original-id'),
                target: @
                data: 2
            )
            @player.destroy()


    ###
    A Shop The Look

    @constructor
    @type {Layout}
    ###
    class module.ExpandedContent extends Marionette.Layout
        regions:
            productInfo: ".product-info"

        events:
            "click .stl-look .stl-item": (event) ->
                $el = @$el
                $ev = $(event.target)
                $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
                
                $targetEl.addClass("selected").siblings().removeClass "selected"
                index = $targetEl.data("index")
                product = @model.get("tagged-products")[index]
                productModel = new module.Product(product)
                productInstance = new module.ProductView(
                    model: productModel
                )
                if App.support.mobile()
                    $('body').scrollTo(".cell.info", 500)
                @productInfo.show(productInstance)
                return
        
        onBeforeRender: ->
            # Need to get an appropriate sized image
            image = $.extend(true, {}, @model.get("defaultImage").attributes)
            image = new module.Image(image)
            if App.support.mobile()
                image.url = image.height($window.height())
            else
                image = image.height(App.utils.getViewportSized(true), true)

            if @model.get("tagged-products") and @model.get("tagged-products").length > 1
                @model.set("tagged-products", _.sortBy(@model.get("tagged-products"), (obj) ->
                    -1 * parseFloat((obj.price or "$0").substr(1), 10)
                ))

            # templates use this as obj.image.url
            @model.set "image", image
            return

        initialize: ->
            @$el.attr
                id: "preview-#{@model.cid}"
                class: "preview-container"
            return

        close: ->
            # See NOTE in onShow
            unless App.support.isAnAndroid()
                $(document.body).removeClass "no-scroll"

            @$(".stick-bottom").waypoint "destroy"
            return

        resizeContainer: ->
            shrinkContainer = (element) ->
                ->
                    unless App.support.mobile()
                        container = element.closest(".fullscreen")
                        containedItem = element.closest(".content")
                        if --imageCount isnt 0
                            return

                        # no container to shrink
                        unless container and container.length
                            return
                        container.css
                            top: "0"
                            bottom: "0"
                            left: "0"
                            right: "0"

                        heightReduction = $(window).height()
                        widthReduction = container.outerWidth()
                        heightReduction -= containedItem.outerHeight()
                        heightReduction /= 2 # Split over top and bottom
                        if heightReduction <= 0 or App.support.mobile() # String because jQuery checks for falsey values
                            heightReduction = "0"
                        widthReduction -= containedItem.outerWidth()
                        widthReduction /= 2
                        if widthReduction <= 0 or App.support.mobile() # String because jQuery checks for falsey values
                            widthReduction = "0"
                        container.css
                            top: heightReduction
                            bottom: heightReduction
                            left: widthReduction
                            right: widthReduction
                    return

            imageCount = $("img.main-image, img.image", @$el).length

            # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
            $("img.main-image, img.image", @$el).one("load", shrinkContainer(@$el)).each ->
                if @complete
                    # Without the timeout the box may not be rendered. This lets the onShow method return
                    setTimeout (=>
                        $(@).load()
                        return
                    ), 1
                return

            return

        # Disable scrolling body when preview is shown
        onShow: ->
            if @model.get("sizes")?.master
                width = @model.get("sizes").master.width
                height = @model.get("sizes").master.height
                if Math.abs((height-width)/width) <= 0.02
                    @model.set("orientation", "square")
                else if width > height
                    @model.set("orientation", "landscape")
                else
                    @model.set("orientation", "portrait")
            if @model.get("tagged-products")?.length > 0
                productInstance = new module.ProductView(
                    model: new module.Product(@model.get("tagged-products")[0])
                )
                @productInfo.show(productInstance)
                @$el.find(".stl-item").filter("[data-index=0]").addClass("selected")
            else if @model.get("template") == "product"
                productInstance = new module.ProductView(
                    model: new module.Product(@model.attributes)
                )
                @productInfo.show(productInstance)
            @resizeContainer()


    ###
    Contents inside a PreviewWindow.

    Content is displayed using a cascading level of templates, which
    increases in specificity.

    @constructor
    @type {Layout}
    ###
    class module.PreviewContent extends module.ExpandedContent

        template: "#tile_preview_template"
        templates: ->
            templateRules = [
                # supported contexts: options, data
                "#<%= options.store.slug %>_<%= data.template %>_mobile_preview_template"
                "#<%= data.template %>_mobile_preview_template"
                "#<%= options.store.slug %>_<%= data.template %>_preview_template"
                "#<%= data.template %>_preview_template"
                "#product_mobile_preview_template"
                "#product_preview_template"
                "#tile_mobile_preview_template" # fallback
                "#tile_preview_template" # fallback
            ]
            unless App.support.mobile()

                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            templateRules

        onRender: ->
            # hide discovery, then show this window as a page.
            if App.support.mobile()
                @trigger("swap:feed", @$el) # out of scope
                @trigger("feed:swapped")
            App.vent.trigger("previewRendered", @)
            return


        # Disable scrolling body when preview is shown
        onShow: ->
            super

            #  NOTE: Previously, it was thought that adding `no-scroll`
            #  to android devices was OK, because no problems were observed
            #  on some device.
            #
            #  Turns out, that was wrong.
            #
            #  It seems like no-scroll prevent scrolling on *some* android
            #  devices, but not others.
            #
            #  So, for now, only add no-scroll if the device is NOT an android.
            #
            unless App.support.mobile()
                width = Marionette.getOption(@, "width")
                if width
                    @$(".content").css("width", width + "px")
                else if App.support.mobile()
                    @$el.width($window.width()) # assign width

                # if it's a real preview, add no-scroll
                unless @$el.parents("#hero-area").length
                    @trigger("scroll:disable")
            return


    ###
    View responsible for Hero-specific things

    @constructor
    @type {ItemView}
    ###
    class module.HeroContent extends Marionette.Layout
        template: "#herovideo_template"
        regions:
            video: ".hero-video"
        templates: ->
            templateRules = [
                "#<%= options.store.slug %>_<%= data.template %>_template"
                "#<%= data.template %>_template"
                "#hero_template" # fallback
            ]
            unless App.support.mobile()

                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            templateRules

        onRender: ->
            # hide discovery, then show this window as a page.
            if App.support.mobile()
                @trigger("swap:feed", @$el) # out of scope
                @trigger("feed:swapped")
            App.vent.trigger("heroRendered", @)
            return

        onShow: ->
            video = @model.get('video')
            if video?
                videoInstance = new module.YoutubeVideoView(video)
                @video.show(videoInstance)
            return


    ###
    View responsible for the "Hero Area"
    (e.g. Shop-the-look, featured, or just a plain div)

    @constructor
    @type {Layout}
    ###
    class module.HeroAreaView extends Marionette.Layout
        className: "heroContainer"
        template: "#hero_container_template"
        regions:
            content: ".content"
        
        ###
        @param data - can be an {object} (tileJson) or a {number} (tile-id)
        ###
        initialize: (data) ->
            tile = if _.isObject(data) and not _.isEmpty(data) then data else undefined
            tileId = if App.utils.isNumber(data) then data else App.option("page:home:hero")
            
            # data can be an object (tileJson)
            if tile?
                @tileLoaded = $.when(tile)
            # data can be a number (tile-id)
            else if tileId?
                @tileLoaded = $.Deferred()
                tileLoadedResolve = =>
                    @tileLoaded.resolve(arguments)
                module.Tile.getTileById(tileId, tileLoadedResolve, tileLoadedResolve)
            # data didn't work, try to get category from intentRank if its setup
            else if App.intentRank?.currentCategory?
                tile = @getCategoryHeroImages(App.intentRank.currentCategory())
                @tileLoaded = $.when(tile)
            # get category from intentRank when its ready
            else 
                @tileLoaded = $.Deferred()
                App.vent.once('intentRankInitialized', =>
                    tileJson = @updateCategoryHeroImages(App.intentRank.currentCategory())
                    @tileLoaded.resolve(tileJson)
                )
            # tile can be a {Tile} or {object} tileJson
            @tileLoaded.done((tile) =>
                @model = if _.isObject(tile) and not _.isEmpty(tile) then module.Tile.selectTileSubclass(tile) else undefined
                @listenTo(App.vent, "windowResize", =>
                    App.heroArea.show(@)
                )
                return
            )

            @listenTo(App.vent, "change:category", @updateCategoryHeroImages)
            return

        onShow: ->
            @tileLoaded.done(=>
                if @model?
                    contentOpts = model: @model
                    contentInstance = undefined
                    if _.contains(contentOpts.model.get("type", ""), "hero")
                        contentInstance = new module.HeroContent(contentOpts)
                    else
                        contentInstance = new module.PreviewContent(contentOpts)
                    @content.show(contentInstance)
                else
                    @content.close()
                return
            )

        updateCategoryHeroImages: (category) ->
            @model?.destroy()
            heroImagesModel = @getCategoryHeroImages(category)
            @model = if heroImagesModel then new module.Tile(heroImagesModel) else undefined
            App.heroArea.show(@)

        getCategoryHeroImages: (category='') ->
            category = if category? then category else App.option('page:home:category')
            catObj = (App.categories.findModelByName(category) or {})
            desktopHeroImage = (catObj['desktopHeroImage'] or App.option('page:desktopHeroImage'))
            mobileHeroImage = (catObj['mobileHeroImage'] or App.option('page:mobileHeroImage'))
            if desktopHeroImage
                heroImages =
                    "desktopHeroImage": desktopHeroImage
                    "mobileHeroImage": mobileHeroImage or desktopHeroImage
                    "template": "hero"
                    "type": "hero"
            else
                heroImages = undefined
            return heroImages


    ###
    Container view for a PreviewContent object.

    @constructor
    @type {Layout}
    ###
    class module.PreviewWindow extends Marionette.Layout
        tagName: "div"
        className: "previewContainer"
        template: "#preview_container_template"
        templates: ->
            templateRules = [
                # supported contexts: options, data
                "#<%= options.store.slug %>_<%= data.template %>_mobile_preview_container_template"
                "#<%= data.template %>_mobile_preview_container_template"
                "#<%= options.store.slug %>_<%= data.template %>_preview_container_template"
                "#<%= data.template %>_preview_container_template"
                "#product_mobile_preview_container_template"
                "#product_preview_container_template"
                "#mobile_preview_container_template" # fallback
                "#preview_container_template" # fallback
            ]
            unless App.support.mobile()

                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            return templateRules

        regions:
            content: ".template.target"

        events:
            "click .close, .mask": ->
                # If we have been home then it's safe to use back()
                if App.initialPage == ''
                    Backbone.history.history.back()
                else
                    App.previewArea.close()
                    category = App.intentRank.currentCategory()
                    route = if category then "category/#{category}" else ""
                    App.router.navigate(route,
                        trigger: false
                        replace: true
                    )
                return

        initialize: (options) ->
            @options = options
            return

        onMissingTemplate: ->
            @content.close()
            @close()
            return

        templateHelpers: ->

        # return {data: $.extend({}, this.options, {template: this.template})};
        onRender: ->
            heightMultiplier = undefined

            # cannot declare display:table in marionette class.
            heightMultiplier = (if App.utils.portrait() then 1 else 2)
            @$el.css
                display: "table"
                height: (if App.support.mobile() then heightMultiplier * $window.height() else "")

            template = @options.model.get("template")
            contentOpts = model: @options.model
            contentInstance = undefined
            contentInstance = new module.PreviewContent(contentOpts)

            # remember if $.fn.swapWith is called so the feed can be swapped back
            contentInstance.on("feed:swapped", =>
                @triggerMethod("feed:swapped")
                return
            )

            contentInstance.on("swap:feed", ($el) ->
                App.discoveryArea.$el.parent().swapWith($el)
                return
            )

            contentInstance.on("scroll:disable", ->
                $(document.body).addClass("no-scroll")
                return
            )

            @content.show(contentInstance)
            App.previewLoadingScreen.hide()

            @listenTo(App.vent, "rotate", (width) =>
                # On change in orientation, we want to rerender our layout
                # this is automatically unbound on close, so we don't have to clean
                heightMultiplier = (if App.utils.portrait() then 1 else 2)
                @$el.css(
                    height: (if App.support.mobile() then heightMultiplier * $window.height() else "")
                )
                if App.utils.landscape()
                    @$el.closest(".previewContainer").addClass("landscape")
                else
                    @$el.closest(".previewContainer").removeClass("landscape")
                @content.currentView.resizeContainer()
                if @content.currentView?.productInfo?.currentView
                    productRegion = @content.currentView.productInfo
                    productRegion.show(productRegion.currentView,
                        forceShow: true
                    )
                return
            )
            return

        positionWindow: ->
            windowMiddle = $window.scrollTop() + $window.height() / 2
            if App.windowMiddle
                windowMiddle = App.windowMiddle
            if App.windowHeight and App.support.mobile()
                @$el.css("height", App.windowHeight)
            @$el.css("top", Math.max(windowMiddle - (@$el.height() / 2), 0))

        onShow: ->
            @image_load = imagesLoaded(@$el)
            @listenTo(@image_load, 'always', =>
                @positionWindow()
            )
            return

        onClose: ->
            # hide this, then restore discovery.
            if @feedSwapped
                @$el.swapWith(App.discoveryArea.$el.parent())

                # handle results that got loaded while the discovery
                # area has an undefined height.
                App.feed.layout(App.discovery)
                App.feed.masonry.resize()
            return


        # state-keeping for restoring feed previously swapped out
        onFeedSwapped: ->
            @feedSwapped = true
            return


    ###
    View for switching categories.

    @constructor
    @type {ItemView}
    ###
    class module.CategoryView extends Marionette.ItemView
        tagName: "div"
        className: "category"

        template: "#category_template"
        templates: ->
            templateRules = [
                "#<%= options.store.slug %>_mobile_category_template"
                "#<%= options.store.slug %>_category_template"
                "#mobile_category_template"
                "#category_template"
            ]
            unless App.support.mobile()
                templateRules = _.reject(templateRules, (t) ->
                    return _.contains(t, "mobile")
                )
            templateRules

        events:
            'click': (event) ->
                category = @model.get("name")
                $el = @$el
                $subCatEl = $el.find('.sub-category')

                if $subCatEl.length and not $el.hasClass('expanded')
                    # First click, expand subcategories
                    $el.addClass('expanded')
                    $el.siblings().removeClass('expanded')
                else
                    # First click w/ no subcategories or
                    # second click w/ categories, select category
                    $el.removeClass('expanded')
                    unless $el.hasClass('selected') and not $subCatEl.hasClass('selected')
                        @selectCategoryEl($el)

                        App.router.navigate("category/#{category}",
                            trigger: true
                        )
                return false # stop propogation

            'click .sub-category': (event) ->
                $el = @$el
                category = @model
                $ev = $(event.target)
                $subCatEl = if $ev.hasClass('sub-category') then $ev else $ev.parent('.sub-category')

                # Close categories drop-down
                $el.removeClass 'expanded'

                # Retrieve subcategory object
                subCategory = _.find(category.get('subCategories'), (subcategory) ->
                    return subcategory.name == $subCatEl.data('name')
                )
                # switch to the selected category if it has changed
                unless $el.hasClass('selected') and $subCatEl.hasClass('selected') and not $subCatEl.siblings().hasClass('selected')
                    @selectCategoryEl($subCatEl)

                    # If subCategory leads with "|", its an additional filter on the parent category
                    if subCategory['name'].charAt(0) == "|"
                        switchCategory = category.get("name") + subCategory['name']
                    # Else, subCategory is a category
                    else
                        switchCategory = subCategory['name']

                    App.router.navigate("category/#{switchCategory}",
                        trigger: true
                    )
                return false # stop propogation

        # Apply the 'selected' class to a category or sub-category element
        selectCategoryEl: (el) ->
            $el = $(el)

            if $el.hasClass('category')
                # remove selected from child sub-categories
                $el.find('.sub-category').removeClass('selected')
                # switch to the selected category if it has changed
                unless $el.hasClass('selected')
                    $el.addClass('selected')
                    # remove selected from other categories
                    $el.siblings().each ->
                        self = $(@)
                        self.removeClass('selected')
                        self.find('.sub-category').removeClass('selected')

            else if $el.hasClass('sub-category')
                $catEl = $el.parents('.category')
                
                # switch to selected sub-category
                $el.addClass('selected')
                $el.siblings().removeClass('selected')
                # switch to selected category if not already
                unless $catEl.hasClass('selected')
                    $catEl.addClass('selected')
                    # remove selected from other categories
                    $catEl.siblings().each ->
                        self = $(@)
                        self.removeClass('selected')
                        self.find('.sub-category').removeClass('selected')
            return @


    ###
    A collection of Categories to display.

    @constrcutor
    @type {CollectionView}
    ###
    class module.CategoryCollectionView extends Marionette.CollectionView
        tagName: "div"
        className: "category-area"
        itemView: module.CategoryView

        initialize: (options) ->
            if App.support.mobile() and App.option("page:mobileCategories")
                catOpt = "page:mobileCategories"
            else
                catOpt = "page:categories"
            categories = for category in App.option(catOpt, [])
                if typeof(category) is "string"
                    category = {name: category}
                category

            @collection = new module.CategoryCollection(categories, model: module.Category)

            # Watch for updates to feed, generally from intentRank
            @listenTo(App.vent, "change:category", @selectCategory)

            # Enable sticky category bar
            if App.option("page:stickyCategories")
                @$el.parent().waypoint('sticky')
            
            return @
        
        onRender: ->
            if App.intentRank.currentCategory()?
                @selectCategory(App.intentRank.currentCategory())
            else
                App.vent.once('intentRankInitialized', =>
                    if App.intentRank.currentCategory()?
                        @selectCategory (App.intentRank.currentCategory())
                )
            return @

        # Remove the 'selected' class from all category and sub-category elements
        unselectCategories: ->
            @$el.find('.selected').removeClass('selected')
            return @

        ###
        Given a category string, find it and select it (add the .selected class)
        An empty string '' will remove selection from all categories
        Returns boolean if category / sub-category found
        
        @returns {bool}
        ###
        selectCategory: (category) ->
            if category == ''
                # home category
                @unselectCategories()
                return true
            try
                catMapObj = @collection.findModelByName(category)
                catView = @children.findByModel(catMapObj.category)

                $el = catView.$el
                $catEl = catView.$el.find(".sub-category[data-name='#{catMapObj.subCategory}']")

                $target = if catMapObj.subCategory then $catEl else $el
                catView.selectCategoryEl($target)
                return true
            catch err
                if App.option 'debug', false
                    console.error("Could not select category '#{category}' because:\n#{err.message}")
            return false
