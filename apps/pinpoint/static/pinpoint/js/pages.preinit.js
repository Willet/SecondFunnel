/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _,
console */
var SecondFunnel = new Marionette.Application(),
    broadcast,
    receive,
    debugOp,
    ev = new $.Event('remove'),
    orig = $.fn.remove;

SecondFunnel.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

// A ?debug value of > 1 will leak memory, and should not be used as reference
// heap sizes on production. ibm.com/developerworks/library/wa-jsmemory/#N101B0
(function (console, level, hash) {
    var hashIdx = hash.indexOf('debug=');
    try {
        // console logging thresholds
        SecondFunnel.QUIET = 0;
        SecondFunnel.ERROR = 1;
        SecondFunnel.WARNING = 2;
        SecondFunnel.LOG = 3;
        SecondFunnel.VERBOSE = 4;
        SecondFunnel.ALL = 5;

        // patch all console methods individually.
        console.debug = console.debug || $.noop;
        console.log = console.log || $.noop;
        console.warn = console.warn || $.noop;
        console.error = console.error || $.noop;

        if (window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1') {
            level = SecondFunnel.options.debug = SecondFunnel.ERROR;
        }

        if (hashIdx > -1) {
            level = SecondFunnel.options.debug = hash[hashIdx + 6];
        }

        // remove console functions depending on desired debug threshold.
        if (level < SecondFunnel.ERROR) {
            console.error = $.noop;
        }

        if (level < SecondFunnel.WARNING) {
            console.warn = $.noop;
        }

        if (level < SecondFunnel.LOG) {
            console.log = $.noop;
        }

        if (level < SecondFunnel.VERBOSE) {
            console.debug = $.noop;
        }
    } catch (e) {
        // this is an optional operation. never let this stop the script.
    }
}(window.console = window.console || {},
  SecondFunnel.options.debug,
  window.location.hash + window.location.search));

// pre-fetch images for the initial results. (shaves off a second for imagesLoaded)
(function () {
    _.each(_.pluck(SecondFunnel.options.initialResults, 'image'), function (src) {
        if (typeof src === 'string') {
            (new Image()).src = src.replace('master.jpg', 'grande.jpg');
            (new Image()).src = src.replace('master.jpg', 'large.jpg');
        }
    });
}());

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
            $this.data('scrollTimeout', setTimeout(callback, 500, self));
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

$.fn.scaleImages = $.fn.scaleImages || function () {
    // looks for .auto-scale elements and replace them with an image.
    $(this).find('img.auto-scale').each(function () {
        var $el = $(this),
            data = $el.data();
        if (data.src && data.size) {
            $el.attr('src', SecondFunnel.utils.pickImageSize(data.src, data.size));
        }
    });
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
        broadcast('deferredScriptsLoaded', urls);
    });
};

// underscore's fancy pants capitalize()
_.mixin({
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
    }
});

(function (views) {
    // View's render() is a noop. It won't trigger a NoTemplateError
    // like other views do. Here's a patch.
    Marionette.View.prototype.render = function () {
        if (!$(this.template).length) {
            function throwError(message, name) {
                var error = new Error(message);
                error.name = name || 'Error';
                throw error;
            }
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
            /*try {*/
                // call the original function
                result = oldRender.apply(this, arguments);  // usually 'this'

                // do something else
                SecondFunnel.utils.runWidgets(this);

            /*} catch (err) {
                // failed... close the view
                broadcast('viewRenderError', err, this);

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
            }*/

            // return the return of the original function, pretend nothing happened
            return result;
        };
    });
}([Marionette.View, Marionette.CompositeView, Marionette.ItemView]));

broadcast = function (eventName) {
    // alias for vent.trigger with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    console.debug('Broadcasting "' + eventName + '" with args=%O', pArgs);
    SecondFunnel.vent.trigger.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.fire(eventName, pArgs);
    }
};

/**
 * alias for vent.on with a clear intent that the event triggered
 * is NOT used by internal code (pages.js).
 * calling method: (eventName, other stuff)
 */
receive = function (eventName) {
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    console.debug('Received "' + eventName + '" with args=%O', pArgs);
    SecondFunnel.vent.on.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.on(eventName, pArgs);
    }
};

/**
 * similar usage as $.noop
 */
debugOp = function () {
    console.debug('%O, %O', this, arguments);
};

// allow jasmine to run on the campaign page if the url contains "specrunner".
(function () {
    /**
     * Sequential script getter. ($.fn.getScripts is parallel)
     * @param urls {String}: array of script urls
     * @param callback {Function}: what to do afterwards.
     */
    var getScripts = function (urls, callback) {
            var script = urls.shift();
            $.getScript(script, function () {
                if (urls.length + 1 <= 0) {
                    if (typeof callback === 'function') {
                        callback();
                    }
                } else {
                    getScripts(urls, callback);
                }
            });
        },
        runTest = function () {
            var protoSrcMaps = [
                    "/static/js/jasmine.js",
                    "/static/js/jasmine-html.js",
                    "/static/js/jasmine-console.js",
                    "/static/pinpoint/js/pages.preinit.spec.js",
                    "/static/pinpoint/js/pages.spec.js",
                    "/static/pinpoint/js/pages.support.spec.js",
                    "/static/pinpoint/js/pages.utils.spec.js",
                    "/static/pinpoint/js/pages.layoutengine.spec.js",
                    "/static/pinpoint/js/pages.viewport.spec.js"
                ],
                href = window.location.href.toLowerCase();

            if (href.indexOf('specrunner.html') > 0) {
                protoSrcMaps.push("/static/js/jasmine.specrunner.html.js");
            } else if (href.indexOf('specrunner') > 0) {
                protoSrcMaps.push("/static/js/jasmine.specrunner.console.js");
            } else {
                return;
            }

            protoSrcMaps = SecondFunnel.option('protoSrcMaps') || protoSrcMaps;

            getScripts(protoSrcMaps);
        };

    SecondFunnel.vent.on('finished', runTest);
}());