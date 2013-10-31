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

        'initialize': function (attributes, options) {
            var self = this,
                defaultImage,
                videoTypes = ["youtube", "video"],
                type = this.get('content-type').toLowerCase(),
                imgInstances = [];

            try {
                defaultImage = this.getDefaultImage();
                this.set({
                    'defaultImage': defaultImage,
                    'dominant-colour': defaultImage.get('dominant-colour')
                });
            } catch (e) {
                // not a tile with default-image, or
                // image tile has no size information
                this.set({
                    'defaultImage': new module.Image({
                        'url': this.get('url')
                    })
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

            // replace all image json with their objects.
            _.each(this.get('images'), function (image) {
                imgInstances.push(new module.Image(image));
            });
            self.set('images', imgInstances);

            broadcast('tileModelInitialized', this);
        },

        'getDefaultImageId': function () {
            try {
                return this.get('default-image') ||
                    this.get('images')[0].id ||
                    this.get('images')[0].get('id');
            } catch (e) {  // no images
                console.warn('this tile has no images.', this);
                return undefined;
            }
        },

        'getImage': function (imgId) {
            var self = this, defImg;

            imgId = imgId || self.getDefaultImageId();

            defImg = _.findWhere(this.get('images'), {
                'id': imgId
            });

            if (!defImg) {
                try {
                    if (this.get('images')[0] instanceof module.Image) {
                        return this.get('images')[0];
                    } else {
                        return new module.Image(this.get('images')[0]);
                    }
                } catch (err) {
                    // zero images
                }
            }

            // found default image or undefined
            if (defImg instanceof module.Image) {
                // timing: attributes.images already coverted to Images
                return defImg;
            }
            return new module.Image(defImg);
        },

        /**
         * Get the tile's default image as an object.
         * @returns {Image|undefined}
         */
        'getDefaultImage': function () {
            return this.getImage();
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
     *
     * @type {*}
     */
    this.Image = Backbone.Model.extend({
        'defaults': {
            'url': 'http://placehold.it/2048&text=blank',
            'sizes': {
                'master': {
                    'name': 'master',  // easier to know what this is as an obj
                    'dominant-colour': '#ffffff',
                    'width': 2048,
                    'height': 2048
                }
            }
        },

        'initialize': function (data) {
            // add a name, colour, and a sized url to each size datum
            var self = this,
                color = this.get('dominant-colour');
            _.map(this.get('sizes'), function (size, sizeName) {
                self.get('sizes')[sizeName].url =
                    self.get('url').replace(/master\./, sizeName + '.');

                self.get('sizes')[sizeName].name = sizeName;
                self.get('sizes')[sizeName]['dominant-colour'] = color;
            });
        },

        'toJSON': function (options) {
            // the template needs something simpler.
            var attribs = _.clone(this.attributes);
            attribs.normal = this.width(255);
            attribs.wide = this.width(510);
            attribs.full = this.width(1020);
            return attribs;
        },

        'size': function (size) {
            // get url by size name, e.g. 'pico'
            var sizes = this.get('sizes');
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
            var first, sizes = this.get('sizes');
            try {
                first = _.first(_(sizes)
                    .sortBy('width')
                    .filter(function (size) {
                        return size.width >= width && size.height >= height;
                    }));

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
        'defaults': {
            'tile-class': 'image',
            'content-type': 'image'
        },
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
            resp.images = [resp];  // image tile containing one pointer to itself
            return resp;
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
        'loading' : false,

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
            var self = this;

            // SHUFFLE_RESULTS is always true
            resp = _.shuffle(resp);

            return _.map(resp, function (jsonEntry) {
                var TileClass = SecondFunnel.utils.findClass('Tile',
                    jsonEntry.template, module.Tile);
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
            }, this.config, options);

            return Backbone.Collection.prototype.fetch.call(this, opts);
        },

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
            broadcast('tileCollectionInitialized', this);
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
            this.config.apiUrl = apiUrl || this.config.apiUrl ||
                SecondFunnel.option('IRSource');
            this.config.campaign = campaign || this.config.campaign ||
                SecondFunnel.option('campaign');
            this.config.results = results || this.config.results ||
                SecondFunnel.option('IRResultsCount');
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