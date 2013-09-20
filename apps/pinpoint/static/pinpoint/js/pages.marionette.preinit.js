/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _, Willet */
// JSLint/Emacs js2-mode directive to stop global 'undefined' warnings.

var SecondFunnel = new Backbone.Marionette.Application(),
    broadcast,
    receive,
    debugOp,
    ev = new $.Event('remove'),
    orig = $.fn.remove;

SecondFunnel.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

// A ?debug value of > 1 will leak memory, and should not be used as reference
// heap sizes on production. ibm.com/developerworks/library/wa-jsmemory/#N101B0
if (!window.console) {  // shut up JSLint / good practice
    var console = window.console = {
        log: $.noop,
        warn: $.noop,
        error: $.noop
    };
}

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

$.fn.scrollable = function (yesOrNo) {
    // make an element scrollable on mobile.
    if (SecondFunnel.support.mobile() || SecondFunnel.support.touch()) {
        var $el = $(this),  // warning: multiple selectors
            $html = $('html'),
            $body = $('body'),
            scrollPosition;

        if (yesOrNo) {  // lock
            scrollPosition = [
                self.pageXOffset || document.documentElement.scrollLeft || document.body.scrollLeft,
                self.pageYOffset || document.documentElement.scrollTop  || document.body.scrollTop
            ];

            $html.data({
                'scroll-position': scrollPosition,
                'previous-overflow': $html.css('overflow')
            });

            $html.css({
                'overflow': 'hidden',
                'height': '100%'
            });

            $body.data({
                'previous-overflow': $body.css('overflow'),
                'previous-overflow-y': $body.css('overflow-y')
            });
            $body.css({
                'overflow': 'hidden',
                'overflow-y': 'hidden',
                'height': '100%'
            });

            $el
                .height(1.2 * $(window).height())
                .css('max-height', '100%');

        } else {
            scrollPosition = $html.data('scroll-position');

            $html.css({
                'overflow': $html.data('previous-overflow'),
                'height': 'auto'
            });
            $body.css({
                'overflow': $body.data('previous-overflow'),
                'overflow-y': $html.data('previous-overflow-y'),
                'height': 'auto'
            });
        }
        window.scrollTo(scrollPosition[0], scrollPosition[1]);
    }
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
    Backbone.Marionette.View.prototype.render = function () {
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
            try {
                // call the original function
                result = oldRender.apply(this, arguments);  // usually 'this'

                // do something else
                SecondFunnel.utils.runWidgets(this);

            } catch (err) {
                // failed... close the view
                broadcast('viewRenderError', err, this);

                // If template not found signal error in rendering view.
                if (err.name &&  err.name === "NoTemplateError") {
                    if (SecondFunnel.option('debug', SecondFunnel.QUIET) >=
                        SecondFunnel.WARNING) {
                        console.warn("Could not find template " +
                                     this.template + ". View did not render.");
                    }
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
}([Backbone.Marionette.View,
   Backbone.Marionette.CompositeView,
   Backbone.Marionette.ItemView]));

broadcast = function () {
    // alias for vent.trigger with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    if (SecondFunnel.option('debug') >= SecondFunnel.LOG) {
        console.log('Broadcasting "' + arguments[0] + '" with args=%O', pArgs);
    }
    SecondFunnel.vent.trigger.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.fire(arguments[0], pArgs);
    }
};

/**
 * alias for vent.on with a clear intent that the event triggered
 * is NOT used by internal code (pages.js).
 * calling method: (eventName, other stuff)
 */
receive = function () {
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    if (SecondFunnel.option('debug') >= SecondFunnel.LOG) {
        console.log('Received "' + arguments[0] + '" with args=%O', pArgs);
    }
    SecondFunnel.vent.on.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.on(arguments[0], pArgs);
    }
};

/**
 * similar usage as $.noop
 */
debugOp = function () {
    console.log('%O, %O', this, arguments);
};

// allow jasmine to run on the campaign page if the url contains "specrunner".
// not an initializer (too late)
(function () {
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
                    "/static/testing/lib/jasmine-1.3.1/jasmine.js",
                    "/static/testing/lib/jasmine-1.3.1/jasmine-html.js",
                    "/static/testing/lib/jasmine-1.3.1/jasmine-console.js",
                    "/static/pinpoint/js/pages.marionette.preinit.spec.js",
                    "/static/pinpoint/js/pages.marionette.spec.js",
                    "/static/pinpoint/js/pages.marionette.support.spec.js",
                    "/static/pinpoint/js/pages.marionette.utils.spec.js",
                    "/static/pinpoint/js/pages.marionette.layoutengine.spec.js",
                    "/static/pinpoint/js/pages.marionette.viewport.spec.js"
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
            // return _.each(protoSrcMaps, addScript);
            getScripts(protoSrcMaps);
        };

    SecondFunnel.vent.on('finished', runTest);
}());