SecondFunnel.module("utils", function (utils, SecondFunnel) {
    "use strict";

    var $document = $(document),
        $window = $(window),
        regions = {},
        regionWidgets = {};

    /**
     * Cleans obviously invalid UI strings.
     *
     * @param {string} str
     * @param {undefined} opts
     * @returns {string}
     */
    utils.safeString = function (str, opts) {
        var regex =/^(None|undefined|[Ff]alse|0)$/,
            trimmed = $.trim(str);
        if (regex.test(trimmed)) {
            return trimmed.replace(regex, '');
        }
        return str;
    };

    /**
     * Does minimal URL checking (stackoverflow.com/a/1305082/1558430)
     *
     * @param {string} url
     * @returns {bool}
     */
    utils.isURL = function (url) {
        return (typeof url === 'string' && url.length > 2 &&
            url.indexOf('//') >= 0);
    };

    /**
     * add a predefined UI component implemented as a region.
     * @param {string} name of the widget.
     *                 name must be unique.
     *                 if registerWidget is called with an existing
     *                  widget, the old one is overwritten.
     *
     * @param {string} selector a jquery selector,
     * @param {function} functionality the widget function.
     * @returns true
     */
    utils.registerWidget = function (name, selector, functionality) {
        regions[name] = selector;
        regionWidgets[name] = functionality;
        broadcast('widgetRegistered', name, selector, functionality,
            regions, regionWidgets);
        return true;  // success
    };

    /**
     * allows designers to add a custom (tile) class.
     * if class name is already taken, the original class is overwritten.
     *
     * @param {string} name
     * @param {object} defn
     * @returns defn
     */
    utils.addClass = function (name, defn) {
        SecondFunnel.core[_.capitalize(name)] = defn;
        broadcast('classAdded', name, defn);
        return defn;
    };

    /**
     * returns a class in the window scope and app core,
     *  or defaultClass if nothing else is found.
     * This is also known as patching.
     *
     * @param {string} typeName e.g. 'Tile', 'TileView'
     * @param {string} prefix e.g. 'Video'
     * @param {object} defaultClass e.g. TileView
     * @returns {object}|defaultClass
     */
    utils.findClass = function (typeName, prefix, defaultClass) {
        var FoundClass,
            targetClassName = _.capitalize(prefix || '') +
                              _.capitalize(typeName || '');
        if (SecondFunnel.core[targetClassName] !== undefined) {
            // if designers want to define a new tile view, they must
            // let SecondFunnel know of its existence.
            FoundClass = SecondFunnel.core[targetClassName];
        } else {
            FoundClass = defaultClass;
        }

        console.debug('findClass(%s, %s, %O) -> %O', typeName, prefix,
            defaultClass, FoundClass);

        return FoundClass;
    };

    /**
     * process widget regions.
     * each widget function receives args (the view, the $element, option alias).
     * TODO: tests
     *
     * @param {View} viewObject
     */
    utils.runWidgets = function (viewObject) {
        var self = viewObject;

        // process itself (if it is a view)
        _.each(regions, function (selector, name, list) {
            var widgetFunc = regionWidgets[name];
            self.$(selector).each(function (idx, el) {
                return widgetFunc(self, $(el), SecondFunnel.option);
            });
        });

        // process children regions (if it is a layout)
        _.each(self.regions, function (selector, name, list) {
            var isWidget = _.contains(regions, name),
                widgetFunc = (regionWidgets || {})[name];
            if (isWidget && widgetFunc) {
                self.$(selector).each(function (idx, el) {
                    return widgetFunc(self, $(el), SecondFunnel.option);
                });
            }
        });
    };

    /**
     * returns a url that is either
     *    - the url, if it is not an image service url, or
     *    - an image url pointing to one that is at least as wide as
     *      minWidth, or
     *    - an image url pointing to one that is at most as wide as
     *      the window width, or
     *    - if minWidth is ridiculously large, master.jpg.
     * if scalePolicy is "max", then the image served is always smaller
     *    than requested.
     *
     * @param {string} url
     * @param {int} minWidth
     * @param {min|max|undefined} scalePolicy
     * @returns {string}
     */
    utils.pickImageSize = function (url, minWidth, scalePolicy) {
        var i,
            prevKey = 'pico',
            maxLogicalSize = Math.min($window.width(), $window.height()),
            // TODO: URL spec not found in /Willet/planning/blob/master/architecture/specifications/image-service.md
            sizable = /images\.secondfunnel\.com.+\.(jpe?g|png)/.test(url),
            nameRegex = /([^/]+)\.(jpe?g|png)/,
            imageSizes = SecondFunnel.option('imageSizes', {
                // see Scraper: ImageServiceIntegrationTest.java#L52
                "pico": 16,
                "icon": 32,
                "thumb": 50,
                "small": 100,
                "compact": 160,
                "medium": 240,
                "large": 480,
                "grande": 600,
                "1024x1024": 1024,
                "master": 2048
            });

        if (!utils.isURL(url)) {
            throw "First parameter must be a valid URL";
        }

        if (!sizable) {
            return url;
        }

        // TODO: a better idea
        for (i in imageSizes) {
            if (imageSizes.hasOwnProperty(i)) {
                if (!scalePolicy || scalePolicy === 'min') {
                    if (imageSizes[i] >= minWidth) {
                        return url.replace(nameRegex, i + '.$2');
                    }
                } else if (scalePolicy === 'max') {
                    if (imageSizes[i] >= minWidth) {
                        return url.replace(nameRegex, prevKey + '.$2');
                    }
                }
                if (imageSizes[i] >= maxLogicalSize) {
                    return url.replace(nameRegex, prevKey + '.$2');
                }
            }
            prevKey = i;
        }
        return url;
    };
});