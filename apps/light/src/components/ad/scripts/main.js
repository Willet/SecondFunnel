/*global setTimeout, console, clearTimeout, setTimeout */
'use strict';

var $ = require('jquery');
var _ = require('underscore');
var deparam = require('jquery-deparam');
var Marionette = require('backbone.marionette');
var Cloudinary = require('cloudinary');

exports.App = new Marionette.Application();
var App = exports.App,
    ev = new $.Event('remove'),
    orig = $.fn.remove;

window.App = App; // add to window
window.SecondFunnel = App; // old alias

// _globals stores things that survive application reinitialization.
// it is currently used to keep reference to window's scroll and
// resize handlers so we can unbind them later.
App._globals = App._globals || {};

App.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

(function (document) {
    // relays current page parameters to all outgoing link clicks.
    // combines PAGES_INFO.urlParams (default to nothing) with the params
    // in the page url right now.
    var pageParams = {},
        search = window.location.search,
        campaignParams = App.options.urlParams || {},
        urlParse = function (url) {
            var a = document.createElement('a'),
                search = '';
            a.href = url;

            if (a.search) {
                search = a.search.substr(1);  // remove '?'
            }

            return {
                'href': a.href,
                'host': a.host,
                'hostname': a.hostname,
                'pathname': a.pathname,
                'search': search,
                'hash': a.hash,
                'protocol': a.protocol + "//"
            };
        };

    if (search && search.length && search[0] === '?') {
        search = search.substr(1);
        pageParams = deparam(search);
    }

    // :type object
    pageParams = $.extend({}, pageParams, campaignParams);

    App.options.urlParams = pageParams;

    $(document).on('click', 'a', function (ev) {
        var $target = $(ev.target),
            href = $target.attr('href'),
            parts = urlParse(href),
            params = $.extend({}, deparam(parts.search), App.options.urlParams || {}),
            paramStr = $.param(params);

        if (paramStr) {
            paramStr = "?" + paramStr;
        }

        href = parts.protocol +  // http://
               parts.host +      // google.com:80
               parts.pathname +  // /foobar?
               paramStr +   // baz=kek
               parts.hash;  // #hello
        $target.attr('href', href);
    });
}(document));

(function (details) {
    var pubDate;
    if (details && details.page && details.page.pubDate) {
        pubDate = details.page.pubDate;
    }

    // feature, not a bug
    if (window.console && console.log) {
        console.log('%cSecondFunnel', 'font-family:sans-serif; font-weight:bold; font-size:12pt;');
        console.log('Published ' + pubDate);
    }
}(App.options));

(function (window) {
    /* https://app.asana.com/0/9719124443216/11060830366388
     * Add ability to view feed in popular order using not
     * http://test-gap.secondfunnel.com/livedin?algorithm=popular
     * but
     * http://test-gap.secondfunnel.com/livedin?popular
     */
    try {
        if (window !== undefined &&
            window.location &&
            window.location.search &&
            window.location.search.indexOf &&
            typeof window.location.search.indexOf === 'function' &&
            window.location.search.indexOf('popular') &&
            window.location.search.indexOf('?popular') > -1 &&
            window.location.search.indexOf('&popular') === -1) {
            if (window.PAGES_INFO &&
                typeof window.PAGES_INFO === 'object') {
                window.PAGES_INFO.IRAlgo = 'popular';
            }
            if (window.App && window.App.options) {
                // PAGES_INFO was read before this block; need to read again
                App.options.IRAlgo = 'popular';
            }
        }
    } catch (err) {
        // fail silently
    }
}(window || {}));

// A ?debug value of 1 will leak memory, and should not be used as reference
// heap sizes on production. ibm.com/developerworks/library/wa-jsmemory/#N101B0
(function (level, hash) {
    var hashIdx,
        debugLevel = level;
    // console logging thresholds
    App.QUIET = 0;
    App.ALL = 5;

    window.console = window.console || {};

    // patch all console methods individually.
    _(['log', 'debug', 'warn', 'error']).each(function (method) {
        window.console[method] = window.console[method] || function (wat) {
            // actually... if console.log exists, use it anyway
            if (method !== 'log' &&
                typeof window.console.log === 'function' ||
                typeof window.console.log === 'object') {
                window.console.log(wat);
            }
        };
    });

    // IE8 has this as undefined
    if (!window.devicePixelRatio) {
        window.devicePixelRatio = 1;
    }

    // removes the 'debug' param from all outgoing urls.
    hashIdx = hash.indexOf('debug=');
    if (hashIdx > -1) {
        debugLevel = App.options.debug = hash[hashIdx + 6];
        if (App.options.urlParams && App.options.urlParams.debug) {
            delete App.options.urlParams.debug;
        }
    } else {
        debugLevel = 0;
    }

    // remove console functions depending on desired debug threshold.
    if (debugLevel < (App.QUIET + 1)) {
        console.log = $.noop;
        console.debug = $.noop;
    }
}(App.options.debug, window.location.hash + window.location.search));

// As implemented, will break in IE9
// Need a smarter way to determine if we can use console.debug
//(function (original) {
//    // make vent.trigger display debug messages.
//    App.vent.trigger = function (eventName) {
//        console.debug('App.vent.trigger(' + eventName + '): %o',
//            _.rest(arguments));
//        return original.apply(App.vent, arguments);
//    };
//}(App.vent.trigger));

// http://stackoverflow.com/questions/1199352/
String.prototype.truncate = function (n, useSentenceBoundary, addEllipses) {
    var tooLong = this.length > n,
        s = tooLong ? this.substr(0, n) : this;
    if (tooLong && useSentenceBoundary && s.lastIndexOf('. ') > -1) {
        s = s.substr(0, s.lastIndexOf('. ') + 1);
    }
    if (tooLong && addEllipses) {
        s = s.substr(0, s.length - 3) + '...';
    }
    return s;
};

/**
 * https://gist.github.com/mrdoob/838785 (modified)
 * Provides requestAnimationFrame in a cross browser way.
 * @author paulirish / http://paulirish.com/
 */
if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = window.webkitRequestAnimationFrame ||
        window.mozRequestAnimationFrame || window.oRequestAnimationFrame ||
        window.msRequestAnimationFrame || function (callback, element) {
            void(element);
            // precomputed value for 60fps: 1000/60 = 16.6667
            window.setTimeout(callback, 16.6667);
        };
}

// JQuery Special event to listen to delete
// stackoverflow.com/questions/2200494
// does not work with jQuery UI
// does not work when affected by html(), replace(), replaceWith(), ...
$.fn.remove = function () {
    $(this).trigger(ev);
    if (orig) {
        return orig.apply(this, arguments);
    } else {
        return $(this);
    }
};

/**
 * @param {function} callback
 */
$.fn.scrollStopped = function (callback) {
    // stackoverflow.com/a/14035162/1558430
    $(this).scroll(function () {
        var self = this, $this = $(self);
        if ($this.data('scrollTimeout')) {
            clearTimeout($this.data('scrollTimeout'));
        }
        if (callback) {
            $this.data('scrollTimeout', setTimeout(callback, 60, self));
        }
    });
};

/**
 * Hides this page element, then shows another page element in place.
 * This is very similar to what JQM does.
 *
 * @param showWhich {jQuery}   selected page
 * @returns {jQuery}
 */
$.fn.swapWith = function (showWhich) {
    showWhich.css('display', showWhich.data('display') || 'block');
    this.data('offset', $(window).scrollTop()).css('display', 'none');
    $(window).scrollTop(showWhich.data('offset') || 0);

    return this;
};

$.fn.getClasses = $.fn.getClasses || function () {
    // random helper. get an element's list of classes.
    // example output: ['facebook', 'button']
    return _.compact(_.map($(this).attr('class').split(' '), $.trim));
};


(function ($) {
    /**
     * Special jQuery listener for rotation events.  A rotation event occurs
     * when the orientation of the page triggers.  A rotation can also be triggered
     * by the user.
     */
    var listener,
        $window = $(window);
    // On iOS devices, orientationchange does not exist, so we have to
    // listen for resize.  Similarly, the use of orientationchange is not
    // standard.  Reference: http://stackoverflow.com/questions/1649086/
    if (_.has(window, "onorientationchange")) {
        listener = "orientationchange";
    } else {
        listener = 'resize';
    }

    $window.on(listener, function () {
        $window.trigger('rotate');
    });
}(window.jQuery || window.$));

/**
 * Retrieve the first selected element's TileView and Tile, if applicable.
 * Applicability largely depends on whether or not you had selected a tile.
 *
 * Due to aggressive garbage collection, these two calls may not succeed.
 * If selector did not find a tile, returns an object with undefined values.
 *
 * @return {Object}
 *
 * @type {Function}
 */
$.fn.tile = $.fn.tile || function () {
    var props = {},
        cid = this.attr('id');

    if (!(this.hasClass('tile') && cid)) {
        return props;
    }

    try {
        props.view = App.discoveryArea.currentView.children
            .findByModelCid(cid);
        // props.model = props.view.model;  // not always
    } catch (err) { }

    try {
        props.model = _.findWhere(App.discovery.collection.models,
            {'cid': cid});

        // these can be undefined.
        props.type = props.model.get('type');
        props.template = props.model.get('template');
    } catch (err) { }

    return props;
};

$.getScripts = function (urls, callback, options) {
    // batch getScript with caching
    // callback receives as many ajax xhr objects as the number of urls.

    // like getScript, this function is incompatible with scripts relying on
    // its own tag existing on the page (e.g. firebug, facebook jssdk)
    var calls = _.map(urls, function (url) {
        var options = $.extend(options || {}, {
                'dataType': 'script',
                'crossDomain': true,
                'cache': true,
                'url': url
            });
        return $.ajax(options);
    });
    $.when.apply($, calls).done(callback, function () {
        App.vent.trigger('deferredScriptsLoaded', urls);
    });
};

_.mixin({
    'buffer': function (fn, wait) {
    // a variant of _.debounce, whose called function receives an array
    // of buffered args (i.e. fn([arg, arg, arg...])
    //
    // the fn will receive only one argument.
        var args = [],
            originalContext = this,
            newFn = _.debounce(function () {
                    // newFn calls the function and clears the arg buffer
                    var result = fn.call(originalContext, args);
                    args = [];
                    return result;
                }, wait);

        return function (arg) {
            args.push(arg);
            return newFn.call(originalContext, args);
        };
    },
    'capitalize': function (string) {
        // underscore's fancy pants capitalize()
        var str = string || '';
        return str.charAt(0).toUpperCase() + str.substring(1);
    },
    'get': function (obj, key, defaultValue) {
        // thin wrapper around obj key access that never throws an error.
        try {
            var val = obj[key];
            if (val !== undefined) {
                return obj[key];
            }
        } catch (err) {
            // default
        }
        return defaultValue;
    },
    'uniqBy': function (obj, key) {  // shorthand
        return _.uniq(obj, false, function (x) {
            return x[key];
        });
    }
});

(function (App, views) {
    /**
     * View's render() is a noop. It won't trigger a NoTemplateError
     * like other Views do. Here's a patch.
     * @returns {*}
     */
    Marionette.View.prototype.render = function () {
        function throwError(message, name) {
            var error = new Error(message);
            error.name = name || 'Error';
            throw error;
        }
        if (!this.$(this.template).length) {
            throwError(this.template, 'NoTemplateError');
        }

        // default functionality: $.noop()

        return this;
    };

    // patch render to always run widgets.
    _.each(views, function (ViewClass) {
        var oldRender = ViewClass.prototype.render || $.noop;

        ViewClass.prototype.render = function () {
            var result;
            // TODO: uncomment
            //try {
                // call the original function
                result = oldRender.apply(this, arguments);  // usually 'this'
                /*
            } catch (err) {
                // failed... close the view
                App.vent.trigger('viewRenderError', err, this);
                console.error('A TEMPLATE DID NOT RENDER');
                console.error('A TEMPLATE DID NOT RENDER', err, this);

                // If template not found signal error in rendering view.
                if (err.name &&  err.name === 'NoTemplateError') {
                    console.warn('Could not find template ' +
                            this.template + '. View did not render.');
                    // Trigger methods
                    this.isClosed = true;
                    // .triggerMethod only triggers methods defined in prototype
                    this.triggerMethod('missing:template');
                } else {
                    console.warn('Error rendering template: ', this.template, err);
                    this.triggerMethod('render:error', err);
                }

                this.close();
            }
            */

            // return the return of the original function, pretend nothing happened
            return result;
        };
    });
}(App, [Marionette.View, Marionette.CompositeView, Marionette.ItemView]));

/**
 * Initialize cloudinary
 */
Cloudinary.config({ 'cloud_name': 'secondfunnel', 'api_key': '471718281466152' });
App.CLOUDINARY_DOMAIN = 'http://' + Cloudinary.SHARED_CDN + '/' + Cloudinary.config().cloud_name + '/image/upload/';



App.module('utils', require('pages.utils'));
App.module('core', require('pages.core'));
App.module('intentRank', require('pages.ir'));
App.module('core', require('pages.core.models'));
App.module('core', require('pages.core.views'));
App.module('support', require('pages.support'));
App.module('feed', require('pages.core.feed'));
App.module('optimizer', require('pages.optimizer'));
//App.module('tracker', require('pages.tracker'));
//App.module('sharing', require('pages.sharing'));
App.module('viewport', require('pages.viewport'));
//App.utils.registerWidget('gallery', '.gallery, .gallery-dots', require('pages.widget.gallery'));
App.module("scroller", require('./ad.scroller'));

var reinit = require('pages.init');
reinit.reinitialize(App);
App.start();
