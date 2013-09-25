/*global SecondFunnel, Backbone, Marionette, console, broadcast */
/**
 * @module support
 */
SecondFunnel.module("support", function (support, SecondFunnel) {
    // make new module full of transient utilities
    "use strict";

    var $window = $(window),
        testUA = function (regex) {
            return regex.test(window.navigator.userAgent);
        };

    /**
     * True if the system thinks the device is mobile.
     * Currently, this is just a check to see if the screen is 767px or less.
     * For a more "draconian" detection method, use `$.browser.mobile`.
     *
     * @method mobile
     * @type {Function}
     * @returns {Boolean}
     */
    support.mobile = _.memoize(function () {
        // if one day device mode can change, remove _.memoize.
        return ($window.width() < 768);  // 768 is set in stone now
    });

    /**
     * True if the browser supports touch events.
     *
     * @method touch
     * @type {Function}
     * @returns {Boolean}
     */
    support.touch = function () {
        return ('ontouchstart' in document.documentElement) ||
            $('html').hasClass('touch-enabled');
    };

    /**
     * True if the device identifies itself as an iPad.
     *
     * @method isAniPad
     * @type {Function}
     * @returns {Boolean}
     */
    support.isAniPad = function () {
        // use of this function is highly discouraged, but you know it
        // will be used anyway
        return testUA(/ipad/i);
    };

    /**
     * The absolutely-no-errors-must-leave-this-function 'decorator'.
     * arguments after context will be passed to func.
     *
     * @method failsafe
     * @param func {Function}: the method to protect.
     * @param context {object}: should be the caller's "this"
     * @returns protected function return
     */
    support.failsafe = function (func, context /*, *args */) {
        try {
            var pArgs = Array.prototype.slice.call(arguments, 2);
            return func.apply(context || window, pArgs);
        } catch (err) {
            console.error('Exception in %O: %O', func, err);
        }
        return null;  // have a return, just to shut up jslint
    };
});