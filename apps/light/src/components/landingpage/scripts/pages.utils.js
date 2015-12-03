'use strict';

require('jquery-deparam');
/**
 * @module utils
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

    var $window = $(window),
        regions = {};

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
    
    /**
     * @returns <boolean> true if test is an integer or a string containing only numerals
     */
    module.isNumber = function (test) {
        return /^\d+$/.test(test);
    }

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
     * Returns the current page route iff App.option('page:slug') is defined
     * '' is a valid response
     */
    module.getRoute = function () {
        var path = window.location.pathname,
            slug = App.option('page:slug'),
            slugIndex = path.indexOf(slug),
            route = path.substring(slugIndex + slug.length);

        if (_.isString(slug) && !_.isEmpty(slug) && slugIndex !== -1) {
            route = (route.indexOf('/') === 0) ? route.substring(1) : route;
            return route;
        } else {
            return false;
        }
    }
    
    /**
     * ALL CLICKS TO EXTERNAL URLS SHOULD GO THROUGH THIS FUNCTION
     * 
     * Opens url in correct window w/ tracking parameters appended & Emits tracking event
     *
     * @param {string} url
     * @param {string} target, optional override ('_blank','_top','_parent','_self')
     */
    module.openUrl = function (url, target) {
        var windowParams = $.extend({}, $.deparam( window.location.search.substr(1) )),
            url = module.urlAddParams(url, windowParams);
        if (!_.contains(['_blank','_top','_parent','_self'], target)) {
            target = module.openInWindow();
        }
        url = module.addUrlTrackingParameters(url);
        App.vent.trigger("tracking:click", url);
        window.open(url, target);
        return;
    };
    
    /**
     * Returns window target for url redirect
     *
     * @returns {string}
     */
    module.openInWindow = function () {
        return App.option("page:openLinksInNewWindow", true) ? "_blank" : "_self";
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
     * Returns value of querystring parameter param in url, or null if not found
     *
     * @param {string} url
     * @param {string} param - name of parameter
     *
     * @returns {string} questring parameter param or null if not found
     */
    module.urlGetParam = function (url, param) {
        var urlParts,
            paramsObj = {};
        if (_.isString(url) && _.isString(param)) {
            urlParts = module.urlParse( url );
            // use substr to remove leading '?'. ''.substr(1) returns ''
            paramsObj = $.deparam(urlParts.search.substr(1));
        }
        return paramsObj[param] || null;
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
        */
        return module.urlAddParams(url, App.option("page:urlParams"));
    };
};
