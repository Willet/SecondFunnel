describe('intentRank', function () {
    var module = SecondFunnel.intentRank,
        originalModule= $.extend({}, module);

    beforeEach(function () {
        module = $.extend({},originalModule);
        module.initialize(PAGES_INFO);
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
            //noinspection JSValidateTypes
            expect(module.options.campaign).toEqual(-5);
        });
    });

    describe('getResultsOnline', function () {
        it('should fetch content when asked to', function() {
            var results,
                done;
            function setResults(received) {
                results = received;
                done = true;
            }
            module.options.type='campaign';
            module.getResultsOnline(module.options,setResults);
            waitsFor(function() {return done},
                'fetching results', 6000);
            runs(function () {
                expect(results && results.length).toBeTruthy();
            });
        });
    });
});