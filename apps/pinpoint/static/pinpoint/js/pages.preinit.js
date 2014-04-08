/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _,
console, location, clearTimeout, setTimeout */
var App = new Marionette.Application(),
    SecondFunnel = App,  // old alias
    debugOp,
    ev = new $.Event('remove'),
    orig = $.fn.remove;

// _globals stores things that survive application reinitialization.
// it is currently used to keep reference to window's scroll and
// resize handlers so we can unbind them later.
App._globals = App._globals || {};

App.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

App.options.urlParams = window.location.search;

(function (document) {
    $(document).on('click', 'a', function(ev) {
        var $target = $(ev.target),
            urlParams = App.options.urlParams;
        if (urlParams.length > 0) {
            var href = $target.attr('href');
            if (href && href.indexOf('#') == -1 &&
                    href.indexOf(urlParams.substring(1)) == -1) {
                href += href.indexOf('?') > -1 ? urlParams.replace('?', '&') : urlParams;
                $target.attr('href', href);
            }
        }
    });
})(document);

(function (details) {
    var pubDate;
    if (details && details.page && details.page.pubDate) {
        pubDate = details.page.pubDate;
    }

    // feature, not a bug
    if (window.console && console.log) {
        console.log("%cSecondFunnel", "font-family:sans-serif; font-size:32pt;");
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
(function (console, level, hash) {
    var hashIdx,
        debugLevel = level,
        urlParams = App.options.urlParams;
    // console logging thresholds
    App.QUIET = 0;
    App.ALL = 5;

    // patch all console methods individually.
    _(['debug', 'log', 'warn', 'error']).each(function (method) {
        console[method] = console[method] || $.noop;
    });

    hashIdx = hash.indexOf('debug=');
    if (hashIdx > -1) {
        debugLevel = App.options.debug = hash[hashIdx + 6];
        hashIdx = urlParams.indexOf('debug='); // In case there was a hash present
        urlParams = urlParams.replace(urlParams.substr(hashIdx - 1, hashIdx + 7), '');
        if (urlParams.indexOf('?') == -1) {
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
}(window.console = window.console || {},
  App.options.debug,
  window.location.hash + window.location.search));

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

// underscore's fancy pants capitalize()
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
        var str = string || "";
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
            throwError(this.template, "NoTemplateError");
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

                // do something else
                App.utils.runWidgets(this);

            } catch (err) {
                // failed... close the view
                App.vent.trigger('viewRenderError', err, this);

                // If template not found signal error in rendering view.
                if (err.name &&  err.name === "NoTemplateError") {
                    console.warn("Could not find template " +
                                 this.template + ". View did not render.");
                    // Trigger methods
                    this.isClosed = true;
                    // .triggerMethod only triggers methods defined in prototype
                    this.triggerMethod("missing:template");
                } else {
                    this.triggerMethod("render:error", err);
                }

                this.close();
            }

            // return the return of the original function, pretend nothing happened
            return result;
        };
    });
}([Marionette.View, Marionette.CompositeView, Marionette.ItemView]));

/**
 * similar usage as $.noop
 */
debugOp = function () {
    console.debug('%O, %O', this, arguments);
};

/**
 * Initialize cloudinary
 */
$.cloudinary.config({ cloud_name: 'secondfunnel', api_key: '471718281466152' });
App.CLOUDINARY_DOMAIN = "http://" + $.cloudinary.SHARED_CDN + "/" + $.cloudinary.config().cloud_name + "/image/upload/";
