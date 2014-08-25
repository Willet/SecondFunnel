Backbone = require('backbone')
Marionette = require('backbone.marionette')
$ = require('jquery')
_ = require('underscore')
Masonry = require('masonry')
Modernizr = require('modernizr')
imagesLoaded = require('imagesLoaded')

class FeedView extends Marionette.CollectionView

    constructor: () ->
        @collection = new App.core.TileCollection()
        super arguments

    initialize: (options) ->
        # DEFER: check if anything listens to this
        #        itemview's events are already delegated...
        #        by marionette
        @on 'itemview:item:clicked', =>
            @trigger('collection:item:clicked')
        @pagesScrolled = 1

        # Listen to Application Events
        @listenTo App.vent, 'change:category', @categoryChanged, @
        @listenTo App.vent, 'feedEnded', => @ended = true

        @attachListeners()

        # DEFER: this has nothing to do with this view...
        #        especially cause IntentRank then calls this thing back
        initialResults = options.initialResults
        if initialResults and initialResults.length > 0
            @isLoading = true
            if $.isArray intitialResults
                deferred = $.when .initialResults
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


        @listenTo @collection, 'request', =>
            @isLoading = true

        @listenTo @collection, 'sync', =>
            @isLoading = false

        @listenTo @collection, 'error', =>
            @isLoading = false

        # immediately fetch more from IR
        @fetchTiles()

        # DEFER: REMOVE THIS (its really not needed)
        App.discovery = @
        @

    fetchTiles: (options, tile) ->
        if @isLoading
            return (new $.Deffered()).promise()
        xhr = @collection.fetch()
        xhr.done (tileInfo) =>
            @isLoading = false
            # TODO: this is not really a good identifier for end of feed
            if tileInfo and tileInfo.length is 0
                @ended = true
                $(".loading").hide() # DEFER: hack
                App.vent.trigger('feedEnded', @)
        xhr

    # TODO: weird location for this function
    categoryChanged: (event, category) ->
        App.tracker.changeCategory(category)
        if @isLoading
            @on 'loadingFinished', _.once( =>
                @empty(@)
                @ended = false
                $(".loading").show() # DEFER: hack
                @fetchTiles()
            )

    pageScroll: ->
        if @ended
            return @

        children = @$el.children()
        pageHeight = $(window).innerHeight()
        windowTop = $(window).scrollTop()
        pageBottomPos = pageHeight + windowTop
        documentBottomPos = @$el.height() - @$el.offset().top
        viewportHeights = pageHeight * App.option('prefetchHeight', 2.5)

        if not @isLoading and (children.length is 0 or not App.previewArea.currentView) and
                pageBottomPos >= documentBottomPos - viewportHeights
            @fetchTiles()

        # TODO: this is global tracking stuff, really does not need to be on this view
        # Did the user scroll ever ?
        if $(window).scrollTop() > 0
            App.vent.trigger 'tracking:trackEvent',
                category: 'visit'
                action: 'scroll'

        # TODO: this is global tracking stuff, really does not need to be on this view
        # how many pages did the user scroll
        if (windowTop / pageHeight) > @pagesScrolled
            App.vent.trigger 'tracking:trackEvent',
                category: 'visit'
                action: 'scroll'
                label: @pagesScrolled
            @pagesScrolled++

        if windowTop > @lastScrollTop
            App.vent.trigger('scrollDown', @)
        else if windowTop < @lastScrollTop
            App.vent.trigger('scrollUp', @)
        @lastScrollTop = windowTop

    attachListeners: ->
        globals = App._globals

        globals.scrollHandler =
            _.throttle (=> @pageScroll()), 500
        globals.resizeHandler =
            _.throttle (-> $('.resizable', document).trigger('resize')), 1000
        globals.orientationChangeHandler = -> App.vent.trigger('rotate')

        $(window)
            .scroll(globals.scrollHandler)
            .resize(globals.resizeHandler)

    detachListeners: ->
        # detach global listeners
        globals = App._globals
        $(window)
            .unbind 'scroll', globals.scrollHandler
            .unbind 'resize', globals.resizeHandler

        if window.removeEventListener
            window.removeEventListener(
                'orientationchange', globals.orientationChangeHandler, false
            )

    onClose: ->
        @detachListeners()

    getItemView: (item) ->
        # Lookup the class to use based on the template specified on the item
        App.utils.findClass 'TileView',
            App.core.getModifiedTemplateName(item.get('type') or item.get('template'))

class MasonryFeedView extends FeedView

    default_options:
        isAnimated: Modernizr.csstransforms3d
        transitionDuration: '1.2s',
        isInitLayout: false,
        isResizeBound: false    # we are handling it ourselves
        visibleStyle:
            opacity: 1
            transform: 'scale(1)'
        hiddenStyle:
            opacity: 0
            transform: 'scale(0.001)'

    initialize: (options) ->
        super(arguments)
        # only care about the masonry options, parent class will care about rest
        @options = _.extend({}, @default_options, options.masonry)

        @recently_added = []

        App.vent.trigger 'layoutEngineInitialized', @, options
        App.layoutEngine = @ # this is the layout engine now-a-days
        @

    onRender: ->
        @layout()

    layout: () ->
        if not @masonry
            @setupMasonry()

        if not @img_load
            @img_load = imagesLoaded(@$el)
            @img_load.on 'always', (=> @imagesLoaded())

    setupMasonry: ->
        @options.columnWidth = $('.tile-sizer')[0]
        @masonry = new Masonry @$el[0], @options
        @masonry.bindResize()
        @masonry.layout()

    width: ->
        @masonry.columnWidth

    reload: ->
        if @masonry
            @masonry.reloadItems()
        @layout()
        @

    appendHtml: (view, itemview) ->
        @add(itemview.$el)

    add: ($fragment) ->
        @recently_added.push $fragment[0]
        @addItems()

    removeTiles: (tileViews) ->
        removeComplete = (masonry, removedItems) =>
            @collection.remove(_.map(tileViews, (view) -> view.model))
            @masonry.layout()
        @masonry.on 'removeComplete', removeComplete
        @masonry.remove(_.map(tileViews, (view) -> view.$el[0]))

    addItems: _.debounce (->
        recently_added = @recently_added
        @recently_added = []


        imageLoadedCallback = (=>
            @$el.append(recently_added)
            @masonry.appended recently_added
        )

        # need to wait for images to load on these items
        item_imagesloaded = imagesLoaded(recently_added)
        item_imagesloaded.on('always', imageLoadedCallback)
    ), 250, false

    imagesLoaded: _.debounce (->
        @masonry.layout()
    ), 500

    empty: ->
        if @masonry
            @masonry.destroy()
            @masonry = undefined
        @$el.html('')
        @layout()

module.exports = (module, App) ->
    @FeedView = FeedView
    @MasonryFeedView = MasonryFeedView