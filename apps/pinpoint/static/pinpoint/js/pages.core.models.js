/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _, console, App */
/**
 * @module core
 */
App.module('core', function (core, App) {
    // other args: https://github.com/marionettejs/Marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document);


    /**
     * Object store for information about a particular store
     *
     * @constructor
     * @type {Model}
     */
    this.Store = Backbone.Model.extend({
        'defaults': {
            'id': '0',
            'name': 'Store',
            'displayName': ''
        },
        'initialize': function (data) {
            if (!data.slug) {
                throw "Missing store slug";
            }
            if (!data.displayName) {
                this.set('displayName', this.get('name'));
            }
        }
    });

    /**
     * Object store for information about a particular database product,
     * its contents, or its media.
     *
     * @constructor
     * @type {Model}
     */
    this.Tile = Backbone.Model.extend({
        'defaults': {
            // Default product tile settings, some tiles don't
            // come specifying a type or caption
            'caption': "",
            'description': '',
            'tile-id': 0,
            // 'tile-class': 'tile',  // what used tile-class?
            // 'content-type': ''  // where did content-type go?
            'related-products': [],
            'dominant-color': "transparent"
        },

        'parse': function (resp, options) {
            if (!resp.type) {
                resp.type = resp.template;
            }
            resp.caption = App.utils.safeString(resp.caption || '');

            return resp;
        },

        'initialize': function (attributes, options) {
            // turn image json into image objects for easier access.
            var self = this,
                defaultImage,
                imgInstances = [],
                relatedProducts;

            // replace all image json with their objects.
            _.each(this.get('images'), function (image) {
                var localImageVariable;
                if (typeof image === 'string') {
                    // Patch old IR responses.
                    // TODO: Do we still need this?
                    localImageVariable = {
                        'format': "jpg",
                        'dominant-color': "transparent",
                        'url': image,
                        'id': self.getDefaultImageId() || 0
                    };
                } else { // make a copy
                    localImageVariable = $.extend(true, {}, image);
                }
                imgInstances.push(new core.Image(localImageVariable));
            });

            // this tile has no images, or can be an image itself
            if (imgInstances.length === 0) {
                imgInstances.push(new core.Image({
                    'dominant-color': this.get('dominant-color'),
                    'url': this.get('url')
                }));
            }

            defaultImage = imgInstances[0];

            // Transform related-product image, if necessary
            relatedProducts = this.get('related-products');
            if(!_.isEmpty(relatedProducts)) {
                relatedProducts = _.map(relatedProducts, function(product) {
                    var originalImages = product.images || [];
                    var newImages = [];
                    _.each(originalImages, function(image) {
                        var imgObj = $.extend(true, {}, image);
                        newImages.push(new core.Image(imgObj));
                    });
                    product.images = newImages;
                    return product;
                });
            }

            this.set({
                'images': imgInstances,
                'defaultImage': defaultImage,
                'related-products': relatedProducts,
                'dominant-color': defaultImage.get('dominant-color')
            });

            App.vent.trigger('tileModelInitialized', this);
        },

        /**
         *
         * @param byImgId   if omitted, the default image id
         * @returns {core.Image}
         */
        'getImage': function (byImgId) {
            var imgId = parseInt(byImgId || this.getDefaultImageId(), 10),
                defImg;

            defImg =
                // find default image for image-child tiles (e.g. product tile)
                _.findWhere(this.get('images'), {
                    'id': imgId
                }) ||
                // find default image for image-root tiles
                _.findWhere(this.get('images'), {
                    'tile-id': imgId
                });

            if (!defImg) {
                try {
                    if (this.get('images')[0] instanceof core.Image) {
                        return this.get('images')[0];
                    }
                    return new core.Image(this.get('images')[0]);
                } catch (err) {
                    // if all fails, this is most likely a lifestyle image
                    return new core.Image({
                        'dominant-color': this.get('dominant-color'),
                        'url': this.get('url')
                    });
                }
            } else if  (defImg instanceof core.Image) { // found default image
                // timing: attributes.images already coverted to Images
                return defImg;
            }

            return new core.Image(defImg);
        },

        'getDefaultImageId': function () {
            try {
                // product tiles
                if (this.get('default-image')) {
                    return this.get('default-image');
                }
                // product tiles without a default-image attr, guess it
                if (this.get('images') && this.get('images').length) {
                    // product tiles (or tiles with images:[...])
                    var guess = this.get('images')[0]['tile-id'] ||
                                this.get('images')[0].get('tile-id') ||
                                // just going to try everything
                                this.get('images')[0].id ||
                                this.get('images')[0].get('id');
                    if (guess) {
                        return guess;
                    }
                }

                // image tiles (or tiles that are root-level images)
                // note: might be wrong if product tiles still fall through
                return this.get('tile-id').toString();
            } catch (e) {  // no images
                console.warn('This object does not have a default image.', this);
                return undefined;
            }
        },

        /**
         * Get the tile's default image as an object.
         * @returns {Image|undefined}
         */
        'getDefaultImage': function () {
            return this.getImage();
        },

        'url': function () {
            return App.options.IRSource + '/page/' + App.options.campaign + '/tile/' + this.get('tile-id');
        },

        'sync': function (method, model, options) {
            method = 'read'; //Must always be read only
            return Backbone.sync(method, model, options);
        }
    });

    /**
     * The Image object (url, width, height, ...)
     *
     * @constructor
     * @type {*}
     */
    this.Image = Backbone.Model.extend({
        'defaults': {
            'url': 'http://placehold.it/2048&text=blank',
            'dominant-color': 'transparent'
        },

        'initialize': function () {
            // add a name, colour, and a sized url to each size datum
            var self = this,
                color = this.get('dominant-color');

            // the template needs something simpler.
            this.color = color;
            this.url = this.width(App.layoutEngine.width());
        },

        'sync': function () {
            return false;
        },

        /**
         *
         * @param width
         * @param height
         * @param {boolean} obj   whether the complete object or the url
         *                        will be returned
         * @returns {*}
         */
        'dimens': function (width, height, obj) {
            var resized,
                options = $.extend({}, obj);
            resized = $.extend({}, this.defaults, this.attributes);

            if (width > 0) {
                options.width = width;
            }

            if (height > 0) {
                options.height = height;
            }

            resized.url = App.utils.getResizedImage(this.get('url'), options);

            if (obj) {
                return resized;
            }

            return resized.url;
        },

        'width': function (width, obj) {
            // get url by min width
            return this.dimens(width, 0, obj);
        },

        'height': function (height, obj) {
            // get url by min height
            return this.dimens(0, height, obj);
        }
    });

    /**
     * automatically subclassed by TileCollection's model() method
     * @type {Tile}
     */
    this.ImageTile = this.Tile.extend({
        /**
         * An ImageTile  *is* an image JSON, so we need to allocate all of its
         * attributes inside an 'images' field.
         *
         * @param resp
         * @param options
         * @returns {*}
         */
        'parse': function (resp, options) {
            // create tile-like attributes
            resp['default-image'] = 0;

            // image tile contains image:[one copy of itself]
            resp.images = [$.extend(true, {}, resp)];
            return resp;
        }
    });

    /**
     * automatically subclassed by TileCollection's model() method
     * @type {Tile}
     */
    this.VideoTile = this.Tile.extend({
        'defaults': {
            'type': 'video'
        }
    });

    this.YoutubeTile = this.VideoTile.extend({
        'defaults': {
            'type': 'video'
        }
    });

    /**
     * Our TileCollection manages ALL the tiles on the page.
     * This is essentially IntentRank.
     *
     * @constructor
     * @type {Collection}
     */
    this.TileCollection = Backbone.Collection.extend({
        /**
         * Subclass each tile JSON into their specific containers.
         * @param item      model attributes
         * @returns {Tile}   or an extension of it
         */
        'model': function (item) {
            var TileClass = App.utils.findClass('Tile',
                    item.type || item.template, core.Tile);

            return new TileClass(item);
        },

        'config': {},
        'loading' : false,

        // {[tileId: maxShow,]}
        // if tileId is in initial results and you want it shown only once,
        // set maxShow to 0.
        // TILES THAT LOOK THE SAME FOR TWO PAGES CAN HAVE DIFFERENT TILE IDS
        'resultsThreshold': App.option('resultsThreshold', {}),

        /**
         * process common attributes, then delegate the collection's parsing
         * method to their individual tiles.
         *
         * @param resp
         * @param options
         * @returns {Array}
         */
        'parse': function (resp, options) {
            // this = the instance
            var self = this,
                i = 0,
                tileJson,
                tileId,
                respBuilder = [];  // new resp after filter(s)

            for (i = 0; i < resp.length; i++) {
                tileJson = resp[i];
                tileId = tileJson['tile-id'];
                if (!tileId) {
                    continue;  // is this a tile...?
                }

                // (hopefully) temporary method for newegg pages to restrict
                // the appearance of a particular youtube video to
                // "once, including the one in initial results".
                if (tileJson.template === 'youtube' &&
                    tileJson['original-id'] === "YICKow4ckUA") {
                    continue;
                }

                // decrement the allowed displays of each shown tile.
                if (self.resultsThreshold[tileId] !== undefined &&
                    --self.resultsThreshold[tileId] < 0) {
                    // tile has been disabled by its per-page threshold
                    continue;
                }

                respBuilder.push(tileJson);  // this tile passes
            }

            // SHUFFLE_RESULTS is always true
            //respBuilder = _.shuffle(respBuilder); Why do we shuffle the results?

            return _.map(respBuilder, function (jsonEntry) {
                var TileClass = App.utils.findClass('Tile',
                    jsonEntry.type || jsonEntry.template, core.Tile);
                return TileClass.prototype.parse.call(self, jsonEntry);
            });
        },

        /**
         * Allows tiles to be fetched without options.
         *
         * @param options
         * @returns {*}
         */
        fetch: App.intentRank.fetch,

        /**
         * Interact with IR using the built-in Backbone thingy.
         *
         * @returns {Function|String}
         */
        'url': function () {
            var url,
                category = App.intentRank.options.category;

            url = _.template(
                '<%=apiUrl%>/page/<%=campaign%>/getresults?results=<%=results%>',
                this.config
            );

            if (category) {
                return url + "&category=" + encodeURIComponent(category);
            }

            return url;
        },

        'initialize': function (arrayOfData, url, campaign, results) {
            this.setup(url, campaign, results);  // if necessary
            this.tiles = {};
            this.on('add', this.itemAdded, this);
            App.vent.trigger('tileCollectionInitialized', this);
        },

        /**
         * Adds a reference to the tile in a hashmap of tiles.  Useful for
         * getting the tile if you only know the real tile id.
         *
         * @param tile {Object}
         * @param collection {Object}
         * @param options {Object}
         */
        'itemAdded': function (tile, collection, options) {
            var id = tile.get('tile-id');
            this.tiles[id] = tile;
        },

        /**
         * (Re)configure this object to fetch from an Intent Rank URL.
         *
         * @param apiUrl
         * @param campaign
         * @param results
         */
        'setup': function (apiUrl, campaign, results) {
            // apply new parameters, or default to existing ones
            this.config.apiUrl = apiUrl ||
                App.option('IRSource') ||
                this.config.apiUrl;
            this.config.campaign = campaign ||
                App.option('campaign') ||
                this.config.campaign;
            this.config.results = results ||
                App.option('IRResultsCount') ||
                this.config.results;
        }
    });


    /**
     * Categories are used to filter results from IR.
     *
     * @constructor
     * @type {Model}
     */
    this.Category = Backbone.Model.extend({
        'url': function () {
            return _.template(
                '<%=IRSource%>/page/<%=campaign%>/getresults?results=<%=IRResultsCount&category=<%=name%>',
                _.extend({}, App.options, this.attributes)
            );
        }
    });

    /**
     * Container for categories, does nothing for now.
     *
     * @constructor
     * @type {Collection}
     */
    this.CategoryCollection = Backbone.Collection.extend({
        model: this.Category
    });
});
