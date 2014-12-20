"use strict"

imagesLoaded = require('imagesLoaded')
require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky

module.exports = (module, App, Backbone, Marionette, $, _) ->

    $window = $(window)
    $document = $(document)

    # specifically, pages scrolled downwards; pagesScrolled defaults
    # to 1 because the user always sees the first page.
    pagesScrolled = 1

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
                    window.open url, App.utils.openInWindow()
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


    class module.ImageTileView extends module.TileView
        template: "#image_tile_template"


    class module.VideoTileView extends module.TileView
        template: "#video_tile_template"

        onInitialize: ->
            @$el.addClass "wide"
            return

        onClick: ->
            if @model.get("url")
                window.open @model.get("url"), App.utils.openInWindow()
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
                console.warn "YT could not load. Opening link to youtube.com"
                window.open @model.get("original-url"), App.utils.openInWindow()
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


    class module.TileCollectionView extends Marionette.CollectionView


    ###
    Widgets that make up a Product Info in a Expanded Content

    @constructor
    @type {ItemView}
    ###
    class module.ProductInfoView extends Marionette.ItemView
        initialize: (options) ->
            unless options.infoItem
                throw new Error("infoItem is a required property")
            @options = options
            return

        getTemplate: ->
            "#product_#{@options.infoItem}_template"


    ###
    A Shop The Look

    @constructor
    @type {Layout}
    ###
    class module.ExpandedContent extends Marionette.Layout
        regions:
            price: ".price"
            title: ".title"
            buy: ".buy"
            description: ".description"
            galleryMainImage: ".gallery-main-image"
            gallery: ".gallery"
            galleryDots: ".gallery-dots"
            socialButtons: ".social-buttons"

        events:
            "click .stl-look .stl-item": (event) ->
                $el = @$el
                $ev = $(event.target)
                $targetEl = if $ev.hasClass('stl-item') then $ev else $ev.parents('.stl-item')
                
                $targetEl.addClass("selected").siblings().removeClass "selected"
                index = $targetEl.data("index")
                product = @model.get("tagged-products")[index]
                productModel = new module.Product(product)

                if $el.parents("#hero-area").length
                    # this is a featured content area
                    App.options.heroGalleryIndex = index
                    App.options.heroGalleryIndexPage = 0
                else
                    # likely a pop-up
                    App.options.galleryIndex = index
                    App.options.galleryIndexPage = 0
                if product.images.length is 1
                    $el.find(".gallery, .gallery-dots").addClass "hide"
                else
                    $el.find(".gallery, .gallery-dots").removeClass "hide"
                @renderSubregions productModel
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
                @model.set "tagged-products", _.sortBy(@model.get("tagged-products"), (obj) ->
                    -1 * parseFloat((obj.price or "$0").substr(1), 10)
                )

            # templates use this as obj.image.url
            @model.set "image", image
            return

        initialize: ->
            @$el.attr
                id: "preview-#{@model.cid}"
            return

        close: ->
            # See NOTE in onShow
            unless App.support.isAnAndroid()
                $(document.body).removeClass "no-scroll"

            @$(".stick-bottom").waypoint "destroy"
            return

        renderSubregions: (product) ->
            # SocialButtons are a View
            if App.option('page:socialButtons') and App.option('page:socialButtons').length
                @socialButtons.show new App.sharing.SocialButtons model: @model

            # Refactor subregions to be Views/ItemViews
            # for now, remove socialButtons region and render widgets
            keys = _.without _.keys(@regions), 'socialButtons'

            _.each keys, (key) =>
                @[key].show new module.ProductInfoView(
                    model: product
                    infoItem: key
                )
                return
            App.utils.runWidgets this
            @resizeContainer()
            return

        resizeContainer: ->
            shrinkContainer = (element) ->
                ->
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
            product = undefined
            index = App.option("galleryIndex", 0)
            if @$el.parents("#hero-area").length
                index = App.option("heroGalleryIndex", 0)

            @$(".stl-look").each ->
                $(this).find(".stl-item").eq(index).addClass "selected"
                return

            if @model.get("tagged-products") and @model.get("tagged-products").length
                product = new module.Product(@model.get("tagged-products")[index])
                @renderSubregions product
            else if @model.get("template", "") is "product"
                @renderSubregions @model
            else
                @resizeContainer()

            if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
                $(".stick-bottom", @$el).addClass("stuck").waypoint "sticky",
                    offset: "bottom-in-view"
                    direction: "up"

            return


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
                    t.indexOf("mobile") > -1
                )
            templateRules

        onRender: ->
            # hide discovery, then show this window as a page.
            if App.support.mobile()
                @trigger "swap:feed", @$el # out of scope
                @trigger "feed:swapped"
            App.vent.trigger "previewRendered", this
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
            unless App.support.isAnAndroid()
                width = Marionette.getOption(this, "width")
                if width
                    @$(".content").css "width", width + "px"
                else if App.support.mobile()
                    @$el.width $window.width() # assign width

                # if it's a real preview, add no-scroll
                unless @$el.parents("#hero-area").length
                    @trigger "scroll:disable"
            return


    ###
    View responsible for the "Hero Area"
    (e.g. Shop-the-look, featured, or just a plain div)

    @constructor
    @type {Layout}
    ###
    class module.HeroAreaView extends Marionette.Layout
        className: "previewContainer"
        regions:
            content: ".content"

        getTemplate: ->

            # if page config contains a product, render hero area with a
            # template that supports it
            if App.option("featured") isnt undefined and $("#shopthelook_template").length
                return "#shopthelook_template"
            "#hero_template"


        ###
        @param data normal product data, or, if omitted,
        the featured product.
        ###
        initialize: (data) ->
            tile = if not _.isEmpty(data) then data else
                App.option("featured") or @getCategoryHeroImages App.intentRank.category

            @model = new module.Tile(tile)
            @listenTo App.vent, "windowResize", =>
                App.heroArea.show @
                return

            @listenTo App.vent, "change:category", @updateCategoryHeroImage

            return

        onShow: ->
            contentOpts = model: @model
            contentInstance = undefined
            contentInstance = new module.PreviewContent(contentOpts)
            @content.show contentInstance
            return

        updateCategoryHeroImage: (category) ->
            @model.destroy()
            @model = new module.Tile(@getCategoryHeroImages(category))
            App.heroArea.show @

        getCategoryHeroImages: (category='') ->
            catObj = App.categories.findModelByName(category) or {}
            heroImages =
                "desktopHeroImage": catObj['desktopHeroImage'] or App.options['desktop_hero_image']
                "mobileHeroImage": catObj['mobileHeroImage'] or App.options['mobile_hero_image']
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
                    t.indexOf("mobile") > -1
                )
            templateRules

        regions:
            content: ".template.target"

        events:
            "click .close, .mask": ->

                #If we have been home then it's safe to use back()
                if App.initialPage is ""
                    Backbone.history.history.back()
                else
                    hashnav = if App.intentRank.options.category then "#" + App.intentRank.options.category else ""
                    App.router.navigate hashnav,
                        trigger: true
                        replace: true
                return

            "click .buy": (event) ->
                $target = $(event.target)
                # Over-write addUrlTrackingParameters for each customer
                url = App.utils.addUrlTrackingParameters( $target.find('.button').attr('href') )
                window.open url, App.utils.openInWindow()
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
            self = this

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
            contentInstance.on "feed:swapped", ->
                self.triggerMethod "feed:swapped"
                return

            contentInstance.on "swap:feed", ($el) ->
                App.discoveryArea.$el.parent().swapWith $el
                return

            contentInstance.on "scroll:disable", ->
                $(document.body).addClass "no-scroll"
                return

            @content.show contentInstance
            App.previewLoadingScreen.hide()
            @listenTo App.vent, "rotate", (width) ->
                # On change in orientation, we want to rerender our layout
                # this is automatically unbound on close, so we don't have to clean
                heightMultiplier = (if App.utils.portrait() then 1 else 2)
                self.$el.css height: (if App.support.mobile() then heightMultiplier * $window.height() else "")
                self.content.show new module.PreviewContent(contentOpts)
                return

            return

        positionWindow: ->
            windowMiddle = $window.scrollTop() + $window.height() / 2
            if App.windowMiddle
                windowMiddle = App.windowMiddle
            if App.windowHeight and App.support.mobile()
                @$el.css "height", App.windowHeight
            @$el.css "top", Math.max(windowMiddle - (@$el.height() / 2), 0)

        onShow: ->
            @img_load = imagesLoaded(@$el)
            @img_load.on 'always', =>
                @positionWindow()
            return

        onClose: ->
            App.options.galleryIndex = 0
            App.options.galleryIndexPage = 0

            # hide this, then restore discovery.
            if @feedSwapped
                @$el.swapWith App.discoveryArea.$el.parent()

                # handle results that got loaded while the discovery
                # area has an undefined height.
                App.layoutEngine.layout App.discovery
                App.layoutEngine.masonry.resize()
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
                    t.indexOf("mobile") > -1
                )
            templateRules

        events:
            'click': (event) ->
                category = @model.get("name")
                $el = @$el
                $subCatEl = $el.find('.sub-category')

                if $subCatEl.length and not $el.hasClass 'expanded'
                    # First click, expand subcategories
                    $el.addClass 'expanded'
                    $el.siblings().removeClass 'expanded'
                else
                    # First click w/ no subcategories or
                    # second click w/ categories, select category
                    $el.removeClass 'expanded'
                    unless $el.hasClass 'selected' and not $subCatEl.hasClass 'selected'
                        @selectCategoryEl($el)

                        App.router.navigate(category,
                            trigger: true
                        )
                return false # stop propogation

            'click .sub-category': (event) ->
                $el = @$el
                category = @model
                $ev = $(event.target)
                $subCatEl = if $ev.hasClass 'sub-category' then $ev else $ev.parent '.sub-category'

                # Close categories drop-down
                $el.removeClass 'expanded'

                # Retrieve subcategory object
                subCategory = _.find category.get('subCategories'), (subcategory) ->
                    return subcategory.name == $subCatEl.data('name')

                # switch to the selected category if it has changed
                unless $el.hasClass 'selected' and $subCatEl.hasClass 'selected' and not $subCatEl.siblings().hasClass 'selected'
                    @selectCategoryEl($subCatEl)

                    # If subCategory leads with "|", its an additional filter on the parent category
                    if subCategory['name'].charAt(0) == "|"
                        switchCategory = category.get("name") + subCategory['name']
                    # Else, subCategory is a category
                    else
                        switchCategory = subCategory['name']

                    App.router.navigate(switchCategory,
                        trigger: true
                    )
                return false # stop propogation

        # Apply the 'selected' class to a category or sub-category element
        selectCategoryEl: (el) ->
            $el = $(el)

            if $el.hasClass 'category'
                # remove selected from child sub-categories
                $el.find('.sub-category').removeClass 'selected'
                # switch to the selected category if it has changed
                unless $el.hasClass 'selected'
                    $el.addClass 'selected'
                    # remove selected from other categories
                    $el.siblings().each ->
                        self = $(@)
                        self.removeClass 'selected'
                        self.find('.sub-category').removeClass 'selected'

            else if $el.hasClass 'sub-category'
                $catEl = $el.parents('.category')
                
                # switch to selected sub-category
                $el.addClass 'selected'
                $el.siblings().removeClass 'selected'
                # switch to selected category if not already
                unless $catEl.hasClass 'selected'
                    $catEl.addClass 'selected'
                    # remove selected from other categories
                    $catEl.siblings().each ->
                        self = $(@)
                        self.removeClass 'selected'
                        self.find('.sub-category').removeClass 'selected'


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
            categories = for category in App.option catOpt, []
                if typeof(category) is "string"
                    category = {name: category}
                category

            if categories.length > 0

                # This specifies that there should be a home button, by default, this is true.
                if App.option("categoryHome")
                    if App.option("categoryHome").length
                        home = App.option("categoryHome")
                    else
                        home = ""
                    categories.unshift {name: home}

                @collection = new module.CategoryCollection categories, model: module.Category
            else
                @collection = new module.CategoryCollection [], model: module.Category

            # Watch for updates to feed, generally from intentRank
            @listenTo App.vent, "change:category", @selectCategory

            # Enable sticky category bar
            if App.option("page:stickyCategories")
                @$el.parent().waypoint('sticky')
            
            return @

        onRender: ->
            App.vent.once 'finished', ->
                if App.intentRank.category
                    @selectCategory category
            return @

        ###
        Given a category string, find it and select it (add the .selected class)
        Returns boolean if category / sub-category found
        @returns {bool}
        ###
        selectCategory: (category) ->
            try
                catMapObj = @collection.findModelByName category
                catView = @children.findByModel(catMapObj.category)

                $el = catView.$el
                $catEl = catView.$el.find(".sub-category[data-name='#{catMapObj.subCategory}']")

                $target = if catMapObj.subCategory then $catEl else $el
                catView.selectCategoryEl $target
                return true
            catch err
                if App.option 'debug', false
                    console.error "Could not find category '#{category}' because:\n#{err.message}"
            return false
