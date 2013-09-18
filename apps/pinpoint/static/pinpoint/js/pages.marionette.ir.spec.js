describe('intentRank', function () {
    "use strict";
    // tested for campaigns

    var module = SecondFunnel.intentRank,
        results, // to test fetching content
        done, // to test fetching content
        setResults = function (received) {
            results = received;
            done = true;
        },
        areWeDone = function() {return done;};

    beforeEach(function () {
        // restore original state (not really but close.)
        module.initialize(PAGES_INFO);
        module.options.type='campaign';

        // reset variables used to test fetching
        results = undefined;
        done = undefined;
    });

    describe('initialize', function () {
        it('should initialize without options', function() {
            expect(module.initialize({}));
        });
    });

    describe('changeCategory', function () {

        it('should not change the category if it\'s not a number', function() {
            var oldCategory = module.options.campaign;
            module.changeCategory(' 8%f');
            expect(module.options.campaign).toEqual(oldCategory);
        });

        it('should not change the category if it\'s not present', function() {
            var oldCategory = module.options.campaign;
            module.changeCategory(-3);
            expect(module.options.campaign).toEqual(oldCategory);
        });

        it('should change the category if it\'s a number and it\'s present', function () {
            module.changeCategory(97);
            expect(module.options.campaign).toEqual(97);
            module.options.categories = [{id:-5}];
            module.changeCategory(-5);
            expect(module.options.campaign).toEqual(-5);
        });
    });

    describe('getResults', function() {
        it('should call getResultsOnline if options.page.offline is falsy', function() {
            spyOn(module,'getResultsOnline');
            var test_PAGES_INFO = $.extend(true,{},PAGES_INFO);
            test_PAGES_INFO.page.offline = false;
            module.initialize(test_PAGES_INFO);
            module.options.type='campaign';
            module.getResults(module.options,setResults);
            expect(module.getResultsOnline).toHaveBeenCalled();
        });

        it('should call getResultsOffline if options.page.offline is truthy', function () {
            spyOn(module,'getResultsOffline');
            var test_PAGES_INFO = $.extend(true,{},PAGES_INFO);
            test_PAGES_INFO.page.offline = true;
            module.initialize(test_PAGES_INFO);
            module.options.type = 'campaign';
            module.getResults(module.options,setResults);
            expect(module.getResultsOffline).toHaveBeenCalled();
        });
    });

    describe('getResultsOffline',function() {
        // TODO: tests
        it('should exists', function() {
            expect(module.getResultsOffline);
        });

        it('should pass results to callback', function() {
            module.getResultsOffline(module.options, setResults);
            waitsFor(areWeDone, 500, 'callback function to be called');
        });

        it('should fetch content when asked to', function() {
            var PAGES_INFO_test = $.extend(true,{}, PAGES_INFO);
            PAGES_INFO_test.content = ['here','goes','content'];
            module.initialize(PAGES_INFO_test);
            module.getResultsOffline(module.options, setResults);
            waitsFor(function () {return done;});
            expect(results && results.length).toBeTruthy();
        });
    });

    describe('getResultsOnline', function () {
        it('should fetch content when asked to', function() {
            module.getResultsOnline(module.options,setResults);
            waitsFor(areWeDone, 'fetching results', 6000);
            runs(function () {
                expect(results && results.length).toBeTruthy();
            });
        });

        it('should pass results to callback', function() {
            module.getResultsOnline(module.options, setResults);
            waitsFor(areWeDone, 500, 'callback function to be called');
        });

        it('should fetch 4 results when told to', function() {
            {
                var n = 4;
                module.options.IRResultsCount = n;
                module.getResultsOnline(module.options,setResults);

                waitsFor(areWeDone, 'fetching results', 6000);
                runs(function() {
                    expect(results && results.length).toBe(n);
                });
            }
        });

        it('should fetch 55 results when told to', function() {
            {
                var n = 55;
                module.options.IRResultsCount = n;
                module.getResultsOnline(module.options,setResults);

                waitsFor(areWeDone, 'fetching results', 6000);
                runs(function() {
                    expect(results && results.length).toBe(n);
                });
            }
        });

        it('should store backup results if a request is successful', function() {
            module.getResultsOnline(module.options,setResults);
            waitsFor(areWeDone);
            runs(function() {
                expect(module.options.backupResults &&
                    module.options.backupResults.length).toBeTruthy();
            });
        });

        it('should use its backup results if it does not find the server', function() {
            function test_fn () {
                module.options.baseUrl = 'fail';
                module.getResultsOnline(module.options, setResults);
                waitsFor(areWeDone, 'fetching backup results',500);
                runs(function() {
                    expect(results && results.length).toBeTruthy();
                });
            }

            // I forgot why I did this in one day. Then it came back. I wanted a successful
            // request before the failed one. So the failed request is in the callback function.
            // Why? Because we want backup results from the successful request.
            module.getResultsOnline(module.options, test_fn);
            waitsFor(areWeDone, 'fetching results', 6000);
        });

        it('should use its backup results if the request times out', function() {
            function test_fn() {
                module.options.IRTimeout = 1;
                module.getResultsOnline(module.options, setResults);
                waitsFor(areWeDone, 'fetching backup results', 500);
                runs(function() {
                    expect (results && results.length).toBeTruthy();
                });
            }

            module.getResultsOnline(module.options, test_fn);
            waitsFor(areWeDone, 'fetching results', 6000);
        });

    });
});