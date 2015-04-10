"use strict"

require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky
swipe = require('jquery-touchswipe')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    $window = $(window)
    $document = $(document)

    ###
    View that provides carousel animations/swipe gestures.
    
    @constructor
    @type {ItemView}
    ###
    class module.CarouselView extends Marionette.ItemView
        template: "#carousel_template"

        events:
            'click .carousel-swipe-left, .carousel-swipe-right, .carousel-swipe-up, .carousel-swipe-down': (ev) ->
                if $(ev.target).hasClass("carousel-swipe-left")
                    @calculateHorizontalPosition("left")
                else if $(ev.target).hasClass("carousel-swipe-right")
                    @calculateHorizontalPosition("right")
                else if $(ev.target).hasClass("carousel-swipe-up")
                    @calculateVerticalPosition("up")
                else
                    @calculateVerticalPosition("down")
                return

        serializeData: ->
            data = {
                items: @items,
                index: @index,
                attrs: @attrs
            }
            return data

        getTemplate: ->
            if @attrs.type
                return "##{@attrs.type}_carousel_template"
            else
                return "#carousel_template"

        ###
        @param attrs : array of extra attributes (e.g. lookImageSrc from ExpandedContent)
        @param index : index of leftmost/topmost item in the carousel
        @param items : array of items to display in the carousel
        ###
        initialize: (data) ->
            @attrs = data['attrs'] or []
            @index = data['index'] or 0
            @items = data['items'] or []
            return

        onRender: ->
            @setElement(@$el.children())
            return

        onShow: ->
            @container = @$el.find(".carousel-container")
            @leftArrow = @$el.find(".carousel-swipe-left")
            @rightArrow = @$el.find(".carousel-swipe-right")
            @upArrow = @$el.find(".carousel-swipe-up")
            @downArrow = @$el.find(".carousel-swipe-down")
            @slide = @$el.find(".carousel-slide")
            if App.support.mobile()
                @slide.swipe(
                    triggerOnTouchEnd: true,
                    swipeStatus: _.bind(@swipeStatus, @)
                    allowPageScroll: 'auto'
                )
            @calculateDistanceOnLoad()
            return

        swipeStatus: (event, phase, direction, distance, fingers, duration) ->
            if phase is 'end'
                if App.utils.portrait()
                    # flip direction for 'natural' scroll
                    direction = if direction is 'left' then 'right' else 'left'
                    @calculateHorizontalPosition(direction)
                else
                    direction = if direction is 'up' then 'down' else 'up'
                    @calculateVerticalPosition(direction)
            return @

        ###
        Moves carousel and shows/hides arrows based on updated carousel position.

        @param distance    : number of pixels to move carousel, set by @calculateHorizontalPosition/@calculateVerticalPosition
        @param orientation : landscape or portrait
        @param duration    : duration of animation in milliseconds
        ###
        updateCarousel: (distance, orientation, duration=300) ->
            updateArrows = =>
                $items = @slide.children(":visible")
                if orientation is "landscape"
                    if Math.round($items.first().offset().left) >= Math.round(@container.offset().left)
                        @leftArrow.hide()
                    else
                        @leftArrow.show()
                    if Math.round($items.last().offset().left + $items.last().width()) <= Math.round(@container.offset().left + @container.width())
                        @rightArrow.hide()
                    else
                        @rightArrow.show()
                else
                    if Math.round($items.first().offset().top) >= Math.round(@container.offset().top)
                        @upArrow.hide()
                    else
                        @upArrow.show()
                    if Math.round($items.last().offset().top + $items.last().outerHeight()) <= Math.round(@container.offset().top + @container.height())
                        @downArrow.hide()
                    else
                        @downArrow.show()
                return
            @upArrow.hide()
            @downArrow.hide()
            @leftArrow.hide()
            @rightArrow.hide()
            # Small random number added to ensure transitionend is triggered.
            distance += Math.random() / 1000
            # Must resize container if switching from landscape to portrait on mobile (% based on initial style).
            height = "95%"
            top = "0"
            if orientation is "landscape"
                translate3d = 'translate3d(' + distance + 'px, 0px, 0px)'
                translate = 'translateX(' + distance + 'px)'
            else
                translate3d = 'translate3d(0px, ' + distance + 'px, 0px)'
                translate = 'translateY(' + distance + 'px)'
                if @index is 0
                    height = "88%"
                else
                    # Making room for up arrow.
                    height = "80%"
                    top = @upArrow.height()
            @container.css(
                "height": height
                "top": top
            )
            @slide.css(
                '-webkit-transition-duration': (duration / 1000).toFixed(1) + 's',
                'transition-duration': (duration / 1000).toFixed(1) + 's',
                '-webkit-transform': translate3d,
                '-ms-transform': translate,
                'transform': translate3d
            ).one('webkitTransitionEnd msTransitionEnd transitionend', updateArrows)
            if duration is 0
                updateArrows()
            return

        ###
        Calculates number of pixels to translate the carousel slide horizontally based on direction and @index.

        @param direction : left  -> after moving the leftmost item to the end of the carousel, finds the first
                                   (partially) visible item from the left and sets it as the leftmost item.
                           none  -> sets item at @index as the leftmost item in the carousel.
                           right -> finds the first item that is cut off on the right (or not visible) and sets
                                    it as the leftmost item.
        ###
        calculateHorizontalPosition: (direction='none') ->
            $container = @container
            $items = @slide.children(":visible")
            if direction is 'left'
                leftMostItem = $items[@index]
                unless leftMostItem is undefined
                    # number of pixels needed to move leftmost item to the end of carousel
                    difference = @container.width()
                    index = _.findIndex($items, (item) ->
                        # true if item is visible after moving leftmost item
                        return ($(item).width() + $(item).offset().left + difference) > $container.offset().left
                    )
            else if direction is "right"
                index = _.findIndex($items, (item) ->
                    # true if item is only partially visible
                    return ($(item).width() + $(item).offset().left) > ($container.width() + $container.offset().left)
                )
            else
                # reposition only if items overflow
                totalItemWidth = _.reduce($items, (sum, item) ->
                    return sum + $(item).outerWidth()
                , 0)
                distance = if totalItemWidth <= @container.width() then 0 else @slide.offset().left - $($items.get(@index)).offset().left 
                @updateCarousel(distance, "landscape", 0)
                return
            if index > -1
                @index = index
                distance = @slide.offset().left - $($items.get(@index)).offset().left
                @updateCarousel(distance, "landscape")
            return

        ###
        Calculates number of pixels to translate the carousel slide vertically based on direction and @index.

        @param direction : down -> finds the first item that is cut off on the bottom (or not visible) and sets
                                   it as the topmost item.
                           none -> sets item at @index as the topmost item in the carousel.
                           up   -> after moving the topmost item to the end of the carousel, finds the first
                                   (partially) visible item from the top and sets it as the topmost item.
        ###
        calculateVerticalPosition: (direction='none') ->
            $container = @container
            $items = @slide.children(":visible")
            if direction is "up"
                topMostItem = $items[@index]
                unless topMostItem is undefined
                    # number of pixels needed to move leftmost item to the end of carousel (while still being partially visible)
                    difference = @container.height()
                    index = _.findIndex($items, (item) ->
                        # true if item is visible after moving leftmost item
                        return ($(item).outerHeight() + $(item).offset().top + difference) > $container.offset().top
                    )
            else if direction is "down"
                index = _.findIndex($items, (item) ->
                    # true if item is only partially visible
                    return ($(item).outerHeight() + $(item).offset().top) > ($container.height() + $container.offset().top)
                )
            else
                distance = @slide.offset().top - $($items[@index]).offset().top
                @updateCarousel(distance, "portrait", 0)
                return
            if index > -1
                @index = index
                distance = @slide.offset().top - $($items[@index]).offset().top
                @updateCarousel(distance, "portrait")
            return

        ###
        Calculates distance after DOM elements are loaded. Assumes carousel is vertical on mobile-landscape,
        and horizontal otherwise (desktop, mobile-portrait).
        ###
        calculateDistanceOnLoad: ->
            calculateDistance = =>
                if --imageCount isnt 0
                    return
                if App.support.mobile() and App.utils.landscape()
                    @calculateVerticalPosition()
                else
                    @calculateHorizontalPosition()
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

        close: ->
            @slide.swipe("destroy")
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
    View responsible for Hero-specific things

    @constructor
    @type {ItemView}
    ###
    class module.HeroContent extends Marionette.Layout
        template: "#herovideo_template"
        regions:
            video: ".hero-video"
            carouselRegion: ".hero-carousel-region"
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
            mobileCatArr = App.option("page:mobileCategories", [])
            if App.support.mobile() and _.isArray(mobileCatArr) and not _.isEmpty(mobileCatArr)
                catArr = mobileCatArr
            else
                catArr = App.option("page:categories", [])
            categories = for category in catArr
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
