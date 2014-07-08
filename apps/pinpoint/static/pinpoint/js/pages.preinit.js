/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _,
console, location, clearTimeout, setTimeout */
var App = new Marionette.Application(),
    SecondFunnel = App,  // old alias
    ev = new $.Event('remove'),
    orig = $.fn.remove;

// Production steps of ECMA-262, Edition 5, 15.4.4.18
// Reference: http://es5.github.com/#x15.4.4.18
if (!Array.prototype.forEach) {

  Array.prototype.forEach = function (callback, thisArg) {

    var T, k;

    if (this == null) {
      throw new TypeError(" this is null or not defined");
    }

    // 1. Let O be the result of calling ToObject passing the |this| value as the argument.
    var O = Object(this);

    // 2. Let lenValue be the result of calling the Get internal method of O with the argument "length".
    // 3. Let len be ToUint32(lenValue).
    var len = O.length >>> 0;

    // 4. If IsCallable(callback) is false, throw a TypeError exception.
    // See: http://es5.github.com/#x9.11
    if (typeof callback !== "function") {
      throw new TypeError(callback + " is not a function");
    }

    // 5. If thisArg was supplied, let T be thisArg; else let T be undefined.
    if (thisArg) {
      T = thisArg;
    }

    // 6. Let k be 0
    k = 0;

    // 7. Repeat, while k < len
    while (k < len) {

      var kValue;

      // a. Let Pk be ToString(k).
      //   This is implicit for LHS operands of the in operator
      // b. Let kPresent be the result of calling the HasProperty internal method of O with argument Pk.
      //   This step can be combined with c
      // c. If kPresent is true, then
      if (k in O) {

        // i. Let kValue be the result of calling the Get internal method of O with argument Pk.
        kValue = O[k];

        // ii. Call the Call internal method of callback with T as the this value and
        // argument list containing kValue, k, and O.
        callback.call(T, kValue, k, O);
      }
      // d. Increase k by 1.
      k++;
    }
    // 8. return undefined
  };
}

// _globals stores things that survive application reinitialization.
// it is currently used to keep reference to window's scroll and
// resize handlers so we can unbind them later.
App._globals = App._globals || {};

App.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

(function (document) {
    "use strict";
    // relays current page parameters to all outgoing link clicks.
    // combines PAGES_INFO.urlParams (default to nothing) with the params
    // in the page url right now.
    var params = {},
        search = window.location.search,
        defaultParams = App.options.urlParams || {};

    if (search && search.length && search[0] === '?') {
        search = search.substr(1);
        params = $.deparam(search);
    }

    // :type object
    params = $.extend({}, defaultParams, params);

    App.options.urlParams = '?' + $.param(params);

    $(document).on('click', 'a', function(ev) {
        var $target = $(ev.target),
            urlParams = App.options.urlParams,
            href;
        if (!$.isEmptyObject(urlParams)) {
            href = $target.attr('href');
            if (href && href.indexOf('#') === -1 &&  // no hashes in the url
                href.indexOf(urlParams.substring(1)) === -1) {  // params not already in the url
                if (href.indexOf('?') > -1) {
                    // extend existing params
                    href += urlParams.replace('?', '&');
                } else {
                    // attach params
                    href += urlParams;
                }
                $target.attr('href', href);
            }
        }
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
    "use strict";
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
        debugLevel = level,
        urlParams = App.options.urlParams;
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
    window.devicePixelRatio = window.devicePixelRatio || 1;

    // removes the 'debug' param from all outgoing urls.
    hashIdx = hash.indexOf('debug=');
    if (hashIdx > -1) {
        debugLevel = App.options.debug = hash[hashIdx + 6];
        hashIdx = urlParams.indexOf('debug='); // In case there was a hash present
        urlParams = urlParams.replace(urlParams.substr(hashIdx - 1, hashIdx + 8), '');
        if (urlParams.indexOf('?') === -1) {
            App.options.urlParams = '?' + urlParams.substring(1);
        } else {
            App.options.urlParams = urlParams;
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


/**
 * Special jQuery listener for rotation events.  A rotation event occurs
 * when the orientation of the page triggers.  A rotation can also be triggered
 * by the user.
 */
(function ($) {
    "use strict";
    if ($ === undefined) {
        return;
    }
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
        "use strict";
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
        if (!$(this.template).length) {
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
            try {
                // call the original function
                result = oldRender.apply(this, arguments);  // usually 'this'
            } catch (err) {
                // failed... close the view
                App.vent.trigger('viewRenderError', err, this);

                // If template not found signal error in rendering view.
                if (err.name &&  err.name === 'NoTemplateError') {
                    console.warn('Could not find template ' +
                            this.template + '. View did not render.');
                    // Trigger methods
                    this.isClosed = true;
                    // .triggerMethod only triggers methods defined in prototype
                    this.triggerMethod('missing:template');
                } else {
                    this.triggerMethod('render:error', err);
                }

                this.close();
            }

            // return the return of the original function, pretend nothing happened
            return result;
        };
    });
}([Marionette.View, Marionette.CompositeView, Marionette.ItemView]));

/**
 * Initialize cloudinary
 */
$.cloudinary.config({ cloud_name: 'secondfunnel', api_key: '471718281466152' });
App.CLOUDINARY_DOMAIN = "http://" + $.cloudinary.SHARED_CDN + "/" + $.cloudinary.config().cloud_name + "/image/upload/";
