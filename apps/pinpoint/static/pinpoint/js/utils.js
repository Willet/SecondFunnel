var cache = (function () {
    var get, set, hasLocalStorage, localData = {};

    hasLocalStorage = function () {
        try {
            return 'localStorage' in window && window['localStorage'] !== null;
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

var api = (function () {
    var uris = {
        'video_gdata': "https://gdata.youtube.com/feeds/api/videos/%object_id%?v=2&alt=json-in-script&callback=?"
    }, getProduct, getProducts, fetchProduct;

    getObject = function (object_type, object_id, callback) {
        var object;

        if (object_id === undefined || object_type === undefined) {
            callback(false);
            return;
        }

        object = cache.get(object_type + "_" + object_id);

        if (object === null) {
            fetchObject(object_type, object_id, callback);
        } else {
            callback(object);
        }
    };

    getObjects = function (object_type, object_ids, step, callback) {
        var result = [];

        if (object_ids.length == 0) {
            callback(result);
        }

        _.each(object_ids, function (object_id) {
            getObject(object_type, object_id, function (object) {
                result.push(object);

                step(result.length, object_ids.length);

                if (result.length == object_ids.length) {
                    callback(result);
                }
            });
        });
    };

    fetchObject = function (object_type, object_id, callback) {
        var dataType = (object_type == "video_gdata") ? "jsonp" : "json";
        $.ajax({
            url: uris[object_type].replace("%object_id%", object_id),
            dataType: dataType,
            success: function (data) {
                cache.set(object_type + "_" + object_id, data);

                if (object_type == "product") {
                    $.ajax({
                        url: uris.products_media.replace("%object_id%", object_id),
                        dataType: "json",
                        success: function (data) {
                            var prod = cache.get(object_type + "_" + object_id);

                            if (data.meta.total_count > 0) {
                                prod.media = data.objects[0];
                                cache.set(object_type + "_" + object_id, prod);
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
}());