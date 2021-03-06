"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->
    ###
    View for showing a Tile (or its extensions).
    This LayoutView contains socialButtons and tapIndicator regions.
    
    @constructor
    @type {LayoutView}
    ###
    class module.TileView extends Marionette.LayoutView
        type: "TileView"
        tagName: "div"
        template: "#product_tile_template"
        id: -> return @model.cid
        className: -> return "tile #{String(@model.get('template'))}"
        templates: ->
            templateRules = [
                "#<%= options.store.slug %>_<%= data.source %>_<%= data.template %>_mobile_tile_template" # gap_instagram_image_mobile_tile_template
                "#<%= data.source %>_<%= data.template %>_mobile_tile_template" # instagram_image_mobile_tile_template
                "#<%= options.store.slug %>_<%= data.template %>_mobile_tile_template" # gap_image_mobile_tile_template
                "#<%= data.template %>_mobile_tile_template" # image_mobile_tile_template
                "#<%= options.store.slug %>_<%= data.source %>_<%= data.template %>_tile_template" # gap_instagram_image_tile_template
                "#<%= data.source %>_<%= data.template %>_tile_template" # instagram_image_tile_template
                "#<%= options.store.slug %>_<%= data.template %>_tile_template" # gap_image_tile_template
                "#<%= data.template %>_tile_template" # image_tile_template
                "#product_mobile_tile_template" # fallback
                "#product_tile_template" # fallback
            ]
            unless App.support.mobile()

                # remove mobile templates if it isn't mobile, since they take
                # higher precedence by default
                templateRules = _.reject(templateRules, (t) ->
                    t.indexOf("mobile") > -1
                )
            templateRules

        events:
            click: "onClick"
            mouseenter: "onHover"
            mouseleave: "onHover"

        regions: # if ItemView, the key is 'ui': /docs/marionette.itemview.md#organizing-ui-elements
            socialButtons: ".social-buttons"

        defaultWideableTemplates:
            image: true
            gif: true
            youtube: true
            banner: false
            product: false

        initialize: (options) ->
            # expose model reference in form of id
            @$el.attr("data-tile-id": "#{@model.get('tile-id')}")

            # If the tile model is changed, re-render the tile
            @listenTo(@model, "changed", (=> @modelChanged))
            super

        modelChanged: (model, value) ->
            @render()
            return

        onHover: (ev) ->

            # Trigger tile hover event with event and tile
            App.vent.trigger "tileHover", ev, @
            if App.support.mobile() or App.support.touch() # don't need buttons here
                return @

            # load buttons for this tile only if it hasn't already been loaded
            if not @socialButtons.$el
                @socialButtons.show new App.sharing.SocialButtons(model: @model)

            # show/hide buttons only if there are buttons
            if @socialButtons?.$el?.children()?.length
                inOrOut = (if (ev.type is "mouseenter") then "cssFadeIn" else "cssFadeOut")
                @socialButtons.currentView.load()
                @socialButtons.$el[inOrOut] 200
            return @

        onClick: (ev) ->
            # clicking on social buttons is not clicking on the tile
            # this is a dirty check
            if $(ev.target).parents(".button").length
                return

            App.vent.trigger("tracking:tile:open", @model)

            if App.option("page:tiles:openTileInHero", false)
                # open tile in hero area
                App.router.navigate("tile/#{String(@model.get('tile-id'))}", trigger: true)
            else
                # open tile in popup
                App.router.navigate("preview/#{String(@model.get('tile-id'))}", trigger: true)
            return


        ###
        Before the View is rendered. this.$el is still an empty div.
        ###
        onBeforeRender: ->
            normalTileWidth = App.feed.width()
            wideableTemplates = _.extend({}, @defaultWideableTemplates, App.option("page:tiles:wideableTemplates", {}))
            columnDetails =
                1: ""
                2: "wide"
                3: "full"

            wideable = wideableTemplates[@model.get("template")]
            showWide = (Math.random() < App.option("page:tiles:wideProbability", 0.5))
            if _.isNumber(@model.get("colspan"))
                columns = @model.get("colspan")
            else if wideable and showWide
                columns = 2
            else
                columns = 1
            if App.support.mobile() # maximum of 2 columns
                if columns < 2
                    columns = 1
                else
                    columns = 2
            idealWidth = normalTileWidth * columns
            # Update default image width to at least idealWidth
            @model.get("defaultImage").width(idealWidth)
            @$el.addClass(columnDetails[columns])

            # Listen for the image being removed from the DOM, if it is, remove
            # the View/Model to free memory
            @$el.on("remove", (ev) =>
                if ev.target is @el
                    @destroy
            )
            return

        onMissingTemplate: ->
            # If a tile fails to load, destroy the model
            # and subsequently this tile.
            console.warn "Missing template - this view is closing.", this
            @destroy()
            return


        ###
        onRender occurs between beforeRender and show.
        ###
        onRender: ->
            tileImage = @model.get("image") # assigned by onBeforeRender
            $tileImg = @$("img.focus")
            hexColor = undefined
            rgbaColor = undefined

            # set dominant colour on tile, and set the height of the tile
            # so it looks like it is all-ready
            if @model.get("dominant-color")
                hexColor = @model.get("dominant-color")
                rgbaColor = App.utils.hex2rgba(hexColor, 0.5)
                $tileImg.css("background-color": rgbaColor)

            # this is the 'image 404' event
            if $tileImg and $tileImg.length >= 1
                $tileImg[0].onerror = =>
                    console.warn("Image error, closing views: " + arguments)
                    @destroy()
                    return

            if App.sharing and App.option("conditionalSocialButtons", {})[@model.get("colspan")]
                socialButtons = $(".socialButtons", @$el)
                buttons = new App.sharing.SocialButtons(
                    model: @model
                    buttonTypes: App.option("conditionalSocialButtons", {})[@model.get("colspan")]
                )
                socialButtons.append(buttons.render().$el)
            @$el.addClass(@model.get("orientation") or "portrait")

            if App.utils.isIframe() and @$el.hasClass("landscape")
                @$el.addClass("full")

            # add view to our database
            App.vent.trigger("tracking:tile:view", @model.get("tile-id"))
            return


    class module.ProductTileView extends module.TileView
        # A product tile displays one product
        type: "ProductTileView"
        template: "#product_tile_template"

        onClick: ->
            App.vent.trigger('tracking:tile:bannerExit', @model)
            if App.option('page:tiles:openProductTileInPDP')
                App.utils.openUrl(@model.get("url"))
            else
                super
            return


    class module.ImageTileView extends module.TileView
        # An image tile is an image that is tagged with one or more products
        type: "ImageTileView"
        template: "#image_tile_template"


    class module.GifTileView extends module.TileView
        # An image tile that has a gif - enables progressive loading
        type: "GifTileView"
        template: "#gif_tile_template"

        initialize: ->
            super
            @listenToOnce App.vent, "layoutCompleted", =>
                # First load image, then load gif
                try
                    if @model.get("images") and @model.get("images")[0].get("gifUrl")
                        gifUrl = @model.get("images")[0].get("gifUrl")
                        @$("img.focus").attr("src", gifUrl)
                catch e
                    console.warn "This gif does not have a base image.", @get("images")


    class module.CollectionTileView extends module.ImageTileView
        # An image with a feed of products
        type: "CollectionTileView"


    class module.BannerTileView extends module.TileView
        ###
        A banner tile is any piece of content that links to a 3rd party site
        To be used sparingly to achieve client requests
        ###
        type: "BannerTileView"
        template: "#image_tile_template"

        onClick: ->
            App.vent.trigger('tracking:tile:bannerExit', @model)
            if @model.get("redirectUrl")
                App.utils.openUrl(@model.get("redirectUrl"))
            return false # stop event propogation


    class module.VideoTileView extends module.TileView
        type: "VideoTileView"
        template: "#video_tile_template"

        onClick: ->
            if @model.get("url")
                App.utils.openUrl(@model.get("url"))
            return

        onPlaybackEnd: (ev) ->
            App.vent.trigger("videoEnded", ev, @)
            return


    class module.YoutubeTileView extends module.TileView
        type: "YoutubeTileView"
        template: "youtube_tile_template"

        regions:
            _.extend({}, module.TileView::regions, # super ugly syntax
                video: ".youtube-video"
            )
        onClick: (ev) ->
            thumbId = "thumb-#{@model.cid}"
            $thumb = @$("div.thumbnail")
            $thumb.attr("id", thumbId).wrap($("<div>", {'class': 'youtube-video'}))

            video = @model.get('video')
            if video?
                videoInstance = new module.YoutubeVideoView(video)
                @video.show(videoInstance)
            return


    class module.HeroTileView extends module.TileView
        type: "HeroTileView"
        template: "#hero_template"


    class module.HerovideoTileView extends module.HeroTileView
        type: "HerovideoTileView"
        template: "#herovideo_template"

