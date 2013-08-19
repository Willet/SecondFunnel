var Willet = Willet || {};

Willet.cache = (function () {
    "use strict";
    var get, set, hasLocalStorage, localData = {};

    hasLocalStorage = function () {
        try {
            return 'localStorage' in window && window.localStorage !== null;
        } catch (e) {
            return false;
        }
    };

    get = function (key) {
        if (hasLocalStorage()) {
            return JSON.parse(localStorage.getItem(key));
        }

        if (key in localData) {
            return localData[key];
        }

        return null;
    };

    set = function (key, value) {
        if (hasLocalStorage()) {
            localStorage.setItem(key, JSON.stringify(value));
        } else {
            localData[key] = value;
        }
    };

    return {
        "get": get,
        "set": set
    };
}());

Willet.mediaAPI = (function (options) {
    "use strict";
    var uris = {
            'product': "/api/assets/v1/product/%object_id%?store=%store_id%&format=json",
            'products_media': "/api/assets/v1/product_media/?store=%store_id%&product=%object_id%&format=json",
            'video': "/api/assets/v1/youtube_video/%object_id%/?format=json",
            'generic_image': "/api/assets/v1/generic_image/%object_id%/?format=json",
            'video_gdata': "https://gdata.youtube.com/feeds/api/videos/%object_id%?v=2&alt=json-in-script&callback=?"
        },

        getObject = function (object_type, object_id, callback) {
            // @param callback: a function that gets called
            //                  when everything completes
            var object;

            if (object_id === undefined || object_type === undefined) {
                callback(false);
                return;
            }

            object = Willet.cache.get(object_type + "_" + object_id);

            if (object === null) {
                fetchObject(object_type, object_id, callback);
            } else {
                callback(object);
            }
        },

        getObjects = function (object_type, object_ids, step, callback) {
            // @param step: a function that gets called every time an object
            //              arrives
            // @param callback: a function that gets called
            //                  when everything completes
            var result = [];

            if (object_ids.length === 0) {
                callback(result);
            }

            _.each(object_ids, function (object_id) {
                getObject(object_type, object_id, function (object) {
                    result.push(object);

                    step(result.length, object_ids.length);

                    if (result.length === object_ids.length) {
                        callback(result);
                    }
                });
            });
        },

        fetchObject = function (object_type, object_id, callback) {
            var dataType = (object_type === "video_gdata") ? "jsonp" : "json",
                objectURL = uris[object_type] || '';

            $.ajax({
                url: objectURL
                    .replace("%object_id%", object_id)
                    .replace("%store_id%", options.store_id),
                dataType: dataType,
                success: function (data) {
                    Willet.cache.set(object_type + "_" + object_id, data);

                    if (object_type === "product") {
                        // get the product's media (e.g. images, and err... others)
                        $.ajax({
                            url: uris.products_media.replace("%object_id%", object_id),
                            dataType: "json",
                            success: function (data) {
                                var prod = Willet.cache.get(object_type + "_" + object_id);

                                if (data.meta.total_count > 0) {
                                    prod.media = data.objects[0];
                                    Willet.cache.set(object_type + "_" + object_id, prod);
                                }

                                callback(prod);
                            }
                        });
                    } else {
                        callback(data);
                    }
                }
            });
        };

    return {
        "getObject": getObject,
        "getObjects": getObjects
    };
}(window.analyticsSettings || {}));

Willet.debug = (function (me, mediator) {
    // willet debugger. This is/was mostly code by Nicholas Terwoord.
    "use strict";
    var log_array = [],
        _log,
        _error;

    if (typeof (window.console) === 'object'
            && ((typeof (window.console.log) === 'function'
            && typeof (window.console.error) === 'function')
            || (typeof (window.console.log) === 'object' // IE
                && typeof (window.console.error) === 'object'))) {
        _log = function () {
            if (window.console.log.apply) {
                window.console.log.apply(window.console, arguments);
            } else {
                window.console.log(arguments);
            }
            log_array.push(arguments); // Add to logs
        };
        _error = function () {
            if (window.console.error.apply) {
                window.console.error.apply(window.console, arguments);
            } else {
                window.console.error(arguments);
            }
            log_array.push(arguments); // Add to logs
        };
    }

    me.logs = me.logs || function () {
        // Returns as list of all log & error items
        return log_array;
    };

    // set up a hook to let log and error be fired
    if (mediator.on) {
        mediator.on('log', _log);
        mediator.on('error', _error);
    }

    return me;
}(Willet.debug || {}, Willet.mediator));

Willet.browser = Willet.browser || {
    // default values - not meant to be used as-is
    'touch': ('ontouchstart' in document.documentElement),
    'mobile': (window.innerWidth < 768)
};