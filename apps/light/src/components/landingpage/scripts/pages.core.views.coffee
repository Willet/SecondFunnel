"use strict"

imagesLoaded = require('imagesLoaded')
require("jquery-scrollto")
require("jquery-waypoints") # register $.fn.waypoint
require("jquery-waypoints-sticky") # register $.fn.waypoint.sticky

module.exports = (module, App, Backbone, Marionette, $, _) ->
    $window = $(window)
    $document = $(document)

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
                if App.support.mobile()
                    $('body').scrollTo ".cell.info", 500
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
            product = undefined
            index = App.option("galleryIndex", 0)
            if @$el.parents("#hero-area").length
                index = App.option("heroGalleryIndex", 0)

            @$(".stl-look").each ->
                $(this).find(".stl-item").eq(index).addClass("selected")
                return

            if @model.get("tagged-products") and @model.get("tagged-products").length
                product = new module.Product(@model.get("tagged-products")[index])
                @renderSubregions(product)
            else if @model.get("template", "") is "product"
                @renderSubregions(@model)
            else
                @resizeContainer()

            if @$el.parents("#hero-area").length and not Modernizr.csspositionsticky
                $(".stick-bottom", @$el).addClass("stuck").waypoint("sticky",
                    offset: "bottom-in-view"
                    direction: "up"
                )

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
                width = Marionette.getOption(this, "width")
                if width
                    @$(".content").css("width", width + "px")
                else if App.support.mobile()
                    @$el.width($window.width()) # assign width

                # if it's a real preview, add no-scroll
                unless @$el.parents("#hero-area").length
                    @trigger("scroll:disable")
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
            # if the model has a template, let the PreviewContent try to render it
            # otherwise, assume its just hero images
            if @model.attributes.template
                return "#shopthelook_template"
            else
                return "#hero_template"
        
        ###
        @param data normal product data, or, if omitted,
        the featured product.
        ###
        initialize: (data) ->
            # TODO Refactor to utilize default coming from 'page:setup'
            # and remove App.option("featured")
            tile = if not _.isEmpty(data) then data else App.option("featured")
            if tile
                @deferred = $.when(tile)
            # Try to get it from intentRank if its setup
            else if App.intentRank.currentCategory
                tile = @getCategoryHeroImages(App.intentRank.currentCategory())
                @deferred = $.when(tile)
            # Get category from intentRank when its ready
            else 
                @deferred = $.Deferred()
                App.vent.once('intentRankInitialized', =>
                    @deferred.resolve(=>
                        return @updateCategoryHeroImages(App.intentRank.currentCategory())
                    )
                )
                        
            @deferred.done((tile) =>
                @model = new module.Tile(tile)
                @listenTo(App.vent, "windowResize", =>
                    App.heroArea.show @
                )
                return
            )

            @listenTo(App.vent, "change:category", @updateCategoryHeroImage)
            return

        onShow: ->
            @deferred.done(=>
                contentOpts = model: @model
                contentInstance = undefined
                contentInstance = new module.PreviewContent(contentOpts)
                @content.show(contentInstance)
                return
            )

        updateCategoryHeroImage: (category) ->
            @model.destroy()
            @model = new module.Tile(@getCategoryHeroImages(category))
            App.heroArea.show(@)

        getCategoryHeroImages: (category='') ->
            catObj = (App.categories.findModelByName(category) or {})
            heroImages =
                "desktopHeroImage": (catObj['desktopHeroImage'] or App.options['desktop_hero_image'])
                "mobileHeroImage": (catObj['mobileHeroImage'] or App.options['mobile_hero_image'])
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
            return templateRules

        regions:
            content: ".template.target"

        events:
            "click .close, .mask": ->
                # If we have been home then it's safe to use back()
                if App.initialPage == ''
                    Backbone.history.history.back()
                else
                    App.router.navigate("category/#{App.intentRank.currentCategory()}",
                        trigger: true
                        replace: true
                    )
                return

            "click .buy": (event) ->
                $target = $(event.target)
                # Over-write addUrlTrackingParameters for each customer
                url = App.utils.addUrlTrackingParameters( $target.find('.button').attr('href') )
                App.utils.openUrl(url)
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
                @content.show(new module.PreviewContent(contentOpts))
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
            @img_load = imagesLoaded(@$el)
            @img_load.on('always', =>
                @positionWindow()
            )
            return

        onClose: ->
            App.options.galleryIndex = 0
            App.options.galleryIndexPage = 0

            # hide this, then restore discovery.
            if @feedSwapped
                @$el.swapWith(App.discoveryArea.$el.parent())

                # handle results that got loaded while the discovery
                # area has an undefined height.
                App.layoutEngine.layout(App.discovery)
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
            if App.intentRank.currentCategory
                @selectCategory(App.intentRank.currentCategory())
            else
                App.vent.once('intentRankInitialized', =>
                    if App.intentRank.currentCategory
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
