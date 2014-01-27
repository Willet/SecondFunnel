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
            'caption': "Shop product",
            'description': '',
            'tile-id': 0,
            // 'tile-class': 'tile',  // what used tile-class?
            // 'content-type': ''  // where did content-type go?
            'related-products': [],
            'dominant-colour': "transparent"
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
                uri = this.get('url'),
                redirect_uri = this.get('redirect-url');

            // replace all image json with their objects.
            _.each(this.get('images'), function (image) {
                var localImageVariable;
                if (typeof image === 'string') {
                    // patch old IR image response with this new dummy format,
                    // wild guessing every attribute in the process.
                    localImageVariable = {
                        'format': "jpg",
                        'dominant-colour': "transparent",
                        'url': image,
                        'id': self.getDefaultImageId() || 0,
                        'sizes': {
                            'master': {
                                'width': 2048,
                                'height': 2048
                            }
                        }
                    };
                } else {
                    // make a copy...
                    localImageVariable = $.extend(true, {}, image);
                }
                imgInstances.push(new core.Image(localImageVariable));
            });

            // check if url exists and that we have search params
            if (App.URL_PARAMS.length > 0) {
                if (uri) {
                    uri += (uri.indexOf('?') > -1 ? '&' : '?') +
                        App.URL_PARAMS.substr(1);
                }
                if (redirect_uri) {
                    this.set({
                      'redirect-url': redirect_uri + (redirect_uri.indexOf('?') > -1 ? '&' : '?') +
                        App.URL_PARAMS.substr(1)
                    });
                }
            }

            // this tile has no images, or can be an image itself
            if (imgInstances.length === 0) {
                imgInstances.push(new core.Image({
                    'url': uri
                }));
            }

            defaultImage = this.getDefaultImage();

            this.set({
                'images': imgInstances,
                'defaultImage': defaultImage,
                'dominant-colour': defaultImage.get('dominant-colour'),
                'url': uri
            });

            App.vent.trigger('tileModelInitialized', this);
        },

        /**
         *
         * @param byImgId   if omitted, the default image id
         * @returns {core.Image}
         */
        'getImage': function (byImgId) {
            var self = this,
                imgId = parseInt(byImgId || self.getDefaultImageId(), 10),
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
                    // fuck this shit (wild guess)
                    return new core.Image({
                        'url': this.get('url')
                    });
                }
            }

            // found default image or undefined
            if (defImg instanceof core.Image) {
                // timing: attributes.images already coverted to Images
                return defImg;
            }

            if (!defImg) {
                console.warn('getImage is going to return an Image stub.');
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

        'sync': function () {
            return false;  // forces ajax PUT requests to the server to succeed.
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
            'sizes': {
                'master': {
                    'name': 'master',  // easier to know what this is as an obj
                    'dominant-colour': 'transparent',
                    'width': 2048,
                    'height': 2048
                }
            }
        },

        'initialize': function () {
            // add a name, colour, and a sized url to each size datum
            var self = this,
                color = this.get('dominant-colour'),

                // this might be the 36-hour line
                mySizes = $.extend(true, {}, this.get('sizes'));

            _.map(mySizes, function (size, sizeName) {
                mySizes[sizeName].url =
                    self.get('url').replace(/master\./, sizeName + '.');

                mySizes[sizeName].name = sizeName;
                mySizes[sizeName]['dominant-colour'] = color;
            });

            self.set('sizes', mySizes);

            // the template needs something simpler.
            this.color = color;
            this.normal = this.width(255);
            this.wide = this.width(510);
            this.full = this.width(1020);
            this.url = this.normal;  // overwrites backbone method
        },

        'sync': function () {
            return false;
        },

        'size': function (size) {
            // get url by size name, e.g. 'pico'
            var sizes = this.get('sizes');

            size = size || 'large';  // first size above 255px wide

            try {
                return sizes[size].url;
            } catch (e) {  // size not available ==> master.jpg
                return this.get('url');
            }
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
            var first,
                sizes = this.get('sizes'),
                sortedImages;
            try {
                // [{master}] if mocked
                sortedImages = _(sizes)
                    .sortBy('width')
                    .filter(function (size) {
                        return size.width >= width && size.height >= height;
                    });

                // {master} if mocked
                first = _.first(sortedImages) ||  // if one image is large enough
                    // the largest one if none of the images are large enough
                    // (unstable sort if widths equal for any two sizes)
                    _(sizes).sortBy('width').reverse()[0];

                if (obj) {
                    return first;
                }
                return first.url;
            } catch (e) {  // size not available

                if (obj) {
                    return $.extend({}, this.defaults, this.get('url'));
                }
                return this.get('url');
            }
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
                // the appearance of each "banner" tile to "once".
                if (tileJson.template === 'banner') {
                    if (self.resultsThreshold[tileId] === undefined) {
                        // give each tile ONE chance to appear,
                        // whatever its tile id is
                        self.resultsThreshold[tileId] = 1;
                    }
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
            respBuilder = _.shuffle(respBuilder);

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
            return _.template(
                '<%=apiUrl%>/page/<%=campaign%>/getresults?results=<%=results%>',
                this.config
            );
        },

        'initialize': function (arrayOfData, url, campaign, results) {
            this.setup(url, campaign, results);  // if necessary
            App.vent.trigger('tileCollectionInitialized', this);
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
     * Base empty category, no functionality needed here.
     *
     * @constructor
     * @type {Model}
     */
    this.Category = Backbone.Model.extend({

    });

});
