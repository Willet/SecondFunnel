'use strict';
/**
 * @module Underscore Extensions
 *
 * Patches _ object
 *
 */
module.exports = function (module, App, Backhone, Marionette, $, _) {
    var collectionContains = _.contains;
    var optimizeCb = function(func, context, argCount) {
        if (context === void 0) return func;
        switch (argCount == null ? 3 : argCount) {
          case 1: return function(value) {
            return func.call(context, value);
          };
          case 2: return function(value, other) {
            return func.call(context, value, other);
          };
          case 3: return function(value, index, collection) {
            return func.call(context, value, index, collection);
          };
          case 4: return function(accumulator, value, index, collection) {
            return func.call(context, accumulator, value, index, collection);
          };
        }
        return function() {
          return func.apply(context, arguments);
        };
    };
    var cb = function(value, context, argCount) {
        if (value == null) return _.identity;
        if (_.isFunction(value)) return optimizeCb(value, context, argCount);
        if (_.isObject(value)) return _.matcher(value);
        return _.property(value);
    };
    _.mixin({
        'buffer': function (fn, wait) {
        // a variant of _.debounce, whose called function receives an array
        // of buffered args (i.e. fn([arg, arg, arg...])
        //
        // the fn will receive only one argument.
            var args = [],
                originalContext = this,
                newFn = _.debounce(function () {
                        // newFn calls the function and clears the arg buffer
                        var result = fn.call(originalContext, args);
                        args = [];
                        return result;
                    }, wait);

            return function (arg) {
                args.push(arg);
                return newFn.call(originalContext, args);
            };
        },
        'capitalize': function (string) {
            // underscore's fancy pants capitalize()
            var str = string || '';
            return str.charAt(0).toUpperCase() + str.substring(1);
        },
        'get': function (obj, key, defaultValue) {
            // thin wrapper around obj key access that never throws an error.
            try {
                var val = obj[key];
                if (val !== undefined) {
                    return val;
                }
            } catch (err) {
                // default
            }
            return defaultValue;
        },
        'uniqBy': function (obj, key) {  // shorthand
            return _.uniq(obj, false, function (x) {
                return x[key];
            });
        },
        'truncate': function (string, n, useWordBoundary, addEllipses) {
            // truncate string at boundary
            // http://stackoverflow.com/questions/1199352/
            if (!_.isString(string)) {
                return "";
            }
            var tooLong = string.length > n,
                s = tooLong ? string.substr(0, n) : string;
            if (tooLong && useWordBoundary && s.lastIndexOf(' ') > -1) {
                if (addEllipses) {
                    s = s.substr(0, s.length - 3)
                    s = s.substr(0, s.lastIndexOf(' ')) + '...';
                }
                else {
                    s = s.substr(0, s.lastIndexOf(' ') + 1);
                }
            }
            else if (tooLong && addEllipses) {
                s = s.substr(0, s.length - 3) + '...';
            }
            return s;
        },
        // overloads contains to handle {String} and {Obj}
        'contains': function(collection_or_str, needle) {
            if (_.isString(collection_or_str)) {
                if (needle === '') return true;
                return collection_or_str.indexOf(needle) !== -1;
            } else {
                return collectionContains(collection_or_str, needle);
            }
        }
    });
};
