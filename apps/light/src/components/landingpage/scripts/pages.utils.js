'use strict';

require('jquery-deparam');
/**
 * @module utils
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

    var $window = $(window),
        regions = {},
        regionWidgets = {};

    /**
     * Cleans obviously invalid UI strings.
     *
     * @param {string} str
     * @param {undefined} opts
     * @returns {string}
     */
    module.safeString = function (str) {
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
            App.windowMiddle = data.window_middle;
            App.windowHeight = data.window_height;

            if (App.previewArea.currentView) {
                if (App.support.mobile()) {
                    App.previewArea.currentView.$el.css('height', App.window_height);
                }

                App.previewArea.currentView.$el.css('top',
                    Math.max(App.window_middle - (App.previewArea.currentView.el.height() / 2), 0)
                );
            }
        }
    });

    module.postExternalMessage = function (message) {
        window.parent.postMessage(message, '*');
    };

    /**
     * @returns true     if the page is in an iframe.
     */
    module.isIframe = function () {
        if (typeof top === 'undefined') {
            return false;
        }
        return (window !== top);
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
     module.registerWidget = function (name, selector, functionality) {
        regions[name] = selector;
        regionWidgets[name] = functionality;
        App.vent.trigger('widgetRegistered', name, selector, functionality,
            regions, regionWidgets);
        return true;  // success
    };

    /**
     * process widget regions.
     * each widget function receives args (the view, the $element, option alias).
     * TODO: tests
     *
     * @param {View} viewObject
     */
    module.runWidgets = function (viewObject) {
        var self = viewObject;

        // process itself (if it is a view)
        _.each(regions, function (selector, name, list) {
            var widgetFunc = regionWidgets[name];
            self.$(selector).each(function (idx, el) {
                return widgetFunc.call(self, self, $(el), App.option);
            });
        });

        // process children regions (if it is a layout)
        _.each(self.regions, function (selector, name, list) {
            var isWidget = _.contains(regions, name),
                widgetFunc = (regionWidgets || {})[name];
            if (isWidget && widgetFunc) {
                self.$(selector).each(function (idx, el) {
                    return widgetFunc.call(self, self, $(el), App.option);
                });
            }
        });
    };

    /**
     * Returns true if landscape.
     *
     * @returns {Boolean}
     */
    module.landscape = function () {
        return $(window).height() < $(window).width();
    };

    /**
     * Returns true if portrait.
     *
     * @returns {Boolean}
     */
    module.portrait = function () {
        return !module.landscape();
    };

    /**
     * allows designers to add a custom (tile) class.
     * if class name is already taken, the original class is overwritten.
     *
     * @param {string} name
     * @param {object} defn
     * @returns defn
     */
    module.addClass = function (name, defn) {
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
    module.findClass = function (typeName, prefix, defaultClass) {
        var className = _.capitalize(prefix || '') + _.capitalize(typeName || '');
        return App.core[className] || defaultClass;
    };

    /**
     * $.fn.css() cannot translate 8-code hex to rgba.
     *
     * @param {string} hexColor   e.g. '#abcdef'
     * @param {float}  opacity    e.g. 0.5
     * @return {string}           e.g. rgba(1,2,3,opacity)
     */
    module.hex2rgba = function (hexColor, opacity) {
        return 'rgba(' + parseInt(hexColor.slice(-6, -4), 16) +
            ',' + parseInt(hexColor.slice(-4, -2), 16) +
            ',' + parseInt(hexColor.slice(-2), 16) +
            ',' + opacity + ')';
    };

    /**
     * execute param1 if any only if param2 is true
     */
    module.iff = function (fn, flag) {
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
    module.getQuery = function (name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)'),
            results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    };

    /**
     * Returns a ViewportSized Height based on the Viewport size of the browser, taking into
     * account the chrome.
     */
    module.getViewportSized = function (byWidth) {
        var height = $(window).height(),
            width = $(window).width();

        if (height >= 959 || (byWidth && width >= 1600)) {
            return 700;
        } else if (height >= 900 || (byWidth && width >= 1160)) {
            // 1160 is the Samantha Zheng number
            return 600;
        } else if (height >= 800 || (byWidth && width >= 1024)) {
            return 500;
        } else if (height > 656 || (byWidth && width >= 768)) {
            return 400;
        }
        return 300;
    };

    /**
     * Returns a formatted url for a cloudinary image
     *
     * @param {string} url
     * @param {Object} options
     *
     * @returns {Object}
     */
    module.getResizedImage = function (url, options) {
        var ratio = Math.ceil(window.devicePixelRatio * 2) / 2,
            width = Math.max(options.width || 0, App.option('minImageWidth')),
            height = Math.max(options.height || 0, App.option('minImageHeight'));
        options = {};

        // Do NOT transform animated gifs
        if (url.indexOf('.gif') > -1) {
            return url;
        }

        // Round to the nearest whole hundred pixel dimension;
        // prevents creating a ridiculous number of images.
        if ((width && !height) || width > height) {
            options.width = Math.ceil(width / 100.0) * (100 * ratio);
        } else if ((height && !width) || height > width) {
            options.height = Math.ceil(height / 100.0) * 100;
        } else {
            options.width = App.layoutEngine.width() * ratio;
        }

        options = _.extend({
            crop: 'fit',
            quality: 75
        }, options);

        if (url.indexOf('c_fit') > -1) {
            // Transformation has been applied to this url, Cloudinary is not smart
            // with these, so lets be instead.
            url = url.replace(/(\/c_fit[,_a-zA-Z0-9]+\/v.+?\/)/, '/');
        }

        url = url.replace(App.CLOUDINARY_DOMAIN, ''); // remove absolute uri
        url = $.cloudinary.url(url, options);

        return url;
    };

    /**
     * ALL CLICKS TO EXTERNAL URLS SHOULD GO THROUGH THIS FUNCTION
     * 
     * Opens url in correct window w/ tracking parameters appended & Emits tracking event
     *
     * @param {string} url
     */
    module.openUrl = function (targetUrl) {
        var windowParams = $.extend({}, $.deparam( window.location.search.substr(1) )),
            url = module.urlAddParams(targetUrl, windowParams);
        url = module.addUrlTrackingParameters(url);
        App.vent.trigger("tracking:click", url);
        window.open(url, module.openInWindow());
        return;
    };

    /**
     * Returns window target for url redirect
     *
     * @returns {string}
     */
    module.openInWindow = function () {
        return App.option("page:openInNewWindow", true) ? "_blank" : "_self";
    };

    /**
     * Returns the url parsed into components
     *
     * @param {string} url
     *
     * @returns {Object}
     */
    module.urlParse = function (url) {
        // Trick to parse url is to use location object of a-tag
        var path, port, a = document.createElement('a');
        a.href = url;
        path = a.pathname;

        // IE excludes the leading /
        if (path.length && path.charAt(0) !== '/') {
            path = '/' + path;
        }

        // Check if port is in url, because:
        // - Safari reports "0" when no port is in the href
        // - IE reports "80" when no port is in the href
        port = (url.indexOf(":" + a.port) > -1) ? a.port : "";

        // <protocol>//<hostname>:<port><pathname><search><hash>
        // hreft - complete url
        // host - <hostname>:<port>
        // origin - <protocal>//<hostname>:<port>
        return {
            'href':     a.href,
            'host':     a.host,
            'origin':   a.origin,
            'protocol': a.protocol,
            'hostname': a.hostname,
            'port':     port,
            'pathname': path, // if path, includes leading '/'
            'search':   a.search, // if search, includes leading '?'
            'hash':     a.hash // if hash, includes leading '#'
        };
    };

    /**
     * Returns the url string constructed from components
     *  - non-empty pathname must include leading '/'
     *  - non-empty search must include leading '?'
     *  - non-empty hash must incldue leading '#'
     *
     * @param {Object} url parts
     *
     * @returns {string} url
     */
    module.urlBuild = function (urlObj) {
        // <protocol>//<hostname>:<port><pathname><search><hash>
        var url = urlObj.protocol + '//' + urlObj.hostname;
        if (urlObj.port) {
            url += ':' + urlObj.port;
        }
        url += urlObj.pathname + urlObj.search + urlObj.hash;

        return url;
    };

    /**
     * Returns the url string with additional params appended to querystring
     *
     * @param {Object} url parts
     * @param {object} additional querystring parameters
     *
     * @returns {string} url
     */
    module.urlAddParams = function (url, params) {
        var urlParts, paramsObj;
        
        urlParts = module.urlParse( url );
        // use substr to remove leading '?'. ''.substr(1) returns ''
        paramsObj = $.extend({}, params, $.deparam( urlParts.search.substr(1) ));
        urlParts.search = _.isEmpty(paramsObj) ? '' : '?' + $.param( paramsObj );
        
        return module.urlBuild( urlParts );
    };

    /**
     * STUB - returns url with client tracking parameters appended
     *
     * @param {string} url
     *
     * @returns {string} url
     */
    module.addUrlTrackingParameters = function (url) {
        /* example implementation:
        var params = { 
            "utm_source":   "SecondFunnel",
            "utm_medium":   "ReferringDomains",
            "utm_campaign": "online gift guide"
        };
        return module.urlAddParams(url, params);
        */
        return url;
    };
};
