/*global App, Backbone, Marionette, console, _, $, location */
/**
 * @module utils
 */
App.module("utils", function (utils, App) {
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
    this.safeString = function (str, opts) {
        var regex = /^(None|undefined|[Ff]alse|0)$/,
            trimmed = $.trim(str);
        if (regex.test(trimmed)) {
            return trimmed.replace(regex, '');
        }
        return str;
    };

    $window.on('message', function (event) {
        var originalEvent = event.originalEvent,
            data = originalEvent.data;

        try {
            data = JSON.parse(data);
        } catch (error) {
            return;
        }

        if (data.target !== 'second_funnel') {
            return;
        }

        if (!data.type) {
            return;
        }

        if (data.type === 'load_content') {
            var loadUntilHeight = function (height) {
                if ($('body').height() < height) {
                    App.discoveryArea.currentView.collection.fetch().done(function () {
                        loadUntilHeight(height);
                    });
                }
            };
            loadUntilHeight(data.height);
        } else if (data.type === 'window_location') {
            App.window_middle = data.window_middle;

            if (App.previewArea.currentView) {
                App.previewArea.currentView.$el.css('top',
                    Math.max(App.window_middle - (App.previewArea.currentView.el.height() / 2), 0)
                );
            }
        }
    });

    this.postExternalMessage = function (message) {
        window.parent.postMessage(message, '*');
    };

    /**
     * Does minimal URL checking (stackoverflow.com/a/1305082/1558430)
     *
     * @param {string} url
     * @returns {bool}
     */
    this.isURL = function (url) {
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
    this.registerWidget = function (name, selector, functionality) {
        regions[name] = selector;
        regionWidgets[name] = functionality;
        App.vent.trigger('widgetRegistered', name, selector, functionality,
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
    this.addClass = function (name, defn) {
        App.core[_.capitalize(name)] = defn;
        App.vent.trigger('classAdded', name, defn);
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
    this.findClass = function (typeName, prefix, defaultClass) {
        var className = _.capitalize(prefix || '') + _.capitalize(typeName || '');
        return App.core[className] || defaultClass;
    };

    /**
     * process widget regions.
     * each widget function receives args (the view, the $element, option alias).
     * TODO: tests
     *
     * @param {View} viewObject
     */
    this.runWidgets = function (viewObject) {
        var self = viewObject;

        // process itself (if it is a view)
        _.each(regions, function (selector, name, list) {
            var widgetFunc = regionWidgets[name];
            self.$(selector).each(function (idx, el) {
                return widgetFunc(self, $(el), App.option);
            });
        });

        // process children regions (if it is a layout)
        _.each(self.regions, function (selector, name, list) {
            var isWidget = _.contains(regions, name),
                widgetFunc = (regionWidgets || {})[name];
            if (isWidget && widgetFunc) {
                self.$(selector).each(function (idx, el) {
                    return widgetFunc(self, $(el), App.option);
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
     *
     * @param {string} url
     * @param {int} minWidth
     * @deprecated
     *
     * @returns {string}
     */
    this.pickImageSize = function (url, minWidth) {
        return url;
    };

    /**
     * $.fn.css() cannot translate 8-code hex to rgba.
     *
     * @param {string} hexColor   e.g. '#abcdef'
     * @param {float}  opacity    e.g. 0.5
     * @return {string}           e.g. rgba(1,2,3,opacity)
     */
    this.hex2rgba = function (hexColor, opacity) {
        return 'rgba(' + parseInt(hexColor.slice(-6, -4), 16) +
            ',' + parseInt(hexColor.slice(-4, -2), 16) +
            ',' + parseInt(hexColor.slice(-2), 16) +
            ',' + opacity + ')';
    };

    /**
     * execute param1 if any only if param2 is true
     */
    this.iff = function (fn, flag) {
        var truthTest = flag;
        if (typeof flag === 'function') {
            truthTest = flag();
        }
        if (truthTest) {
            return fn();
        }
        return false;
    };

    /**
     * Get query strings
     * http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
     */
    this.getQuery = function (name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    };

    /**
     * Returns a formatted url for a cloudinary image
     *
     * @param {string} url
     * @param {Object} options
     *
     * @returns {Object}
     */
    this.getResizedImage = function (url, options) {
        var columnWidth = App.layoutEngine.width(),
            width = options.width || columnWidth,
            height = options.height || columnWidth * 2,
            multiplier = App.support.mobile() ? 1 : 2;

        // Round to the nearest whole hundred pixel dimension;
        // prevents creating a ridiculous number of images.
        if (width > height) {
            // wider than it is tall, so have to apply aspect
            // ratio calculations
            height = (height / width) * columnWidth;
            height = Math.ceil((height / 100.0) * 100);
            options.height = height * multiplier;
        } else {
            width = Math.ceil((columnWidth / 100.0) * 100);
            options.width = width * multiplier;
        }

        options = _.extend({
            crop: 'fit'
        }, options);

        return $.cloudinary.url(url, options);
    };
});
