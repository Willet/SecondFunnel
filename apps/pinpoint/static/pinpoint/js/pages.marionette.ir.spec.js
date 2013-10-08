/*global describe, SecondFunnel, _, $, it, should, sinon, sinon, runs, waitsFor,
  beforeEach, expect, spyOn
 */

describe('intentRank', function () {
    "use strict";
    // tested for campaigns

    var module = SecondFunnel.intentRank,
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

            // TODO: not sure this actually works. Need to investigate
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

        ($.jsonp && $.jsonp.restore && $.jsonp.restore());
        ($.ajax.restore && $.ajax.restore());
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

    describe('getResults', function () {
        it('should call getResultsOnline if SecondFunnel.options.page.offline is falsy', function () {
            spyOn(module, 'getResultsOnline');
            var testOptionsPage = $.extend(true, {}, SecondFunnel.options.page);
            testOptionsPage.offline = false;
            replace(SecondFunnel.options, 'page')['with'](testOptionsPage);
            module.getResults(module.options, setResults);
            expect(module.getResultsOnline).toHaveBeenCalled();
        });

        it('should call getResultsOffline if SecondFunnel.options.page.offline is truthy', function () {
            spyOn(module, 'getResultsOffline');
            var testOptionsPage = $.extend(true, {}, SecondFunnel.options.page);
            testOptionsPage.offline = true;
            replace(SecondFunnel.options, 'page')['with'](testOptionsPage);
            module.options.type = 'campaign';
            module.getResults(module.options, setResults);
            expect(module.getResultsOffline).toHaveBeenCalled();
        });
    });

    describe('getResultsOffline', function () {
        it('should exists', function () {
            expect(module.getResultsOffline).toBeDefined();
        });

        it('should pass results to callback', function () {
            module.getResultsOffline(module.options).always(setResults);
            waitsFor(areWeDone, 500, 'callback function to be called');
        });

        it('should fetch content when asked to', function () {
            var fakeResults = ['here', 'goes', 'content'];
            replace(module.options, 'backupResults')['with'](fakeResults);
            module.getResultsOffline(module.options).always(setResults);
            waitsFor(function () {return done; });
            runs(function () {
                // assuming it does not return more items than it has stored;
                expect(results.length).toBeGreaterThan(0);
            });
        });

        it('should fetch 3 results when asked to', function () {
            var n = 3,
                fakeResults = ['here', 'goes', 'content', 'more', 'content'];
            replace(module.options, 'backupResults')['with'](fakeResults);
            replace(module.options, 'IRResultsCount')['with'](n);
            module.getResultsOffline(module.options).always(setResults);
            waitsFor(function () {return done; });
            runs(function () {
                // assuming it does not return more items than it has stored;
                expect(results.length).toEqual(3);
            });
        });
    });

    describe('getResultsOnline', function () {
        it('should pass results to callback', function () {
            module.getResultsOnline(module.options).always(setResults);
            waitsFor(areWeDone, 500, 'callback function to be called');
        });

        it('should fetch content when asked to', function () {
            sinon.stub($, 'ajax', mockAjaxSuccess);
            sinon.stub($, 'jsonp', mockAjaxSuccess);
            module.getResultsOnline(module.options).always(setResults);
            waitsFor(areWeDone, 'fetching results', 6000);
            runs(function () {
                expect(results).toEqual(expected);
            });
        });

        it('should fetch 4 results when told to', function () {
            sinon.stub($, 'ajax', mockAjaxSuccess);
            sinon.stub($, 'jsonp', mockAjaxSuccess);
            var n = 4;
            replace(module.options, 'IRResultsCount')['with'](n);
            module.getResultsOnline(module.options).always(setResults);

            waitsFor(areWeDone, 'fetching results', 6000);
            runs(function () {
                expect(results.length).toBe(n);
            });
        });

        it('should fetch 55 results when told to', function () {
            sinon.stub($, 'ajax', mockAjaxSuccess);
            sinon.stub($, 'jsonp', mockAjaxSuccess);
            var n = 55;
            replace(module.options, 'IRResultsCount')['with'](n);
            module.getResultsOnline(module.options).always(setResults);

            waitsFor(areWeDone, 'fetching results', 6000);
            runs(function () {
                expect(results.length).toBe(n);
            });
        });


        it('should use its backup results if server returns nothing', function () {
            sinon.stub($, 'ajax', mockAjaxZeroResults);
            sinon.stub($, 'jsonp', mockAjaxZeroResults);
            var backupResults = [{'backup': 'backup'}];
            replace(module.options, 'backupResults')['with'](backupResults);
            module.getResultsOnline(module.options).always(setResults);

            waitsFor(areWeDone, 'fetching backup results', 500);
            runs(function () {
                expect(results).toEqual(backupResults);

            });
        });

        it('should use its backup results if we receive an Ajax error', function () {
            sinon.stub($, 'ajax', mockAjaxError);
            sinon.stub($, 'jsonp', mockAjaxError);
            var backupResults = [{'backup': 'backup'}];
            replace(module.options, 'backupResults')['with'](backupResults);
            module.getResultsOnline(module.options).always(setResults);

            waitsFor(areWeDone, 'fetching backup results', 500);
            runs(function () {
                expect(results).toEqual(module.options.backupResults);
            });
        });
    });
});
