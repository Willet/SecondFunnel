SecondFunnel.module("support", function (support, SecondFunnel) {
    // make new module full of transient utilities
    "use strict";

    var $window = $(window),
        testUA = function (regex) {
            return regex.test(window.navigator.userAgent);
        };

    support.mobile = _.memoize(function () {
        // if one day device mode can change, remove _.memoize.
        return ($window.width() < 768);  // 768 is set in stone now
    });
    support.touch = function () {
        return ('ontouchstart' in document.documentElement) ||
            $('html').hasClass('touch-enabled');
    };

    support.isAniPad = function () {
        // use of this function is highly discouraged, but you know it
        // will be used anyway
        return testUA(/ipad/i);
    };

    support.failsafe = function (func, context /*, *args */) {
        // the absolutely-no-errors-must-leave-this-function 'decorator'.
        // context should be the caller's 'this'.
        // arguments after context will be passed to func.
        try {
            var pArgs = Array.prototype.slice.call(arguments, 2);
            return func.apply(context || window, pArgs);
        } catch (err) {
            if (SecondFunnel.option('debug', SecondFunnel.QUIET) >= SecondFunnel.ERROR) {
                console.error('Exception in %O: %O', func, err);
            }
        }
        return null;  // have a return, just to shut up jslint
    };
});