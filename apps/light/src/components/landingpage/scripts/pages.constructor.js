/*global setTimeout, console, clearTimeout, setTimeout */
'use strict';

var $ = require('jquery');
require('jquery-deparam');
var _ = require('underscore');
var Marionette = require('backbone.marionette');
var Cloudinary = require('cloudinary');

var App = new Marionette.Application(),
    ev = new $.Event('remove'),
    orig = $.fn.remove;

// Return App
module.exports.App = window.App = App;

// Update the shared $, _
App.module('', require('jquery.extensions'));
App.module('', require('underscore.extensions'));

// _globals stores things that survive application reinitialization.
// it is currently used to keep reference to window's scroll and
// resize handlers so we can unbind them later.
App._globals = App._globals || {};

App.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

(function (document) {
    // relays current page parameters to all outgoing link clicks.
    // combines PAGES_INFO.urlParams (default to nothing) with the params
    // in the page url right now.

    $(document).on('click', 'a', function (ev) {
        App.utils.openUrl(ev.target.href, ev.target.target);
        return false; // stop default action
    });
}(document));

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
        debugLevel = App.options.debug = hash.charAt(hashIdx + 6);
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

(function (views) {
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
}([Marionette.View, Marionette.CompositeView, Marionette.ItemView]));

// Console welcome message
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

/**
 * Initialize cloudinary
 */
Cloudinary.config({ 'cloud_name': 'secondfunnel', 'api_key': '471718281466152' });
App.CLOUDINARY_DOMAIN = 'http://' + Cloudinary.SHARED_CDN + '/' + Cloudinary.config().cloud_name + '/image/upload/';

/**
 * Setup Application Modules
 * Order matters
 */
App.module('utils', require('pages.utils'));
App.module('core', require('pages.core'));
App.module('intentRank', require('pages.intentrank'));
App.module('core', require('pages.core.models'));
App.module('core', require('pages.core.views.tiles'));
App.module('core', require('pages.core.views.feed'));
App.module('core', require('pages.core.views'));
App.module('support', require('pages.support'));
App.module('optimizer', require('pages.optimizer'));
App.module('tracker', require('pages.tracker'));
App.module('sharing', require('pages.sharing'));
App.module('viewport', require('pages.viewport'));
App.module('router', require('pages.router'));
App.module('init', require('pages.init'));
