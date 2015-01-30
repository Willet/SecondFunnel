"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->

    class module.List

        model: Backbone.Model

        constructor: (models, options={}) ->
            _.extend(@, Backbone.Events)
            @model = options.model if options.model
            @initialize.apply @, arguments
            @length = 0
            @models = []
            @_byId = {}
            if models
                @add models, _.extend({silent: true}, options)

        initialize: ->
            # do nothing

        get: (obj) ->
            if obj is null
                return obj
            return @_byId[obj] || @_byId[obj.id] || @_byId[obj.cid]

        set: (models, options) ->
            # DEFER: this assumes it is always just an add operation
            options = _.defaults({}, options)
            if options.parse
                models = @parse models, options
            @add(models, options)

        parse: (resp, options) ->
            return resp

        add: (models, options) ->
            if singular = not _.isArray(models)
                if models
                    models = [models]
                else
                    models = []
            at = options["at"] || 0
            newModels = _.map models, (attrs) =>
                if attrs instanceof Backbone.Model
                    attrs
                else if _.isFunction(@model)
                    @model(attrs)
                else
                    new @model(attrs)
            @models[at..0] = newModels
            if not options.silent
                _.each newModels, (model) =>
                    @trigger 'add', model, @, options
                @trigger 'add:many', newModels, @, options
            _.each newModels, (model) =>
                @_addReference model

        remove: (models, options={}) ->
            if singular = not _.isArray(models)
                if models
                    models = [models]
                else
                    models = []
            for model in models
                t = _.indexOf(@models, model)
                if t > -1
                    @models[t..t] = []
                    @length = @length - 1
                    if not options.silent
                        @trigger 'remove', model, @, options
                    @_removeReference model, options
            if singular
                return models[0]
            return models

        reset: (models, options) ->
            _.each @models, (model) ->
                @_removeReference(model, options)
            options.previousModels = @models
            @_reset()
            models = @add models, _.extend({silent: true}, options)
            if not options.silent
                @trigger 'reset', @, options
            return models

        push: (model, options) ->
            @add model, _.extend({at: @length}, options)
            return model

        pop: (options) ->
            model = @at(@length - 1)
            @remove model, options
            return model

        unshift: (model, options) ->
            @add model, options
            return model

        shift: (options) ->
            model = @at 0
            @remove model
            return model

        at: (index) ->
            return @models[index]

        _addReference: (model, options) ->
            if not model.collection
                model.collection = @
            @_byId[model.cid] = model
            @_byId[model.id] = model
            model.on('all', @_onModelEvent, @)

        _removeReference: (model, options) ->
            if model.collection is @
                delete model.collection
            delete @_byId[model.cid]
            delete @_byId[model.id]
            model.off('all', @_onModelEvent, @)

        _onModelEvent: (event, model, collection, options) ->
            if (event is 'add' or event is 'remove') and collection isnt @
                return
            if (event is 'destroy')
                @remove(model, options)
            @trigger.apply(@, arguments)

        _reset: () ->
            @length = 0
            @models = []

    underscore_methods = ['forEach', 'each', 'map', 'collect', 'reduce', 'foldl',
        'inject', 'reduceRight', 'foldr', 'find', 'detect', 'filter', 'select',
        'reject', 'every', 'all', 'some', 'any', 'include', 'contains', 'invoke',
        'max', 'min', 'toArray', 'size', 'first', 'head', 'take', 'initial', 'rest',
        'tail', 'drop', 'last', 'without', 'difference', 'indexOf', 'shuffle',
        'lastIndexOf', 'isEmpty', 'chain', 'sample']

    _.each underscore_methods, (method) ->
        module.List.prototype[method] = () ->
            args = [].slice(arguments) # convert to regular array
            args.unshift(@models)
            return _[method].apply(_, args)


    class module.Store extends Backbone.Model
        defaults:
            id: "0"
            name: "Store"
            displayName: ""

        initialize: (data) ->
            unless data
                throw new Error("Missing data")
            unless data.slug
                throw new Error("Missing store slug")
            unless data.displayName
                @set "displayName", @get("name")
            return


    class module.Product extends Backbone.Model


    class module.Tile extends Backbone.Model
        ###
        Attempt to retrieve tile and instantiate it as the correct Tile subclass,
        then execute success_cb or failure_cb
        @param tileId - <string>
        @param success_cb - <function> (<Tile>)
        @param failure_cb - <function>: ()
        ###
        @getTileById = (tileId, success_cb, failure_cb) ->
            isNumber = /^\d+$/.test(tileId);

            if isNumber
                if App.option('debug', false)
                    console.warn('Router getting tile: '+tileId)

                # Check cache
                tileJson = if (App.discovery and App.discovery.tilecache) then App.discovery.tilecache[tileId] else undefined
                if tileJson?
                    tile = @createTile(tileJson)
                # Check current feed
                if not tile?
                    tile = if (App.discovery and App.discovery.collection) then App.discovery.collection.tiles[tileId] else undefined
                if tile?
                    success_cb(tile)
                    return

                console.debug('tile not found, fetching from IR.')

                tile = new App.core.Tile(
                    'tile-id': tileId
                )
                tile.fetch().done(->
                    tile = @selectTileSubclass(tile)
                    success_cb(tile)
                ).fail(failure_cb)
            else
                failure_cb()
            return

        ###
        Creates tile from tileJson, infering correct Tile subclass
        @param tileJson - object literal of tile data
        @return {Tile} or {_*_Tile}
        ###
        @createTile = (tileJson) ->
            tile = new App.core.Tile(tileJson)
            return @selectTileSubclass(tile)

        ###
        Converts a Tile into its correct subclass
        @param tile - {Tile}
        @returns {_*_Tile}
        ###
        @selectTileSubclass = (tile) ->
            TileClass = App.utils.findClass('Tile',
                tile.get('type') || tile.get('template'), App.core.Tile)
            return new TileClass(TileClass.prototype.parse.call(this, tile.toJSON()))

        defaults:
            # Default product tile settings, some tiles don't
            # come specifying a type or caption
            caption: ""
            description: ""
            "tile-id": 0
            "tagged-products": []
            "dominant-color": "transparent"

        parse: (resp, options) ->
            unless resp.type
                resp.type = resp.template
            resp.caption = App.utils.safeString(resp.caption or "")

            # https://therealwillet.hipchat.com/history/room/115122#17:48:02
            if App.option('ad:forceTwoColumns', false)
                resp.orientation = 'portrait'

            resp

        initialize: (attributes, options) ->

            # turn image json into image objects for easier access.
            defaultImage = undefined
            imgInstances = undefined
            relatedProducts = undefined

            # replace all image json with their objects.
            imgInstances = _.map(@get("images"), (image) ->
                new module.Image($.extend(true, {}, image))
            ) or []

            # this tile has no images, or can be an image itself
            if imgInstances.length is 0
                imgInstances.push new module.Image(
                    "dominant-color": @get("dominant-color")
                    url: @get("url")
                )
            defaultImage = @getDefaultImage()

            # Transform related-product image, if necessary
            relatedProducts = @get("tagged-products")
            unless _.isEmpty(relatedProducts)
                relatedProducts = _.map(relatedProducts, (product) ->
                    originalImages = product.images or []
                    newImages = []
                    _.each originalImages, (image) ->
                        imgObj = $.extend(true, {}, image)
                        newImages.push new module.Image(imgObj)
                        return

                    product.images = newImages
                    product
                )
            @set
                images: imgInstances
                image: defaultImage
                defaultImage: defaultImage
                "tagged-products": relatedProducts
                "dominant-color": defaultImage.get("dominant-color")

            App.vent.trigger "tileModelInitialized", this
            return

        ###
        @param byImgId     if omitted, the default image id
        @returns {module.Image}
        ###
        getImage: (byImgId) ->
            imgId = parseInt(byImgId or @getDefaultImageId(), 10)
            defImg = undefined

            # find default image for image-child tiles (e.g. product tile)
            defImg = _.findWhere(@get("images"),
                id: imgId

            # find default image for image-root tiles
            ) or _.findWhere(@get("images"),
                "tile-id": imgId
            )
            unless defImg
                try
                    if @get("images")[0] instanceof module.Image
                        return @get("images")[0]
                    return new module.Image(@get("images")[0])
                catch err

                    # if all fails, this is most likely a lifestyle image
                    return new module.Image(
                        "dominant-color": @get("dominant-color")
                        url: @get("url")
                    )
            # found default image
            # timing: attributes.images already coverted to Images
            else if defImg instanceof module.Image
                return defImg
            new module.Image(defImg)

        getDefaultImageId: ->
            try

                # product tiles
                if @get("default-image")
                    return @get("default-image")

                # product tiles without a default-image attr, guess it
                if @get("images") and @get("images").length

                    # product tiles (or tiles with images:[...])

                    # just going to try everything
                    guess = @get("images")[0]["tile-id"] or
                        @get("images")[0].get("tile-id") or
                        @get("images")[0].id or
                        @get("images")[0].get("id")
                if guess
                    return guess

                # image tiles (or tiles that are root-level images)
                # note: might be wrong if product tiles still fall through
                return @get("tile-id").toString()
            catch e # no images
                console.warn "This object does not have a default image.", this
                return undefined
            return

        ###
        Get the tile's default image as an object.
        @returns {Image|undefined}
        ###
        getDefaultImage: ->
            @getImage()

        url: ->
            App.options.IRSource + "/page/" + App.options.campaign + "/tile/" + @get("tile-id")

        sync: (method, model, options) ->
            method = "read" # Must always be read only
            Backbone.sync method, model, options


    ###
    The Image object (url, width, height, ...)

    @constructor
    @type {*}
    ###
    class module.Image extends Backbone.Model
        defaults:
            url: "http://placehold.it/2048&text=blank"
            "dominant-color": "transparent"

        initialize: ->

            # add a name, colour, and a sized url to each size datum
            self = this
            color = @get("dominant-color")

            # the template needs something simpler.
            @color = color
            @url = @width(App.feed.width())
            return

        sync: ->
            false


        ###
        @param width                     in px; 0 means no width restrictions
        @param height                    in px; 0 means no height restrictions
        @param {boolean} obj     whether the complete object or the url
        will be returned
        @returns {*}
        ###
        dimens: (width, height, obj) ->
            options = $.extend({}, obj)
            resized = $.extend({}, @defaults, @attributes)
            if width > 0
                options.width = width
            if height > 0
                options.height = height
            unless width or height
                options.width = App.feed.width()
            resized.url = App.utils.getResizedImage(@get("url"), options)
            if obj
                return resized
            resized.url

        width: (width, obj) ->
            # get url by min width
            @dimens width, 0, obj

        height: (height, obj) ->
            # get url by min height
            @dimens 0, height, obj


    ###
    An ImageTile    *is* an image JSON, so we need to allocate all of its
    attributes inside an 'images' field.

    @param resp
    @param options
    @returns {*}
    ###
    class module.ImageTile extends module.Tile
        parse: (resp, options) ->
            # create tile-like attributes
            resp["default-image"] = 0

            # image tile contains image:[one copy of itself]
            resp.images = [$.extend(true, {}, resp)]
            return resp


    class module.GifTile extends module.ImageTile
        parse: (resp, options) ->
            # images field will contain gif object as JSON
            super(resp, options)


    ###
    automatically subclassed by TileCollection's model() method
    @type {Tile}
    ###
    class module.VideoTile extends module.Tile
        defaults:
            type: "video"


    class module.YoutubeTile extends module.VideoTile
        defaults:
            type: "video"

        parse: (json) ->
            attrs = json
            if attrs['original-id'] and not attrs["thumbnail"]
                attrs["thumbnail"] = "http://i.ytimg.com/vi/#{attrs["original-id"]}/hqdefault.jpg"
            attrs


    ###
    Our TileCollection manages ALL the tiles on the page.
    This is essentially IntentRank.

    @constructor
    @type {Collection}
    ###
    class module.TileCollection extends module.List

        ###
        Subclass each tile JSON into their specific containers.
        @param item            model attributes
        @returns {Tile}     or an extension of it
        ###
        model: (item) ->
            TileClass = App.utils.findClass("Tile", item.type or item.template, module.Tile)
            new TileClass(item)

        config: {}
        loading: false

        # {[tileId: maxShow,]}
        # if tileId is in initial results and you want it shown only once,
        # set maxShow to 0.
        # TILES THAT LOOK THE SAME FOR TWO PAGES CAN HAVE DIFFERENT TILE IDS
        resultsThreshold: App.option("resultsThreshold", {})

        ###
        reorder landscape tiles to only appear after a multiple-of-2
        products has appeared, allowing gapless layouts in two-col ads.

        this method requires state to be maintained in the tempTiles variable;
        it is not idempotent.

        TODO: this belongs to the layout engine.

        @param {object} resp an array of tile json
        @returns {object} an array of tile json
        ###
        reorderTiles: (resp) ->
            if @currentNonFilledRows is undefined
                @currentNonFilledRows = []
            columnCount = 2 # the number of columns (should get from masonry...)
            respBuilder = [] # new resp after filter(s)

            orientation_column_widths = { # column(s) wide
                "portrait": 1
                "landscape": 2
            }

            # default to portrait
            _.each resp, (tile) ->
                unless tile.orientation
                    tile.orientation = "portrait"

            # only do this for iframe versions
            #unless App.utils.isIframe()
            #    return resp

            _.each resp, (tile) =>
                tileAdded = false
                tileColWidth = orientation_column_widths[tile.orientation]

                # tile is an entire row, can just add it right away
                if tileColWidth == columnCount
                    respBuilder.push(tile)
                    return

                # check existing non-filled rows
                @currentNonFilledRows = _.filter @currentNonFilledRows, (row) ->
                    return true if tileAdded
                    rowColWidth = _.reduce(row, ((memo, tile) -> memo + orientation_column_widths[tile.orientation]), 0)
                    if rowColWidth + tileColWidth <= columnCount
                        # fits in the row, add it to the row
                        row.push tile

                    if rowColWidth + tileColWidth == columnCount
                        # row is now full, "remove" from nonfilled rows and add it to response
                        _.each(row, (tile) -> respBuilder.push(tile))
                        tileAdded = true
                        return false # filter it out
                    return true # let the row remain

                unless tileAdded
                    # couldn't find place for tile, add as a new row
                    newRow = [tile]
                    @currentNonFilledRows.push(newRow)
            respBuilder


        ###
        process common attributes, then delegate the collection's parsing
        method to their individual tiles.

        @param resp
        @param options
        @returns {Array}
        ###
        parse: (resp, options) ->

            # this = the instance
            tileIds = App.intentRank.getTileIds()

            # reorder landscape tiles to only appear after a multiple-of-2
            # products has appeared, allowing gapless layouts in two-col ads.
            resp = @reorderTiles(resp)

            respBuilder = []
            i = 0
            _.each(resp, (tile) =>
                tileId = tile["tile-id"]
                unless tileId # is this a tile???
                    console.warn("WAS NOT A TILE", tile)
                    return

                # decrement the allowed displays of each shown tile.

                # tile has been disabled by its per-page threshold
                if @resultsThreshold[tileId] isnt undefined and --@resultsThreshold[tileId] < 0
                    return

                # if algorithm is finite but a dupe is about to occur,
                # issue a warning but display anyway
                if App.option("IRAlgo", "generic").indexOf("finite") > -1
                    if _.indexOf(tileIds, tileId) > -1
                        console.warn "Tile " + tileId + " is already on the page!"
                        unless App.option("allowTileRepeats", false)
                            return
                respBuilder.push tile # this tile passes
            )
            tiles = _.map respBuilder, (jsonEntry) ->
                TileClass = App.utils.findClass("Tile", jsonEntry.template or jsonEntry.type, module.Tile)
                new TileClass(jsonEntry, parse: true)
            tiles



        ###
        Allows tiles to be fetched without options.

        @param options
        @returns {*}
        ###
        fetch: App.intentRank.fetch

        ###
        Interact with IR using the built-in Backbone thingy.

        @returns {Function|String}
        ###
        url: ->
            url = undefined
            category = App.intentRank.currentCategory()
            url = "#{@config.apiUrl}/page/#{@config.campaign}/getresults?results=#{@config.results}"
            if category
                return url + "&category=" + encodeURIComponent(category)
            url

        initialize: (arrayOfData, url, campaign, results) ->
            @setup url, campaign, results # if necessary
            @tiles = {}
            @on "add", @itemAdded, @
            App.vent.trigger "tileCollectionInitialized", @
            return


        ###
        Adds a reference to the tile in a hashmap of tiles.    Useful for
        getting the tile if you only know the real tile id.

        @param tile {Object}
        @param collection {Object}
        @param options {Object}
        ###
        itemAdded: (tile, collection, options) ->
            id = tile.get("tile-id")
            @tiles[id] = tile
            return


        ###
        (Re)configure this object to fetch from an Intent Rank URL.

        @param apiUrl
        @param campaign
        @param results
        ###
        setup: (apiUrl, campaign, results) ->

            # apply new parameters, or default to existing ones
            @config.apiUrl = apiUrl or App.option("IRSource") or @config.apiUrl
            @config.campaign = campaign or App.option("campaign") or @config.campaign
            @config.results = results or App.option("IRResultsCount") or @config.results
            return

    ###
    Categories are used to filter results from IR.

    @constructor
    @type {Model}
    ###
    class module.Category extends Backbone.Model
        url: ->
            _.template "<%=IRSource%>/page/<%=campaign%>/getresults?results=<%=IRResultsCount%>&category=<%=name%>", _.extend({}, App.options, @attributes)

    ###
    Container for categories, does nothing for now.

    @constructor
    @type {Collection}
    ###
    class module.CategoryCollection extends Backbone.Collection
        model: module.Category

        initialize: ->
            @listenTo(@, 'add, remove, reset', _.debounce(@generateNameModelMap, 100))
        
        ###
        construct a lookup table based on model name
        {
          'for-her':          { category: <Category>, ... cat.attributes properties },
          'for-him':          { category: <Category>, subCategory: 'for-him', ... subCategory properties },
          'for-him|under-10': { category: <Category>, ... cat.attributes properties },
          'for-her|under-20': { category: <Category>, subCategory: '|under-20', ... subCategory properties }
        }
        ###
        generateNameModelMap: ->
            categoryFlattener = (memo, cat) ->
                # Add category first, will be overwritten by any subcategory with same name
                memo[cat.attributes.name] = _.extend {}, cat.attributes,
                    category: cat
                subCatMemo = _.reduce(cat.attributes.subCategories, (subMemo, subcat) ->
                        if subcat.name.charAt(0) == '|'
                            subMemo[cat.attributes.name + subcat.name] = _.extend {}, subcat,
                                subCategory: subcat.name
                                category: cat
                        else
                            subMemo[subcat.name] = _.extend {}, subcat,
                                subCategory: subcat.name
                                category: cat
                        return subMemo
                    , {})
                return _.extend memo, subCatMemo

            @nameModelMap = _.reduce @models, categoryFlattener, {}
        
        ###
        Names can be a simple category ('for-her') or complex category ('for-her|under-20')
        Categories can be a:
          - self-contained simple category or subcategory ('for-her')
          - self-contained complex category or sub-category ('for-her|under-20')
          - filter sub-category ('|under-20'), acts upon its parent category (ie: 'for-her')
            to become ('for-her|under-20')
        Note: filters can be arbitrarily chained
        ###
        findModelByName: (name) ->
            if not @nameModelMap
                # This seems like a perfect piece of code to be in Model.initialization
                # except Backbone won't let you hook in *after* the Collection has been set up...
                @generateNameModelMap()
            return @nameModelMap[name]

        categoryExists: (category) ->
            return Boolean(@findModelByName(category))
