"use strict"

require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky
swipe = require('jquery-touchswipe')
imagesLoaded = require('imagesLoaded')

module.exports = (module, App, Backbone, Marionette, $, _) ->
    $window = $(window)
    $document = $(document)

    ###
    View that provides carousel animations/swipe gestures without knowledge of contained content!

    Notes:
        - carousel initialization will render items using carousel_template
        - can add any additional children to .carousel-slide
        - carousel behavior is determined by visible child elements of .carousel-slide
    
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
            # If items are Backbone models, flatten them to their attributes
            data =
                items: ((if item.toJSON? then item.toJSON() else item) for item in @items)
                index: @index
                attrs: @attrs
            return data

        getTemplate: ->
            if @attrs.template
                return "##{@attrs.template}_carousel_template"
            else
                return "#carousel_template"

        ###
        @param attrs : array of extra attributes (e.g. lookImageSrc from ExpandedContent)
        @param index : index of leftmost/topmost item in the carousel
        @param items : array of items to display in the carousel
        ###
        initialize: (options) ->
            @attrs = options['attrs'] or []
            @index = options['index'] or 0
            @items = options['items'] or []
            return

        onRender: ->
            # Get rid of that pesky wrapping-div
            @$el = @$el.children() # NOTE 1st child will be come element, all other children will be dropped
            @$el.unwrap() # Unwrap the element to prevent infinitely nesting elements during re-render
            @setElement(@$el)
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
            imagesLoaded($("img", @el), (=> @calculateDistance()))
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
                unless $items.length == 0
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
            
            if orientation is "landscape"
                translate3d = 'translate3d(' + distance + 'px, 0px, 0px)'
                translate = 'translateX(' + distance + 'px)'
                # Must resize container if switching from landscape to portrait on mobile (% based on initial style).
                height =  @attrs.landscape?.height or "95%"
                top = "0"
            else
                translate3d = 'translate3d(0px, ' + distance + 'px, 0px)'
                translate = 'translateY(' + distance + 'px)'
                if @index is 0
                    height = @attrs.portrait?.fullHeight or "88%"
                    top = "0"
                else
                    # Making room for up arrow.
                    height = @attrs.portrait?.reducedHeight or @attrs.portrait?.fullHeight or "80%"
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
        Helper method that calls the correct carousel slide translation depending on the use case
        ###
        calculateDistance: ->
            if App.support.mobile()
                if App.utils.landscape()
                    @calculateVerticalPosition()
                else
                    @calculateHorizontalPosition()
            else if @attrs['orientation'] is "landscape"
                @calculateHorizontalPosition()
            else if @attrs['orientation'] is "portrait"
                @calculateVerticalPosition()
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
                        return Math.round($(item).width() + $(item).offset().left + difference) > Math.round($container.offset().left)
                    )
            else if direction is "right"
                index = _.findIndex($items, (item) ->
                    # true if item is only partially visible
                    return Math.round($(item).width() + $(item).offset().left) > Math.round($container.width() + $container.offset().left)
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

        destroy: ->
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
            try
                @player?.destroy()
            catch error
                console.error("Youtube Error: %O", error)
                # Ignore errors destroying the Youtube player
                # Can happen while it is still initializing
                # This will kill all youtube videos on the page!
            return

    
    ###
    View responsible for Hero-specific things

    @constructor
    @type {LayoutView}
    ###
    class module.HeroContent extends Marionette.LayoutView
        template: "#herovideo_template"
        id: -> return "hero-#{@model.cid}"
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
    @type {LayoutView}
    ###
    class module.HeroAreaView extends Marionette.LayoutView
        className: "heroContainer"
        template: "#hero_container_template"
        regions:
            content: ".content"
        
        ###
        @param options: {
            tile: {object} (tile or tileJson)
            tileId: {number} (tile-id)
            updateWithCategory: {boolean, default: true} if true, hero images updated with category changes 
        }
        ###
        initialize: (options) ->
            tile = _.get(options, 'tile', undefined)
            tileId = Number(_.get(options, 'tileId', undefined))
            updateWithCategory = Boolean(_.get(options, 'updateWithCategory', true))
            @tileLoaded = $.Deferred()
            # every path below must resolve @tileLoaded
            # tile can be an object (tileJson)
            if tile?
                @tileLoaded.resolve(tile)
            # tileId is either a tile-id or NaN
            else if tileId
                tileLoadedResolve = =>
                    @tileLoaded.resolve(arguments[0])
                tileLoadedFailed = =>
                    @tileLoaded.resolve()
                module.Tile.getById(tileId, tileLoadedResolve, tileLoadedFailed)
            # no tile, get category from intentRank
            else
                if App.intentRank?.currentCategory?
                    tile = @_getCategoryHeroTile(App.intentRank.currentCategory())
                    @tileLoaded.resolve(tile)
                # get category from intentRank when its ready
                else
                    App.vent.once('intentRankInitialized', =>
                        tile = @_getCategoryHeroTile(App.intentRank.currentCategory())
                        @tileLoaded.resolve(tile)
                    )
            # tile can be a {Tile} or {object} tileJson
            @tileLoaded.done((tile) =>
                if _.isObject(tile) and not _.isEmpty(tile)
                    @model = if _.contains(tile.type, 'Tile') \
                             then tile \
                             else module.Tile.getOrCreate(tile)
                else
                    @model = undefined

                @listenTo(App.vent, "windowResize", =>
                    @render()
                )
                if updateWithCategory
                    @listenTo(App.vent, "change:category", @updateCategoryHeroImages)
                return @
            )

        onShow: ->
            @tileLoaded.done(=>
                @_updateContent()
            )

        updateContent: ->
            if @_isShown
                @_updateContent()

        updateCategoryHeroImages: (category) ->
            @model?.destroy()
            @model = @_getCategoryHeroTile(category)
            @updateContent()

        _updateContent: ->
            # Only to be called after view is shown
            if @model?
                contentInstance = if _.contains(@model.type?.toLowerCase(), "hero") \
                                  then new module.HeroContent(model: @model)
                                  else new module.PreviewContent(model: @model)
                @content.show(contentInstance)
            else
                @content.destroy()
            return

        _getCategoryHeroTile: (category='') ->
            # Generates a HeroTile to be displayed
            # default '' means home
            category = if not _.isEmpty(category) then category else App.option('page:home:category')
            catObj = (App.categories.findModelByName(category) or {})
            heroImage = (catObj['heroImage'] or App.option('page:defaults:heroImage'))
            mobileHeroImage = (catObj['mobileHeroImage'] or App.option('page:defaults:mobileHeroImage'))
            heroTitle = (catObj['heroTitle'] or App.option('page:defaults:heroTitle'))
            mobileHeroTitle = (catObj['mobileHeroTitle'] or App.option('page:defaults:mobileHeroTitle'))
            if heroImage or heroTitle
                heroObj =
                    "heroImage": heroImage
                    "mobileHeroImage": mobileHeroImage or heroImage
                    "heroTitle": heroTitle
                    "mobileHeroTitle": mobileHeroTitle or heroTitle
                    "template": "hero"
                tile = new module.HeroTile(heroObj)
            else
                tile = undefined
            return tile


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

        initialize: (options) ->
            @parent = options.parent

        events:
            'click': (event) ->
                categoryName = @model.get("name")
                categoryUrl = @model.get("url")
                $el = @$el
                $subCatEl = $el.find('.sub-category')

                if $subCatEl.length and not $el.hasClass('expanded')
                    # First click, expand subcategories
                    @parent?.expandCategory($el)
                else
                    # First click w/ no subcategories or
                    # second click w/ categories, select category
                    @parent?.contractCategories()
                    
                    if categoryUrl
                        App.utils.openUrl(categoryUrl)
                    else if categoryName
                        # only open again if it isn't already open
                        unless $el.hasClass('selected') and not $subCatEl.hasClass('selected')
                            @selectCategoryEl($el)

                            App.router.navigate("category/#{categoryName}",
                                trigger: true
                            )
                return false # stop propogation

            'click .sub-category': (event) ->
                $el = @$el
                category = @model
                $ev = $(event.target)
                $subCatEl = if $ev.hasClass('sub-category') then $ev else $ev.parent('.sub-category')

                # Close categories drop-down
                @parent?.contractCategories()

                # Retrieve subcategory object
                # TODO: refactor to index by model id
                subCategory = _.find(category.get('subCategories'), (subcategory) ->
                    return subcategory.name == $subCatEl.data('name')
                )

                # url's take priority over category name's
                if subCategory?['url']
                    App.utils.openUrl(subCategory['url'])

                # else switch to the selected category if it has changed
                else
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
                    @parent?.unselectCategories()
                    $el.addClass('selected')

            else if $el.hasClass('sub-category')
                # switch to selected sub-category
                @collection?.unselectCategories()
                $el.addClass('selected').parents('.category').addClass('selected')
            return @


    ###
    A collection of Categories to display.

    @constrcutor
    @type {CollectionView}
    ###
    class module.CategoryCollectionView extends Marionette.CollectionView
        tagName: "div"
        className: "category-area"
        childView: module.CategoryView
        childViewOptions: (model, index) ->
            return parent: @

        initialize: (options) ->
            @collection = new module.CategoryCollection(_.get(options, 'categories', []),
                                                        model: module.Category)

            # Watch for updates to feed, generally from intentRank
            @listenTo(App.vent, "change:category", @selectCategory)

            return @
        
        onRender: ->
            if App.intentRank.currentCategory()?
                @selectCategory(App.intentRank.currentCategory())
            else
                App.vent.once('intentRankInitialized', =>
                    if App.intentRank.currentCategory()?
                        @selectCategory(App.intentRank.currentCategory())
                )
            return @

        # Remove the 'selected' class from all category and sub-category elements
        unselectCategories: ->
            @$el.find('.selected').removeClass('selected')
            return @

        expandCategory: ($el) ->
            @$el.find(".#{@childView::className}.expanded")?.removeClass('expanded')
            $el.filter(".#{@childView::className}")?.addClass('expanded')
            App.vent.trigger('categories:expanded')

        contractCategories: () ->
            @$el.find(".#{@childView::className}.expanded")?.removeClass('expanded')
            App.vent.trigger('categories:contracted')

        onShow: ->
            # Enable sticky category bar
            sticky = App.option("page:stickyCategories")
            if _.isString(sticky)
                if sticky == 'desktop-only' and not App.support.mobile()
                    @$el.parent().waypoint('sticky')
                else if sticky == 'mobile-only' and App.support.mobile()
                    @$el.parent().waypoint('sticky')
            else if _.isBoolean(sticky) and sticky
                @$el.parent().waypoint('sticky')

            return @

        ###
        Given a category string, find it and select it (add the .selected class)
        An empty string '' will remove selection from all categories
        Returns boolean if category / sub-category found
        
        @returns {bool}
        ###
        selectCategory: (category) ->
            # Unselect currently selected
            @unselectCategories()
            if category == ''
                # home category
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
                    console.warn("Could not select category '#{category}' because:\n#{err.message}")
            return false
