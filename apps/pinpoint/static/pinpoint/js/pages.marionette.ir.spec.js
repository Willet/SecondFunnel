describe('intentRank', function () {
    // tested for campaigns

    var module = SecondFunnel.intentRank,
        originalModule= $.extend({}, module),
        results, // to test fetching content
        done, // to test fetching content
        setResults = function (received) {
            results = received;
            done = true;
        }

    beforeEach(function () {
        // restore original state
        module = $.extend({},originalModule);
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

    describe('getResultsOnline', function () {
        it('should fetch content when asked to', function() {
            module.getResultsOnline(module.options,setResults);
            waitsFor(function() {return done},
                'fetching results', 6000);
            runs(function () {
                expect(results && results.length).toBeTruthy();
            });
        });

        it('should fetch n results when told to', function() {
            function setResults(received) {
                results = received;
                done = true;
            }
            module.options.IRResultsCount = 4;
            module.getResultsOnline(module.options,setResults);

            waitsFor(function() {return done},
                'fetching results', 6000);
            runs(function() {
                expect(results && results.length).toBe(4);
            });
        });

        it('should use its backup results if it does not receive anything from the server', function() {
            function test_fn () {
                module.base_url = 1;
                module.getResultsOnline(module.options,setResults);
                waitsFor(function() {return done},
                    'fetching backup results',500);
                runs(function() {
                    expect(results && results.length).toBeTruthy();
                    console.log(results);
                });
            }
            module.getResultsOnline(module.options,test_fn);
            waitsFor(function() {return done})
        });
    });
});