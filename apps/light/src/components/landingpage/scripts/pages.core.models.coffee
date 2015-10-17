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
                @add(models, _.extend({silent: true}, options))

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
                models = @parse(models, options)
            @add(models, options)

        parse: (resp, options) ->
            return resp

        add: (models, options) ->
            singular = not _.isArray(models)
            if singular
                models = if models then [models] else []
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
                _.each(newModels, (model) => @trigger('add', model, @, options))
                @trigger('add:many', newModels, @, options)
            _.each(newModels, (model) => @_addReference(model))

        remove: (models, options={}) ->
            singular = not _.isArray(models)
            if singular
                models = if models then [models] else []
            for model in models
                t = _.indexOf(@models, model)
                if t > -1
                    @models[t..t] = []
                    @length = @length - 1
                    if not options.silent
                        @trigger('remove', model, @, options)
                    @_removeReference(model, options)
            
            return (if singular then models[0] else models)

        reset: (models, options) ->
            _.each(@models, (model) -> @_removeReference(model, options))
            options.previousModels = @models
            @_reset()
            models = @add(models, _.extend({silent: true}, options))
            if not options.silent
                @trigger('reset', @, options)
            return models

        push: (model, options) ->
            @add(model, _.extend({at: @length}, options))
            return model

        pop: (options) ->
            model = @at(@length - 1)
            @remove(model, options)
            return model

        unshift: (model, options) ->
            @add(model, options)
            return model

        shift: (options) ->
            model = @at 0
            @remove(model)
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

    _.each(underscore_methods, (method) ->
        module.List.prototype[method] = () ->
            args = [].slice(arguments) # convert to regular array
            args.unshift(@models)
            return _[method].apply(_, args)
    )


    class module.Store extends Backbone.Model
        type: "Store"
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
                @set("displayName", @get("name"))
            return


    class module.Product extends Backbone.Model
        type: "Product"

        initialize: (attributes, options) ->
            # Turn images into Image's
            images =
                if @get("images")?.length \
                then (new module.Image($.extend(true, {}, image)) for image in @get("images")) \
                else []
            taggedProducts =
                if _.isArray(@get('tagged-products')) \
                then (new module.Product(p) for p in @get('tagged-products')) \
                else []
            # defaultImage shares some object as images[0] for image caching (urls)
            defaultImage = images[0]
            @set
                images: images
                defaultImage: defaultImage
                taggedProducts: taggedProducts
                "dominant-color": defaultImage.get("dominant-color")
            @unset('default-image')
            @unset('tagged-products')
            return


    class module.ProductCollection extends Backbone.Collection
        type: "ProductCollection"
        model: module.Product


    ###
    The Image object (url, width, height, ...)

    @constructor
    @type {*}
    ###
    class module.Image extends Backbone.Model
        type: "Image"
        defaults:
            url: "http://placehold.it/2048&text=blank"
            "dominant-color": "transparent"

        initialize: (attributes, options) ->
            @color = @get("dominant-color")
            # sizes cloudinary url
            @url = if options? and options["suppressResize"] \
                   then @get("url") \
                   else @width(App.feed.width())
            return

        sync: ->
            false

        width: (width, returnInstance=false) ->
            # get url by minimum width
            # See resizeForDimens for documentation
            @resizeForDimens(width, 0, returnInstance)

        height: (height, returnInstance=false) ->
            # get url by minimum height
            # See resizeForDimens for documentation
            @resizeForDimens(0, height, returnInstance)

        ###
        @param width - in px; 0 means no width restrictions
        @param height - in px; 0 means no height restrictions
        @param {boolean} returnInstance - whether the complete object or the url
        will be returned
        @returns {*}
        ###
        resizeForDimens: (width, height, returnInstance=false) ->
            options = {}
            resized = $.extend({}, @defaults, @attributes)
            if width > 0
                options.width = width
            if height > 0
                options.height = height
            unless width or height
                # App.feed.width is a generic width that doesn't
                # correspond to an image actually displayed
                # (tile image width is slightly smaller to account for tile border)
                options.width = App.feed.width()

            # first check if the resized url exists in sizes
            size = @_lookForSize(options)

            # second check for resized url with the rounded size
            if not size?
                options = @_roundSizes(options)
                size = @_lookForSize(options)
                        
            resized.url = if size?.url? \
                          then size.url \
                          # third generate it from cloudinary url
                          else @resizeCloudinaryImage(@get("url"), options)

            if returnInstance
                # Create a new instance of (Image or a subclass)
                return new module[@type](resized, suppressResize: true)
            else
                return resized.url

        _updateUrl: (options, url) ->
            # Update url if this image url is bigger than the current one
            ...

        _lookForSize: (options) ->
            # Check attributes.sizes if we have image url's specified for this size
            if options.width?
                return _.findWhere(_.values(@attributes['sizes']), width: options.width)
            else 
                return _.findWhere(_.values(@attributes['sizes']), height: options.height)

        _roundSizes: (options, width, height) ->
            ###
            Round to the nearest whole hundred pixel dimension
            prevents creating a ridiculous number of images.

            options: width, height
            width: (optional) width to round
            height: (optional) height to round
            ###
            width = width or options.width
            height = height or options.height
            ratio = Math.ceil(window.devicePixelRatio * 2) / 2

            if options.width? and options.height?
                options.width = Math.ceil(width / 100.0) * (100 * ratio)
                options.height = Math.ceil(height / 100.0) * (100 * ratio)
            else if options.height?
                options.height = Math.ceil(height / 100.0) * (100 * ratio)
            else if App.feed.width() > 0 and not options.width?
                options.width = Math.ceil(App.feed.width()) * ratio
            else
                options.width = Math.ceil(width / 100.0) * (100 * ratio)
            return options


        resizeCloudinaryImage: (url, options) ->
            ###
            Class method which resizes a Cloudinary url

            url - a cloudinary url

            options:
                originalSize: boolean return original url
                width: width to use (given priority over height)
                height: height to use

            returns: resized url
            ###
            if _.contains(url, ".gif")
                # Do NOT transform animated gifs
                return url

            if _.contains(url, "c_fit")
                # Transformation has been applied to this url, Cloudinary is not smart
                # with these, so strip back to original url
                url = url.replace(/(\/c_fit[,_a-zA-Z0-9]+\/v.+?\/)/, '/')

            if options.originalSize
                # return cleaned url
                return url
            
            width = Math.max(options.width || 300, App.option('minImageWidth'))
            height = Math.max(options.height || 300, App.option('minImageHeight'))

            # Round to 100px increments to avoid 
            options = @_roundSizes(options, width, height)

            options =
                crop: 'fit'
                quality: 75
                width: options.width
                height: options.height

            url = url.replace(App.CLOUDINARY_DOMAIN, '') #remove absolute uri
            url = $.cloudinary.url(url, options)
            return url


    class module.Video extends Backbone.Model
        type: "Video"


    class module.YoutubeVideo extends module.Video
        type: "YoutubeVideo"
        
        initialize: (attributes, options) ->
            if attributes['original-id'] and not attributes["thumbnail"]
                @set(
                    thumbnail: "http://i.ytimg.com/vi/#{attributes["original-id"]}/hqdefault.jpg"
                )
            super


    class module.Tile extends Backbone.Model
        type: "Tile"
        ###
        Attempt to retrieve tile and instantiate it as the correct Tile subclass,
        then execute success_cb or failure_cb
        @param tileId - <string>
        @param success_cb - <function> (<Tile>)
        @param failure_cb - <function>: ()
        ###
        # Cache of tile JSON index by tile-id's shared amongst all feeds
        # Currently only used by tiles inserted at page caching
        @tilecache: []
        @getTileById: (tileId, success_cb, failure_cb) ->
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
        @selectTileSubclass: (tile) ->
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
            "dominant-color": "transparent"

        parse: (resp, options) ->
            unless resp.type
                resp.type = resp.template
            resp.caption = App.utils.safeString(resp.caption or "")

            # https://therealwillet.hipchat.com/history/room/115122#17:48:02
            if App.option('ad:forceTwoColumns', false)
                resp.orientation = 'portrait'

            return resp

        initialize: (attributes, options) ->
            ###
            When tile initialization is finished, it is expected that:
            a) product and tagged products are converted to <Product>s,
            b) images, default image and tagged products default image are converted
            to <Image>s.
            ###
            if App.support.mobile() and @mobileOptions?
                # update options on mobile
                @options = _.extend({}, @options, @mobileOptions)

            # Instantiate images first, because we will try to re-use these image models
            # so that image size caching is maximally used.
            if _.isArray(@get("images"))
                @set(images: (new module.Image(im) for im in @get("images") when not _.isEmpty(im)))

            if @get("image")? and not _.isEmpty(@get('image'))
                @set(image: @getOrCreate(@get("image")))

            if @get('product')? and not _.isEmpty(@get('product'))
                @set(product: new module.Product(@get('product')))

            if _.isArray(@get('tagged-products'))
                @set(taggedProducts: (new module.Product(p) for p in @get('tagged-products') when not _.isEmpty(p)))
                @unset('tagged-products')

            if @get('default-image')? and not _.isEmpty(@get('default-image'))
                # getImage uses images, so set first
                defaultImage = @getOrCreateImage(@get('default-image'))
                @set(
                    defaultImage: defaultImage
                    'dominant-color': defaultImage.get('dominant-color')
                )
                @unset('default-image')

            if @get('video')? and not _.isEmpty(@get('video'))
                video = if (@get('video')['source'] == 'youtube') \
                        then new module.YoutubeVideo(@get('video')) \
                        else new module.Video(@get('video'))
                @set(video: video)
            
            App.vent.trigger("tileModelInitialized", @)
            return

        ###
        @param byImgId
        @returns {module.Image}
        ###
        getImage: (imgId) ->
            # returns undefined if @get("images") is undefined
            return _.findWhere(
                @get("images"),
                id: imgId
            )

        ###
        Attempt to find the same image by id before creating a new one
        Helps with caching images

        @param imgObj - either (Number) image ID or (Object) image attributes
        @returns {module.Image} 
        ###
        getOrCreateImage: (imgObj) ->
            if _.isNumber(imgObj)
                # Number is an id in images
                image = @getImage(imgObj)
            else
                # Try to find image before generating a new model
                image = @getImage(imgObj.id) or new module.Image(imgObj)
            return image

        url: ->
            App.options.IRSource + "/page/" + App.options.campaign + "/tile/" + @get("tile-id")

        sync: (method, model, options) ->
            method = "read" # Must always be read only
            Backbone.sync method, model, options


    ###
    Tile's are automatically subclassed by TileCollection's model() method
    ###

    class module.ProductTile extends module.Tile
        type: "ProductTile"


    class module.ImageTile extends module.Tile
        type: "ImageTile"


    class module.GifTile extends module.ImageTile
        type: "GifTile"


    class module.CollectionTile extends module.Tile
        # Similar to Image Tile, but has mini-feed of products
        type: "CollectionTile"
        options:
            showThumbnails: false
            previewFeed: true
        initialize: ->
            super
            # A CollectionTile pop-up supports a different image than the tile view
            if @get("expandedImage")?
                image = if _.isNumber(@get('expandedImage')) \
                        then @getImage(@get('expandedImage')) \
                        else new module.Image(@get('expandedImage'))
                @set(expandedImage: image)
            if @get("expandedMobileImage")?
                image = if _.isNumber(@get('expandedMobileImage')) \
                        then @getImage(@get('expandedMobileImage')) \
                        else new module.Image(@get('expandedMobileImage'))
                @set(expandedMobileImage: image)
            # Used to create a `back to collection description` link
            collectionName = @get('name') or @get('title')
            for product in @get('taggedProducts')
                product.set("collectionName", collectionName)


    class module.VideoTile extends module.Tile
        type: "VideoTile"


    class module.YoutubeTile extends module.VideoTile
        type: "YoutubeTile"


    class module.HeroTile extends module.Tile
        type: "HeroTile"


    class module.HerovideoTile extends module.HeroTile
        type: "HerovideoTile"
        initialize: (attrs, options) ->
            super
            desktopHeroImage = undefined
            mobileHeroImage = undefined
            if attrs.desktopHeroImage
                desktopHeroImage = new module.Image(
                    url: attrs.desktopHeroImage
                    suppressResize: true
                )
            if attrs.mobileHeroImage
                mobileHeroImage = new module.Image(
                    url: attrs.mobileHeroImage
                    suppressResize: true
                )

            if desktopHeroImage
                @set(
                    image: desktopHeroImage
                    images: [desktopHeroImage, (mobileHeroImage or desktopHeroImage)]
                    defaultImage: desktopHeroImage
                )
            App.vent.trigger("tileModelInitialized", @)


    ###
    Our TileCollection manages ALL the tiles on the page

    @constructor
    @type {Collection}
    ###
    class module.TileCollection extends module.List
        type: "TileCollection"
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
        Process tileJSON's into tiles if they are valid. If invalid, warn and discard.

        @param resp - a list of tile's in json
        @param options
        @returns {Array}
        ###
        parse: (resp, options) ->
            reduceToTiles = (memo, tileJson) ->
                if not tileJson["tile-id"]
                    console.warn("Rejected tile during parse because it has no tile-id: %O", tile)
                else
                    try
                        TileClass = App.utils.findClass("Tile", tileJson.template or tileJson.type, module.Tile)
                        tile = new TileClass(tileJson, parse: true)
                        memo.push(tile) # everything worked, let tile through
                    catch e
                        console.warn("Rejecting tile that threw error (%s: %s) during initialization: %O",
                                     e.name, e.message, tile)
                return memo

            tiles = _.reduce(resp, reduceToTiles, [])
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
        type: "Category"
        url: ->
            compiledTemplate = _.template("<%=IRSource%>/page/<%=campaign%>/getresults?results=<%=IRResultsCount%>&category=<%=name%>")
            return compiledTemplate(_.extend({}, options: App.options, @attributes))


    ###
    Container for categories.

    @constructor
    @type {Collection}
    ###
    class module.CategoryCollection extends Backbone.Collection
        type: "CategoryCollection"
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
                memo[cat.attributes.name] = _.extend({}, cat.attributes,
                    category: cat
                )
                subCatMemo = _.reduce(cat.attributes.subCategories, (subMemo, subcat) ->
                        # If subcat doesn't have a name attribute, just ignore it
                        if subcat.name
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
