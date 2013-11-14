/* global $ */
// jshint -W018


var Task = function (fn) {
    "use strict";
    var deferred = new $.Deferred(), self = this;

    // maps (fn) with (data) whenever the page is doing nothing.
    this.map = function (data, timeout) {
        var results = new Array(data.length),
            time = 0,
            i = 0,

            mapper = function (i) {
                // setTimeouts are singly queued up anyway, so
                // they are always executed in order
                var start = new Date().getTime();
                try {
                    results[i] = fn.apply(self, [data[i], i]);
                } catch (e) {  // dummify result with undefined
                    deferred.reject(e, results);
                }

                time = ((time * i) +  // average runtime
                        (new Date().getTime() - start)) / (i + 1);
                if (i === data.length - 1) {  // last item done
                    return deferred.resolve(results);
                }
            };

        for(i = 0; i < data.length; i++) {
            (function(_i) {
                setTimeout(function() {
                    mapper(_i);
                }, i * Math.max(time, timeout, 1));

            }(i));
        }
        return deferred.promise();
    };
};
