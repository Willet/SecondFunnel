SecondFunnel.module("utils", function (utils) {
    "use strict";

    var $document = $(document),
        $window = $(window),
        regions = {},
        regionWidgets = {};

    utils.safeString = function (str, opts) {
        // trims the string and checks if it's just 'None'.
        // more checks to come later.
        return $.trim(str).replace(/^(None|undefined|false|0)$/, '');
    };

    utils.registerWidget = function (name, selector, functionality) {
        // add a predefined UI component implemented as a region.
        // name must be unique. if registerWidget is called with an existing
        // widget, the old one is overwritten.
        regions[name] = selector;
        regionWidgets[name] = functionality;
        broadcast('widgetRegistered', name, selector, functionality,
            regions, regionWidgets);
    };

    utils.addClass = function (name, defn) {
        // allows designers to add a custom (tile) class.
        // if class name is already taken, the original class is overwritten.
        SecondFunnel.classRegistry = SecondFunnel.classRegistry || {};
        SecondFunnel.classRegistry[name] = defn;
        broadcast('classAdded', name, defn);
        return defn;
    };

    utils.findClass = function (typeName, prefix, defaultClass) {
        // returns a class in the window scope and class registry.
        // default: optional. returns it if nothing else is found.
        var FoundClass,
            targetClassName = _.capitalize(prefix) + _.capitalize(typeName);
        if (SecondFunnel.classRegistry[targetClassName] !== undefined) {
            // if designers want to define a new tile view, they must
            // let SecondFunnel know of its existence.
            FoundClass = SecondFunnel.classRegistry[targetClassName];
        } else {
            FoundClass = defaultClass;
        }

        if (SecondFunnel.options.debug >= SecondFunnel.VERBOSE) {
            console.log('findClass(%s, %s, %O) -> %O',
                        typeName, prefix, defaultClass, FoundClass);
        }

        return FoundClass;
    };

    utils.runWidgets = function (viewObject) {
        // process widget regions.
        // each widget function receives args (the view, the $element, option alias).
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

    utils.pickImageSize = function (url, minWidth, scalePolicy) {
        // returns a url that is either
        //   - the url, if it is not an image service url, or
        //   - an image url pointing to one that is at least as wide as
        //     minWidth, or
        //   - an image url pointing to one that is at most as wide as
        //     the window width, or
        //   - if minWidth is ridiculously large, master.jpg.
        // if scalePolicy is "max", then the image served is always smaller
        //   than requested.
        var i,
            prevKey = 'pico',
            maxLogicalSize = Math.min($window.width(), $window.height()),
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