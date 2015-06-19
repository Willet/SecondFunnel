"use strict"

Masonry = require('masonry')
GridMasonry = require('grid.masonry')
Modernizr = require('modernizr')
imagesLoaded = require('imagesLoaded')

module.exports = (module, App, Backbone, Marionette, $, _) ->

    class module.FeedView extends Marionette.CollectionView
        constructor: () ->
            @collection = new App.core.TileCollection()
            super  # this is magic, it passes forward arguments

        initialize: (options) ->
            @pagesScrolled = 1

            _.bindAll(@, 'pageScroll')

            # DEFER: this has nothing to do with this view...
            #        especially cause IntentRank then calls this thing back
            initialResults = options.initialResults
            if initialResults and initialResults.length > 0
                if $.isArray intitialResults
                    deferred = $.when(initialResults)
                else
                    deferred = $.Deferred()
                    intitialResults.onreadystatechange = ->
                        # XMLHttpRequest.DONE on IE 9+ and other browsers; support for IE8
                        if @readyState == 4 and @status == 200
                            deferred.resolve JSON.parse(@response, @responseText)

                deferred.done (initialResults) =>
                    App.options.IRResultsReturned = @collection.models.length
                    @collection.add initialResults
                    App.intentRank.addResultsShown initialResults

            $(window).scrollStopped(=>
                App.vent.trigger('scrollStopped', @)
            )
            
            @listenTo(@collection, 'request', (=>
                @isLoading = true
            ))

            @listenTo(@collection, 'sync', (=>
                @isLoading = false
            ))

            @listenTo(@collection, 'error', (=>
                @isLoading = false
            ))

            @collection.offset = 0

            App.feed = @
            return @

        onShow: ->
            @attachListeners()
            @fetchTiles()

        fetchTiles: ->
            if @isLoading
                return (new $.Deferred()).promise()
            xhr = @collection.fetch()
            xhr.done (tileInfo) =>
                @isLoading = false
                # TODO: this is not really a good identifier for end of feed
                if tileInfo and tileInfo.length is 0
                    @ended = true
                    $(".loading").hide()

                _.delay @pageScroll, 500
            @lastRequest = xhr
            xhr

        pageScroll: ->
            if @ended
                return @

            children = @$el.children()
            pageHeight = $(window).innerHeight()
            windowTop = $(window).scrollTop()
            pageBottomPos = pageHeight + windowTop
            documentBottomPos = @$el.height() - @$el.offset().top
            viewportHeights = pageHeight * App.option('prefetchHeight', 2.5)

            if not @isLoading and not @layoutInProgress and (children.length is 0 or not App.previewArea.currentView) and
                    pageBottomPos >= documentBottomPos - viewportHeights
                @fetchTiles()

            # Track scroll
            if $(window).scrollTop() > 0
                App.vent.trigger('tracking:page:scroll')

            if windowTop > @lastScrollTop
                App.vent.trigger('scrollDown', @)
            else if windowTop < @lastScrollTop
                App.vent.trigger('scrollUp', @)
            @lastScrollTop = windowTop

        attachListeners: ->
            globals = App._globals

            globals.scrollHandler =
                _.throttle (=> @pageScroll()), 500
            globals.resizeHandler = _.throttle((-> App.vent.trigger('window:resize')), 1000)
            globals.orientationChangeHandler = -> App.vent.trigger('window:rotate')

            $(window)
                .scroll(globals.scrollHandler)
                .resize(globals.resizeHandler)

            # serve orientation change event via vent
            $(window).on('rotate', globals.orientationChangeHandler)
        
        detachListeners: ->
            # detach global listeners
            globals = App._globals
            $(window)
                .unbind('scroll', globals.scrollHandler)
                .unbind('resize', globals.resizeHandler)

            if window.removeEventListener
                window.removeEventListener(
                    'orientationchange', globals.orientationChangeHandler, false
                )

        onClose: ->
            if @lastRequest
                @lastRequest.abort()
            @detachListeners()

        itemView: (itemViewOptions) ->
            # Lookup the class to use based on the template specified on the item
            model = itemViewOptions.model
            itemViewClass = App.utils.findClass('TileView',
                model.get('template'),
                App.core.TileView
            ) || App.core.TileView
            return new itemViewClass(itemViewOptions)


    class module.MasonryFeedView extends module.FeedView

        default_options:
            isAnimated: Modernizr.csstransforms3d
            transitionDuration: '0s',
            isInitLayout: false,
            isResizeBound: false    # we are handling it ourselves
            visibleStyle:
                opacity: 1
            hiddenStyle:
                opacity: 0

        initialize: (options) ->
            super # this is magic, it passes forward arguments
            # only care about the masonry options, parent class will care about rest
            @options = _.extend({}, @default_options, options.masonry)
            @recently_added = []
            @layoutInProgress = false

            App.vent.trigger('feedInitialized', @, options)
            return @

        onRender: ->
            @layout()

        layout: () ->
            if not @masonry
                @setupMasonry()

            if not @img_load
                @img_load = imagesLoaded(@$el)
                @img_load.on('always', (=> @imagesLoaded()))

        setupMasonry: ->
            @options.columnWidth = $('.tile-sizer')[0]
            if @options.forceGrid and @options.tileAspectRatio
                if App.option('debug', false)
                    console.warn("Using GridMasonry")
                @masonry = new GridMasonry(@$el[0], @options)
            else
                if App.option('debug', false)
                    console.warn("Using Masonry")
                @masonry = new Masonry(@$el[0], @options)
            @masonry.bindResize()
            @masonry.layout()

        width: ->
            @masonry.columnWidth

        reload: ->
            if @masonry
                @masonry.reloadItems()
            @layout()
            return @

        appendHtml: (view, itemview) ->
            @add(itemview.$el)

        add: ($fragment) ->
            @recently_added.push($fragment[0])
            @reorderTiles()
            @addItems()

        # Hook for re-ordering tiles before being rendered by the feed
        # Used by Ad
        reorderTiles: ->
            return

        removeTiles: (tileViews) ->
            removeComplete = (masonry, removedItems) =>
                @collection.remove(_.map(tileViews, (view) -> view.model))
                _.map(tileViews, (view) => @removeChildView(view))
                @masonry.layout()
            @masonry.on 'removeComplete', removeComplete
            @masonry.remove(_.map(tileViews, (view) -> view.$el[0]))

        addItems: _.debounce((->
            recently_added = @recently_added
            @recently_added = []
            @layoutInProgress = true

            imageLoadedCallback = (=>
                @$el.append(recently_added)
                @masonry.appended(recently_added)
                @layoutInProgress = false
                App.vent.trigger('layoutCompleted', @)
            )

            # need to wait for images to load on these items
            item_imagesloaded = imagesLoaded(recently_added)
            item_imagesloaded.on('always', imageLoadedCallback)
        ), 250, false)

        imagesLoaded: _.debounce((->
            @masonry.layout()
        ), 500)

        empty: ->
            if @masonry
                @masonry.destroy()
                @masonry = undefined
            @$el.html('')
            @layout()
