/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _, console, App */
/**
 * @module core
 */
App.module('core', function (core, App) {
    // other args: https://github.com/marionettejs/Marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document),
        tempTiles = [],  // a list of portrait tiles
        unpairedTile;  // the last tile left behind

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
                throw 'Missing store slug';
            }
            if (!data.displayName) {
                this.set('displayName', this.get('name'));
            }
        }
    });

    this.Product = Backbone.Model.extend();

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
            'caption': '',
            'description': '',
            'tile-id': 0,
            // 'tile-class': 'tile',  // what used tile-class?
            // 'content-type': ''  // where did content-type go?
            'tagged-products': [],
            'dominant-color': 'transparent'
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
                imgInstances,
                relatedProducts;

            // replace all image json with their objects.
            imgInstances = _.map(this.get('images'), function (image) {
                return new core.Image($.extend(true, {}, image));
            }) || [];

            // this tile has no images, or can be an image itself
            if (imgInstances.length === 0) {
                imgInstances.push(new core.Image({
                    'dominant-color': this.get('dominant-color'),
                    'url': this.get('url')
                }));
            }

            defaultImage = self.getDefaultImage();

            // Transform related-product image, if necessary
            relatedProducts = this.get('tagged-products');
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
                'tagged-products': relatedProducts,
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
         * @param width           in px; 0 means no width restrictions
         * @param height          in px; 0 means no height restrictions
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

            if (!(width || height)) {
                options.width = App.layoutEngine.width();
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
         * reorder landscape tiles to only appear after a multiple-of-2
         * products has appeared, allowing gapless layouts in two-col ads.
         *
         * this method requires state to be maintained in the tempTiles variable;
         * it is not idempotent.
         *
         * TODO: this belongs to the layout engine.
         *
         * @param {object} resp     an array of tile json
         * @returns {object}        an array of tile json
         */
        reorderTiles: function (resp) {
            var i = 0,
                col = 0,
                columnCount = 2,  // magic number (other values don't work)
                isIframe = App.utils.isIframe(),
                tile,
                tileId,
                respBuilder = [];  // new resp after filter(s)

            // wide tile left over from last run
            for (i = 0; i < resp.length; i++) {
                tile = resp[i];
                tileId = tile['tile-id'];
                if (!tileId) {
                    continue;  // is this a tile...?
                }

                // this is NOT an ad, subject to none of these conditions
                if (!isIframe) {
                    respBuilder.push(tile);
                    continue;
                }

                if (!tile.orientation) {
                    tile.orientation = 'portrait';
                }

                // limit col to either 0 or 1
                col = col % columnCount;

                // add lone wide tile (if exists)
                if (unpairedTile && col % 2 === 0) {
                    respBuilder.push(unpairedTile);
                    unpairedTile = undefined;
                    // TODO: switch to while loop to avoid this mess
                    i--; continue;
                }

                if (tile.orientation === 'landscape') {
                    if (col === 0) {
                        // wide and col 0 = good
                        respBuilder.push(tile);
                    } else {
                        // wide and col 1 = good
                        unpairedTile = tile;
                        // TODO: switch to while loop to avoid this mess
                        i--;
                    }
                    continue;
                }

                // portrait? check if there are portrait tiles queued
                if (tempTiles.length) {
                    respBuilder.push(tempTiles.shift());
                    col++;
                }
                // there is now either a tile in col 0 or one in col 1
                if (col % 2 === 0) {
                    if (i !== resp.length - 1) {  // unpaired last tile condition
                        tempTiles.push(tile);
                    }
                } else {
                    respBuilder.push(tile);
                    col++;
                }
            }
            return respBuilder;
        },

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
                col = 0,
                isIframe = App.utils.isIframe(),
                tile,
                tileId,
                tileIds = App.intentRank.getTileIds(),
                respBuilder = [];  // new resp after filter(s)

            // reorder landscape tiles to only appear after a multiple-of-2
            // products has appeared, allowing gapless layouts in two-col ads.
            resp = self.reorderTiles(resp);

            // wide tile left over from last run
            for (i = 0; i < resp.length; i++) {
                tile = resp[i];
                tileId = tile['tile-id'];
                if (!tileId) {
                    continue;  // is this a tile...?
                }

                // this is NOT an ad, subject to none of these conditions
                if (!isIframe) {
                    respBuilder.push(tile);
                    continue;
                }

                if (!tile.orientation) {
                    tile.orientation = 'portrait';
                }

                // limit col to either 0 or 1
                col = col % 2;

                // add lone wide tile (if exists)
                if (unpairedTile && col % 2 === 0) {
                    respBuilder.push(unpairedTile);
                    unpairedTile = undefined;
                    i--; continue;
                }

                if (tile.orientation === 'landscape') {
                    if (col === 0) {
                        // wide and col 0 = good
                        respBuilder.push(tile);
                    } else {
                        // wide and col 1 = good
                        unpairedTile = tile;
                        i--;
                    }
                    continue;
                }

                // portrait? check if there are portrait tiles queued
                if (tempTiles.length) {
                    respBuilder.push(tempTiles.shift());
                    col++;
                }
                // there is now either a tile in col 0 or one in col 1
                if (col % 2 === 0) {
                    if (i !== resp.length - 1) {  // unpaired last tile condition
                        tempTiles.push(tile);
                    }
                } else {
                    respBuilder.push(tile);
                    col++;
                }
            }
            resp = respBuilder;
            respBuilder = [];

            for (i = 0; i < resp.length; i++) {
                tile = resp[i];
                tileId = tile['tile-id'];
                if (!tileId) {
                    continue;  // is this a tile...?
                }

                // decrement the allowed displays of each shown tile.
                if (self.resultsThreshold[tileId] !== undefined &&
                    --self.resultsThreshold[tileId] < 0) {
                    // tile has been disabled by its per-page threshold
                    continue;
                }

                // if algorithm is finite but a dupe is about to occur,
                // issue a warning but display anyway
                if (App.option('IRAlgo', 'generic').indexOf('finite') > -1) {
                    if (tileIds.indexOf(tileId) > -1) {
                        console.warn('Tile '  + tileId + ' is already on the page!');
                        if (!App.option('allowTileRepeats', false)) {
                            continue;
                        }
                    }
                }

                respBuilder.push(tile);  // this tile passes
            }

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
                return url + '&category=' + encodeURIComponent(category);
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
