SecondFunnel.module("observable", function (observable) {
    // make new module full of transient utilities
    "use strict";

    var $document = $(document),
        $window = $(window),
        testUA = function (regex) {
            return regex.test(window.navigator.userAgent);
        };

    observable.mobile = function () {
        return ($window.width() < 768);  // 768 is set in stone now
    };
    observable.touch = function () {
        return ('ontouchstart' in document.documentElement);
    };

    observable.isAniPad = function () {
        // use of this function is highly discouraged, but you know it
        // will be used anyway
        return testUA(/ipad/i);
    };

    observable.onErrorResumeNext = function (func, context) {
        // ms.system.reactive.linq.observable.onerrorresumenext(v=vs.103)
        // the absolutely-no-errors-must-leave-this-function 'decorator'.
        // context should be the caller's 'this'.
        // arguments after context will be passed to func.
        try {
            var pArgs = Array.prototype.slice.call(arguments, 2);
            return func.apply(context || window, pArgs);
        } catch (err) {
            console.error('Exception in %O: %O', func, err);
        }
        return null;  // have a return, just to shut up jslint
    };
});