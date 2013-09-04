/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _, Willet */
// JSLint/Emacs js2-mode directive to stop global 'undefined' warnings.

var SecondFunnel,
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
String.prototype.truncate = function (n, useSentenceBoundary) {
    var toLong = this.length > n,
        s = toLong ? this.substr(0, n - 1) : this;
    s = useSentenceBoundary && toLong? s.substr(0, s.lastIndexOf('. ') + 1): s;
    return  s;
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

$.fn.scrollable = $.fn.scrollable || function (yesOrNo) {
    // make an element scrollable on mobile.
    if (SecondFunnel.observable.touch()) { //if touch events exist...
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

            $body.data('previous-overflow', $body.css('overflow'));
            $body.css({
                'overflow': 'hidden',
                'height': '100%'
            });

            $el
                .height(1.5 * $(window).height())
                .css('max-height', '100%');

        } else {
            scrollPosition = $html.data('scroll-position');

            $html.css({
                'overflow': $html.data('previous-overflow'),
                'height': 'auto'
            });
            $body.css({
                'overflow': $body.data('previous-overflow'),
                'height': 'auto'
            });
        }
        window.scrollTo(scrollPosition[0], scrollPosition[1]);
    }
};

$.fn.getClasses = $.fn.getClasses || function () {
    // random helper. get an element's list of classes.
    // example output: ['facebook', 'button']
    return _.compact($(this).attr('class').split(' ').map($.trim));
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
        return string.charAt(0).toUpperCase() + string.substring(1).toLowerCase();
    }
});

broadcast = function () {
    // alias for vent.trigger with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    if (SecondFunnel.option('debug') > 2) {
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
    if (SecondFunnel.option('debug') > 2) {
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