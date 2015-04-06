"use strict"

require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky

module.exports = (module, App, Backbone, Marionette, $, _) ->
    $window = $(window)
    $document = $(document)

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
