/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _, Willet */
// JSLint/Emacs js2-mode directive to stop global 'undefined' warnings.

var SecondFunnel = new Backbone.Marionette.Application(),
    broadcast,
    receive,
    debugOp,
    ev = new $.Event('remove'),
    orig = $.fn.remove;

// A ?debug value of > 1 will leak memory, and should not be used as reference
// heap sizes on production. ibm.com/developerworks/library/wa-jsmemory/#N101B0
if (!window.console) {  // shut up JSLint / good practice
    var console = window.console = {
        log: $.noop,
        warn: $.noop,
        error: $.noop
    };
}

// http://stackoverflow.com/questions/1199352/smart-way-to-shorten-long-strings-with-javascript/1199420#1199420
String.prototype.truncate = function (n, useSentenceBoundary, addEllipses) {
    var tooLong = this.length > n,
        s = tooLong ? this.substr(0, n - 1) : this;
    if (useSentenceBoundary && tooLong) {
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

$.fn.scrollStopped = function (callback) {
    // stackoverflow.com/a/14035162/1558430
    $(this).scroll(function () {
        var self = this, $this = $(self);
        if ($this.data('scrollTimeout')) {
            clearTimeout($this.data('scrollTimeout'));
        }
        $this.data('scrollTimeout', setTimeout(callback, 500, self));
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
        options = $.extend(options || {}, {
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
        string = string || "";
        return string.charAt(0).toUpperCase() + string.substring(1).toLowerCase();
    },
    'get': function (obj, key) {
        // thin wrapper around obj key access that never throws an error.
        try {
            return obj[key];
        } catch (err) {
            return undefined;
        }
    }
});

(function (views) {
    // patch render to always run widgets.
    _.each(views, function (ViewClass) {
        var oldRender = ViewClass.prototype.render;
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
                    this.triggerMethod("missing:template", this);
                }

                this.close();
            }

            // return the return of the original function, pretend nothing happened
            return result;
        };
    });
}([Backbone.Marionette.View,
   Backbone.Marionette.CollectionView,
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

receive = function () {
    // alias for vent.on with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
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

debugOp = function () {
    console.log('%O, %O', this, arguments);
};

// not an initializer (too late)
$(document).ready(function () {
    if (window.jasmine) {
        var jasmineEnv = jasmine.getEnv();
        jasmineEnv.updateInterval = 1000;

        var htmlReporter = new jasmine.HtmlReporter();

        jasmineEnv.addReporter(htmlReporter);

        jasmineEnv.specFilter = function (spec) {
            return htmlReporter.specFilter(spec);
        };

        jasmineEnv.execute();
    }
});