/*global describe, App, _, $, it, should, sinon, sinon, runs, waitsFor,
  beforeEach, expect, spyOn
 */

describe('intentRank', function () {
    "use strict";
    // tested for campaigns

    var module = App.intentRank,
        results, // to test fetching content
        done, // to test fetching content
        expected, // to test fetching content
        setResults = function (received) {
            results = received;
            done = true;
        },
        areWeDone = function () {return done; },
        delay = 100,
        replaced = [], // used to reset state

        // Probably not necessary, but I can't help it
        // How to use:
        // replace(object.property)['with'](replacement)
        // reset() restores original

        replace = function (object, property) {
            var _orig = object[property];
            return {
                'with': function (replacement) {
                    replaced.unshift({'object': object, 'property':
                        property, 'orig': _orig});
                    object[property] = replacement;
                    return object[property];
                }
            };
        },

        reset = function () {
            if (replaced.length) {
                _.each(replaced, function (element, index, list) {
                    element.object[element.property] = element.orig;
                });
            }
            replaced = [];
        },

        mockAjaxSuccess = function (parameters) {
            var results = [],
                deferred = new $.Deferred(),
                i;
            for (i = 0; i < parameters.data.results; ++i) {
                results.push({});
            }
            expected = results;
            // make it asynchronous
            if (parameters.success) {
                setTimeout(function () {parameters.success(results); }, delay);
            }
            setTimeout(function () {deferred.resolve(results); }, delay);
            return deferred.promise();
        },

        mockAjaxZeroResults = function (parameters) {
            var results = [],
                deferred = new $.Deferred();
            // make it asynchronous
            if (parameters.success) {
                setTimeout(function () {parameters.success(results); }, delay);
            }
            setTimeout(function () {deferred.resolve(results); }, delay);
            return deferred.promise();
        },

        mockAjaxError = function (parameters) {
            var deferred = new $.Deferred();

            // make it asynchronous
            if (parameters.success) {
                setTimeout(function () {parameters.error('jqXHR', 'textStatus', 'errorThrown'); }, delay);
            }
            setTimeout(function () {deferred.reject('jqXHR', 'textStatus', 'errorThrown'); }, delay);

            return deferred.promise();
        };

    beforeEach(function () {
        // restore original state (not really but close.)
        reset();

        //campaign mode
        module.options.type = 'campaign';

        // reset variables used to test fetching
        results = undefined;
        done = undefined;
        expected = undefined;

        if ($.jsonp && $.jsonp.restore) {
            $.jsonp.restore();
        }
        if ($.ajax.restore) {
            $.ajax.restore();
        }
    });

    describe('changeCategory', function () {

        it('should not change the category if it\'s not a number', function () {
            var oldCategory = module.options.campaign;
            module.changeCategory('don\'t');
            expect(module.options.campaign).toEqual(oldCategory);
            module.changeCategory('');
            expect(module.options.campaign).toEqual(oldCategory);
        });

        it('should not change the category if it\'s legal but not valid (not meant for this campaign)', function () {
            var oldCategory = module.options.campaign;
            module.changeCategory(3);
            expect(module.options.campaign).toEqual(oldCategory);
        });

        it('should change the category if it\'s a number and it\'s present', function () {
            module.changeCategory(97);
            expect(module.options.campaign).toEqual(97);
            module.options.categories = [{id: -5}];
            module.changeCategory(-5);
            expect(module.options.campaign).toEqual(-5);
        });
    });
});
