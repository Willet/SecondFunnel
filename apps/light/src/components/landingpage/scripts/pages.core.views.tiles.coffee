"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->
	###
    View for showing a Tile (or its extensions).
    This Layout contains socialButtons and tapIndicator regions.

    @constructor
    @type {Layout}
    ###
    class module.TileView extends Marionette.Layout
        tagName: App.option("tileElement", "div")
        className: "tile"

        template: "#product_tile_template"
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
            tapIndicator: ".tap-indicator-target"

        initialize: (options) ->
            data = options.model.attributes

            # expose tile "types" as classes on the dom
            if data.type
                @className = data.type.toLowerCase().split().join(' ')

            if data.template
                @className += " #{data.template}"
            @className += " tile"

            # expose model reference in form of id
            @$el.attr
                class: @className
                id: @model.cid
                data:
                    tile_id: @model.id

            # If the tile model is changed, re-render the tile
            @listenTo @model, "changed", (=> @modelChanged)

            super

        modelChanged: (model, value) ->
            @render()
            return

        onHover: (ev) ->

            # Trigger tile hover event with event and tile
            App.vent.trigger "tileHover", ev, this
            if App.support.mobile() or App.support.touch() # don't need buttons here
                return this

            # load buttons for this tile only if it hasn't already been loaded
            if not @socialButtons.$el
                @socialButtons.show new App.sharing.SocialButtons(model: @model)

            # show/hide buttons only if there are buttons
            if @socialButtons and @socialButtons.$el and @socialButtons.$el.children().length
                inOrOut = (if (ev.type is "mouseenter") then "cssFadeIn" else "cssFadeOut")
                @socialButtons.currentView.load()
                @socialButtons.$el[inOrOut] 200
            this

        onClick: (ev) ->
            tile = @model
            # open tile in popup

            # open tile in new hero area

            #

            if App.option("openTileInPopup", false)
                if App.option("tilePopupUrl")
                    # override for ad units whose tiles point to our pages
                    url = App.option("tilePopupUrl")
                else if tile.get("template") is "product"
                    url = tile.get("url")
                else if tile.get("tagged-products") and tile.get("tagged-products").length
                    url = tile.get("tagged-products")[0].url
                # missing schema
                if url.indexOf("http") is -1 and App.store.get("slug")
                    url = "http://" + App.store.get("slug") + ".secondfunnel.com" + url

                if url and url.length
                    sku = tile.get("sku")
                    tileId = tile.get("tile-id")

                    if App.option('hashPopupRedirect', false) and tileId
                        url += "#" + tileId
                    else
                        if tileId
                            url += "/tile/" + tileId
                        else if sku
                            url += "/sku/" + sku
                    App.utils.openUrl url
                return

            # clicking on social buttons is not clicking on the tile.
            unless $(ev.target).parents(".button").length
                App.router.navigate String(tile.get("tile-id")),
                    trigger: true

            return


        ###
        Before the View is rendered. this.$el is still an empty div.
        ###
        onBeforeRender: ->
            normalTileWidth = App.layoutEngine.width()
            wideableTemplates = App.option("wideableTemplates",
                image: true
                youtube: true
                banner: false
            )
            columnDetails =
                1: ""
                2: "wide"
                3: "three-col"
                4: "full"


            # templates use this as obj.image.url
            @model.set "image", @model.get("defaultImage")
            wideable = wideableTemplates[@model.get("template")]
            showWide = (Math.random() < App.option("imageTileWide", 0.5))
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
            for column in columns
                idealWidth = normalTileWidth * columns
                imageInfo = @model.get("defaultImage").width(idealWidth, true)
                if imageInfo
                    break
            @model.set image: imageInfo
            @$el.addClass columnDetails[columns]

            # Listen for the image being removed from the DOM, if it is, remove
            # the View/Model to free memory
            @$el.on "remove", (ev) =>
                if ev.target is @el
                    @close()

            return

        onMissingTemplate: ->

            # If a tile fails to load, destroy the model
            # and subsequently this tile.
            console.warn "Missing template - this view is closing.", this
            @close()
            return


        ###
        onRender occurs between beforeRender and show.
        ###
        onRender: ->
            model = @model
            tileImage = model.get("image") # assigned by onBeforeRender
            $tileImg = @$("img.focus")
            hexColor = undefined
            rgbaColor = undefined

            # set dominant colour on tile, and set the height of the tile
            # so it looks like it is all-ready
            if model.get("dominant-color")
                hexColor = model.get("dominant-color")
                rgbaColor = App.utils.hex2rgba(hexColor, 0.5)
                $tileImg.css "background-color": rgbaColor

            # this is the 'image 404' event
            if $tileImg and $tileImg.length >= 1
                $tileImg[0].onerror = =>
                    console.warn "Image error, closing views: " + arguments
                    @close()
                    return

            if App.sharing and App.option("conditionalSocialButtons", {})[model.get("colspan")]
                socialButtons = $(".socialButtons", @$el)
                buttons = new App.sharing.SocialButtons(
                    model: model
                    buttonTypes: App.option("conditionalSocialButtons", {})[model.get("colspan")]
                )
                socialButtons.append buttons.render().$el
            @$el.addClass @model.get("orientation") or "portrait"

            if App.utils.isIframe() and @$el.hasClass("landscape")
                @$el.addClass "full"

            # add view to our database
            App.vent.trigger "tracking:trackTileView", model.get("tile-id")
            return


    class module.ProductTileView extends module.TileView
        template: "#product_tile_template"


        onClick: ->
        	if App.option('openProductInPDP')
        		App.utils.openUrl( @model.get("redirect-url"))
        	else
        		# TODO: this is psuedo-code
        		parentClass.onClick()


    class module.ImageTileView extends module.TileView
        template: "#image_tile_template"


    class module.VideoTileView extends module.TileView
        template: "#video_tile_template"

        onInitialize: ->
            @$el.addClass "wide"
            return

        onClick: ->
            if @model.get("url")
                App.utils.openUrl @model.get("url")
            return

        onPlaybackEnd: (ev) ->
            App.vent.trigger "videoEnded", ev, this
            return


    class module.YoutubeTileView extends module.VideoTileView
        template: ->

        onClick: (ev) ->
            thumbId = "thumb-#{@model.cid}"
            $thumb = @$("div.thumbnail")
            if window.YT is undefined
                console.warn "Youtube Player could not load. Opening link to youtube.com"
                App.utils.openUrl @model.get("original-url")
                return
            $thumb.attr("id", thumbId).wrap "<div class=\"video-container\" />"
            player = new window.YT.Player(thumbId,
                width: $thumb.width()
                height: $thumb.height()
                videoId: @model.attributes["original-id"] or @model.id
                playerVars:
                    wmode: "opaque"
                    autoplay: 1
                    controls: false

                events:
                    onReady: $.noop
                    onStateChange: (newState) =>
                        App.tracker.videoStateChange @model.attributes["original-id"] or @model.id, newState
                        switch newState
                            when window.YT.PlayerState.ENDED
                                @onPlaybackEnd()
                            else

                    onError: $.noop
            )
            return