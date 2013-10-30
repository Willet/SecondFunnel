/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _,
  Willet, broadcast, console, SecondFunnel */
/**
 * @module core
 */
SecondFunnel.module('core', function (module, SecondFunnel) {
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
            'tile-id': 0,
            'tile-class': 'tile',
            'content-type': "",
            'related-products': [],
            'dominant-colour': "transparent"
        },

        /**
         * Processes IR's image sizes. Instagram (Image) tiles have their
         * own parsing implementation.
         *
         * @param resp
         * @param options
         * @returns {*}
         */
        'parse': function (resp, options) {
            var defaultImage,
                productImages = resp.images,
                imgUrl,
                imgSizes;

            // if this tile has images at all
            if (_.has(resp, 'default-image') &&
                productImages && productImages.length) {
                // if this tile has the default image that the tile claims
                // to be default
                defaultImage = _.findWhere(productImages, {
                    'id': resp['default-image']
                });

                if (defaultImage) {
                    imgUrl = defaultImage.url;
                    imgSizes = defaultImage.sizes;
                }
            }
            return resp;
        },

        'initialize': function (attributes, options) {
            var self = this,
                defaultImage,
                videoTypes = ["youtube", "video"],
                type = this.get('content-type').toLowerCase();

            try {
                defaultImage = this.getImageAttrs();
                this.set({
                    'defaultImage': defaultImage,
                    'dominant-colour': defaultImage['dominant-colour']
                });
            } catch (e) {
                // not a tile with default-image, or
                // image tile has no size information
                this.set({
                    'defaultImage': {
                        'url': this.get('url')
                    }
                });
            }

            // set up tile type overrides
            this.set({
                'type': this.get('template'),  // default type being its template
                'caption': SecondFunnel.utils.safeString(this.get("caption"))
            });
            if (_.contains(videoTypes, type)) {
                this.set('type', 'video');
            }

            broadcast('tileModelInitialized', this);
        },

        'getDefaultImageId': function () {
            return this.get('default-image') || undefined;
        },

        'getImageAttrs': function (imgId) {
            var img;

            // default to image-id
            imgId = imgId || this.getDefaultImageId();

            if (imgId) {
                // a product tile does not have default-image
                img = _.clone(_.findWhere(this.get('images'), {
                    'id': imgId.toString()
                }));
            } else {
                // an image tile does not have default-image
                img = this.attributes;
            }

            if (!img) {
                throw "Image #" + imgId + " not found";
            }
            if (!img.sizes) {
                // IR gave no sizes. fill it
                img.sizes = {
                    'master': {
                        'width': 2048,
                        'height': 2048
                    }
                };
            }

            _.each(img.sizes, function (sizeObj, sizeName) {
                // assign names to convenience urls.
                img[sizeName] = img.url.replace(/master\./, sizeName + '.');
            });

            return img;
        },

        /**
         * picks an image at least as large as the dimensions you needed.
         *
         * @param imgId
         * @param {Object} requirements   width: 123, height: 123, or both
         */
        'getSizedImage': function (imgId, requirements) {
            var img, minDimension, sizeName, fnRegex;

            // default to image-id
            img = this.getImageAttrs(imgId);

            if (!requirements) {
                return img.url;  // always master.jpg
            }

            // filter defaults
            requirements.width = requirements.width || 1;
            requirements.height = requirements.height || 1;

            // look through the list of sizes and pick the next biggest one
            minDimension = _(img.sizes).filter(function (name, dimens) {
                // filter "as least as large"
                return dimens.width >= requirements.width &&
                    dimens.height >= requirements.height;
            }).sort(function(a, b) {
                // sort sizes ASC
                return a.width - b.width;
            });

            if (!minDimension.length) {
                // requested size exceeded the largest one we have
                return img.url;
            }

            // replace master.jpg by its resized image path.
            sizeName = _.getKeyByValue(img.sizes, minDimension[0]);
            fnRegex = new RegExp('master.' + img.format);
            return img.url.replace(fnRegex, sizeName + img.format);
        },

        'sync': function () {
            return false;  // forces ajax PUT requests to the server to succeed.
        },

        'is': function (type) {
            // check if a tile is of (type). the type is _not_ the tile json.
            return this.get('content-type').toLowerCase() === type.toLowerCase();
        }
    });

    /**
     * automatically subclassed by TileCollection's model() method
     * @type {Tile}
     */
    this.ImageTile = this.Tile.extend({
        'defaults': {
            'tile-class': 'image',
            'content-type': 'image'
        },
        'parse': function (resp, options) {
            var newResp = _.clone(resp),
                imgUrl = newResp.url,
                imgSizes = newResp.sizes;
            if (!imgSizes.length) {
                newResp.sizes = {
                    // stub out sizes for images without them
                    'master': {
                        'width': 2048,
                        'height': 2048
                    }
                };
            }
            // create tile-like attributes
            return {
                'defaultImage': newResp
            };
        }
    });

    /**
     * automatically subclassed by TileCollection's model() method
     * @type {Tile}
     */
    this.VideoTile = this.Tile.extend({
        'defaults': {
            'tile-class': 'video',
            'content-type': 'video'
        }
    });

    this.YoutubeTile = this.VideoTile.extend({
        'defaults': {
            'tile-class': 'youtube',
            'content-type': 'youtube'
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
            var TileClass = SecondFunnel.utils.findClass('Tile',
                    item.template, module.Tile);

            return new TileClass(item);
        },

        'config': {},

        /**
         * process common attributes, then relay the collection's parsing
         * method to their individual tiles.
         *
         * @param resp
         * @param options
         * @returns {Array}
         */
        'parse': function (resp, options) {
            // this = the instance
            var self = this;
            return _.map(resp, function (jsonEntry) {
                var TileClass = SecondFunnel.utils.findClass('Tile',
                    resp.template, module.Tile);
                return TileClass.prototype.parse.call(self, jsonEntry);
            });
        },

        /**
         * From nicks-happy-place.
         * Allows tiles to be fetched without options.
         *
         * @param options
         * @returns {*}
         */
        fetch: function (options) {
            var opts = $.extend({}, {
                'results': 10,
                'add': true,
                'merge': true,
                'remove': false
            }, options);

            return Backbone.Collection.prototype.fetch.call(this, opts);
        },

        /**
         * Interact with IR using the built-in Backbone thingy.
         *
         * @returns {Function|String}
         */
        'url': function () {
            return _.template(
                '<%=url%>/page/<%=campaign%>/getresults?results=<%=results%>',
                this.config
            );
        },

        'loading' : false,

        'initialize': function (arrayOfData, url, campaign, results) {
            this.setup(url, campaign, results);  // if necessary
            broadcast('tileCollectionInitialized', this);
        },

        'setup': function (url, campaign, results) {
            this.config.url = url || SecondFunnel.option('IRSource');
            this.config.campaign = campaign || SecondFunnel.option('campaign');
            this.config.results = results || SecondFunnel.option('IRResultsCount');
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