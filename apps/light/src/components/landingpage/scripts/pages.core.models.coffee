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


    class module.SimilarProduct extends module.Product
        ### 
        A SimilarProduct has tile-like attributes so that it can be mapped to tile templates
        ###
        initialize: (attributes, options) ->
            # Convert image json into objects
            imgInstances = _.map(@get("images"), (image) ->
                new module.Image($.extend(true, {}, image))
            ) or []
            defaultImage = imgInstances[0]
            @set
                images: imgInstances
                image: defaultImage
                defaultImage: defaultImage
                "tagged-products": []
                "dominant-color": defaultImage.get("dominant-color")
            return


    class module.ProductCollection extends Backbone.Collection
        model: module.Product


    class module.Tile extends Backbone.Model
        ###
        Attempt to retrieve tile and instantiate it as the correct Tile subclass,
        then execute success_cb or failure_cb
        @param tileId - <string>
        @param success_cb - <function> (<Tile>)
        @param failure_cb - <function>: ()
        ###
        # Cache of tile JSON index by tile-id's shared amongst all feeds
        # Currently only used by tiles inserted at page caching
        @tilecache = []
        @getTileById = (tileId, success_cb, failure_cb) ->
            if App.utils.isNumber(tileId)
                if App.option('debug', false)
                    console.warn('Router getting tile: '+tileId)

                # Check cache
                tileJson = @tilecache[tileId]
                if tileJson?
                    tile = @selectTileSubclass(tileJson)
                # Check current feed
                if not tile?
                    tile = if (App.discovery?.collection) then App.discovery.collection.tiles[tileId] else undefined
                if tile?
                    success_cb(tile)
                    return

                console.debug("Tile #{tileId} not found, fetching from IR")

                tile = new App.core.Tile(
                    'tile-id': tileId
                )
                tile.fetch().done(=>
                    tile = @selectTileSubclass(tile)
                    success_cb(tile)
                ).fail(failure_cb)
            else
                failure_cb()
            return

        ###
        Creates tile from tileJson or {Tile}, infering correct Tile subclass
        @param tile - {Tile}
        @returns {_*_Tile}
        ###
        @selectTileSubclass = (tile) ->
            if tile instanceof module.Tile
                TileClass = App.utils.findClass('Tile',
                    tile.get('type') || tile.get('template'), App.core.Tile)
                tile = tile.toJSON()
            else
                # assume tile is json
                TileClass = App.utils.findClass('Tile',
                    tile.type || tile.template, App.core.Tile)

            return new TileClass(TileClass.prototype.parse.call(this, tile))

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
            # Merge tagged-products (content tiles) & similar-products (product tiles)
            # Let view deal with the difference
            relatedProducts = @get("tagged-products") or []
            unless _.isEmpty(relatedProducts)
                relatedProducts = _.map(relatedProducts, (product) ->
                    originalImages = product.images or []
                    newImages = []
                    _.each(originalImages, (image) ->
                        imgObj = $.extend(true, {}, image)
                        newImages.push(new module.Image(imgObj))
                        return
                    )
                    product.images = newImages
                    return product
                )
            @set
                images: imgInstances
                image: defaultImage
                defaultImage: defaultImage
                "tagged-products": relatedProducts
                "dominant-color": defaultImage.get("dominant-color")

            App.vent.trigger("tileModelInitialized", @)
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
            return new module.Image(defImg)

        getDefaultImageId: ->
            try

                # product tiles
                if @get("default-image")
                    defaultImageAttr = @get("default-image")
                    delete @attributes['default-image']
                    return defaultImageAttr

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

        initialize: (attributes, options) ->

            # add a name, colour, and a sized url to each size datum
            self = this
            color = @get("dominant-color")

            # the template needs something simpler.
            @color = color
            if options and options["suppress_resize"]
                @url = @get("url")
            else
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
            super

    
    class module.Video extends Backbone.Model


    class module.YoutubeVideo extends module.Video
    

    ###
    automatically subclassed by TileCollection's model() method
    @type {Tile}
    ###
    class module.VideoTile extends module.Tile
        defaults:
            type: "video"


    ###
    A YoutubeTile is instantiated with a Youtube model json
    @type {Tile}
    ###
    class module.YoutubeTile extends module.VideoTile
        parse: (attrs, options) ->
            if attrs['original-id'] and not attrs["thumbnail"]
                attrs["thumbnail"] = "http://i.ytimg.com/vi/#{attrs["original-id"]}/hqdefault.jpg"
            super

        initialize: (attrs, options) ->
            @set(
                video: new module.YoutubeVideo(attrs)
            )
            super


    class module.HeroTile extends module.Tile
        type: "hero"

        parse: (attrs, options) ->
            # WARNING: this only allows 1 content of each type
            # ex: Video, Image
            for content in _.get(attrs, "contents", [])
                content["template"] = content.type
                attrs[content.type] = content
            super


    class module.HerovideoTile extends module.HeroTile
        parse: (attrs, options) ->
            for content in _.get(attrs, "contents", [])
                if content.type == "video" and content["original-id"] and not content["thumbnail"]
                    content["thumbnail"] = "http://i.ytimg.com/vi/#{content["original-id"]}/hqdefault.jpg"
                content["template"] = content.type
                attrs[content.type] = content
            super

        initialize: (attrs, options) ->
            desktopHeroImage = undefined
            mobileHeroImage = undefined
            if attrs.desktopHeroImage
                desktopHeroImage = new module.Image({ "url" : attrs.desktopHeroImage }, {"suppress_resize": true})
            if attrs.mobileHeroImage
                mobileHeroImage = new module.Image({ "url" : attrs.mobileHeroImage }, {"suppress_resize": true})

            @set(
                video: new module.YoutubeVideo(attrs['video'])
                image: desktopHeroImage
                images: [desktopHeroImage, mobileHeroImage]
                defaultImage: desktopHeroImage
            )
            App.vent.trigger("tileModelInitialized", @)


    ###
    Our TileCollection manages ALL the tiles on the page

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

        ###
        process common attributes, then delegate the collection's parsing
        method to their individual tiles.

        @param resp
        @param options
        @returns {Array}
        ###
        parse: (resp, options) ->
            tileIds = App.intentRank.getTileIds()

            respBuilder = _.filter(resp, (tile) =>
                if tile["tile-id"]
                    return true
                else
                    console.warn("Rejected tile during parse because it has no tile-id: #{tile}")
                    return false
            )
            tiles = _.map(respBuilder, (jsonEntry) ->
                TileClass = App.utils.findClass("Tile", jsonEntry.template or jsonEntry.type, module.Tile)
                return new TileClass(jsonEntry, parse: true)
            )
            return tiles

        ###
        Allows tiles to be fetched without options.

        @param options
        @returns {*}
        ###
        fetch: App.intentRank.fetch

        ###
        Interact with IR using the built-in Backbone handler

        @returns {Function|String}
        ###
        url: ->
            category = App.intentRank.currentCategory()
            url = "#{@config.apiUrl}/page/#{@config.campaign}/getresults?results=#{@config.results}"
            if category
                url += "&category=#{encodeURIComponent(category)}"
            return url

        initialize: (arrayOfData, url, campaign, results) ->
            @setup(url, campaign, results) # if necessary
            @tiles = {}
            @on("add", @itemAdded, @)
            App.vent.trigger("tileCollectionInitialized", @)
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
            compiledTemplate = _.template("<%=IRSource%>/page/<%=campaign%>/getresults?results=<%=IRResultsCount%>&category=<%=name%>")
            return compiledTemplate(_.extend({}, options: App.options, @attributes))


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
                                desktopHeroImage: subcat.desktopHeroImage or cat.attributes.desktopHeroImage
                                mobileHeroImage: subcat.mobileHeroImage or cat.attributes.mobileHeroImage
                                subCategory: subcat.name
                                category: cat
                        else
                            subMemo[subcat.name] = _.extend {}, subcat,
                                subCategory: subcat.name
                                category: cat
                        return subMemo
                    , {})
                return _.extend(memo, subCatMemo)

            @nameModelMap = _.reduce(@models, categoryFlattener, {})
        
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
            if not @nameModelMap?
                # This seems like a perfect piece of code to be in Model.initialization
                # except Backbone won't let you hook in *after* the Collection has been set up...
                @generateNameModelMap()
            return @nameModelMap[name]

        categoryExists: (category) ->
            return Boolean(@findModelByName(category))
