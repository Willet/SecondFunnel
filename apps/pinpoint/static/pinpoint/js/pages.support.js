/*global App, Backbone, Marionette, console, $ */
/**
 * @module support
 */
App.module("support", function (module, App) {
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
     * @type {Function}
     * @returns {Boolean}
     */
    this.mobile = function () {
        return ($window.width() <= 768);  // 768 is set in stone now
    };

    /**
     * True if the browser supports touch events.
     *
     * @type {Function}
     * @returns {Boolean}
     */
    this.touch = function () {
        return ('ontouchstart' in document.documentElement) ||
            $('html').hasClass('touch-enabled');
    };

    /**
     * (basically) tests for hardware css transform.
     * @returns {boolean}
     */
    this.transform3d = function () {
        //github.com/Modernizr/Modernizr/blob/master/feature-detects/css/transforms3d.js#L20
        return (document.documentElement.webkitPerspective !== undefined);
    };

    /**
     * True if the device identifies itself as an iPad.
     *
     * @type {Function}
     * @returns {Boolean}
     */
    this.isAniPad = function () {
        // use of this function is highly discouraged, but you know it
        // will be used anyway
        return testUA(/ipad/i);
    };

    /**
     * True if the device identifies itself as an Android.
     *
     * @type {Function}
     * @returns {Boolean}
     */
    this.isAnAndroid = function () {
        // use of this function is highly discouraged, but you know it
        // will be used anyway
        return testUA(/Android/i);
    };

    /**
     * The absolutely-no-errors-must-leave-this-function 'decorator'.
     * arguments after context will be passed to func.
     *
     * @param func {Function}: the method to protect.
     * @param context {object}: should be the caller's "this"
     * @returns protected function return
     */
    this.failsafe = function (func, context /*, *args */) {
        try {
            var pArgs = Array.prototype.slice.call(arguments, 2);
            return func.apply(context || window, pArgs);
        } catch (err) {
            console.error('Exception in %O: %O', func, err);
        }
        return null;  // have a return, just to shut up jslint
    };
});
