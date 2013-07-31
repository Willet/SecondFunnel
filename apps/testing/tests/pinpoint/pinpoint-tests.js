/* Tests related to the pinpoint app go here. */
var jsonData,
    // Our NSA WatchDog
    // Convention: Use watch for functions whose values you want and intercept to fake calls
    nsa = jasmine.createSpyObj("nsa", ['watch', 'intercept']),
    intercept = function() { nsa.intercept(); };

// Basic Functionality tests
describe('The Basics', function() {
    beforeEach(function(){
        nsa = jasmine.createSpyObj("nsa", ['watch', 'intercept']);
    });
        
    // IntentRank
    it('intentrank_more_results', function() {
        PAGES.intentRank.getResults(nsa.watch);

        waitsFor(function() {
            return nsa.watch.callCount > 0;
        }, "call to /intentrank/get-results to respond", 5000);

        runs(function() {
            expect(nsa.watch).toHaveBeenCalled();
        });
    });

    it('intentrank_valid_json', function() {
        PAGES.intentRank.getResults(nsa.watch);

        waitsFor(function() {
            return nsa.watch.callCount > 0;
        }, "call to /intentrank/get-results to respond", 5000);

        runs(function() {
            jsonData = nsa.watch.mostRecentCall.args[0];
            expect(jsonData).toEqual(jasmine.any(Array));
        });
    });

    it('intentrank_loading', function() {
        PAGES.setLoadingBlocks(true);
        expect(PAGES.intentRank.getResults()).toEqual(undefined);
        PAGES.setLoadingBlocks(false);
    });


    // Mediator tests
    it('mediator_on_off', function() {
        Willet.mediator = Willet.mediator.on('openEmail', intercept);
        Willet.mediator.fire('openEmail');
        expect(nsa.intercept.callCount).toEqual(1);

        Willet.autoFactory = (function () {
            function autoOpenEmail () {
                return;
            }

            return {
                'autoOpenEmail': autoOpenEmail
            };
        })();

        spyOn(Willet.autoFactory, 'autoOpenEmail').andCallFake(intercept);
        Willet.mediator.fire('openEmail');
        expect(nsa.intercept.callCount).toEqual(3);

        delete Willet.autoFactory;
        Willet.mediator.off('openEmail');
        Willet.mediator.fire('openEmail');

        expect(nsa.intercept.callCount).toEqual(3);
    });

    it('mediator_callback', function() {
        Willet.mediator.on('fake', nsa.intercept);
        expect(typeof Willet.mediator.callback("fake")).toEqual("function");
        
        Willet.mediator.callback("fake")();
        expect(nsa.intercept.callCount).toEqual(1);
        
        Willet.mediator.getResult('fake');
        expect(nsa.intercept.callCount).toEqual(2);

        Willet.mediator.off("fake");
    });

    // Tracking tests
    it('pagesTracking_initialiazed', function(){
        expect(pagesTracking.notABounce).toBeDefined();
    });
});

// Sample session tests
describe("Sample", function() {
      
    beforeEach(function(){
        nsa = jasmine.createSpyObj("nsa", ['watch', 'intercept']);
        
        spyOn(pagesTracking, 'notABounce').andCallFake(intercept);
        spyOn(PAGES.intentRank, 'updateClickStream').andCallFake(intercept);
        spyOn(PAGES.intentRank, 'updateContentStream').andCallFake(intercept);
    });

    it('session1', function(){
        // User is not a bounce
        pagesTracking.notABounce();
        PAGES.loadResults(nsa.watch, true);
        
        // Load more results below the fold
        waitsFor(function(){
            return nsa.watch.callCount > 0;
        }, 'PAGES.loadResults', 5000);

        runs(function(){
            jsonData = nsa.watch.mostRecentCall.args[0];
            expect(jsonData.error).toBeUndefined();
            expect(jsonData).toEqual(jasmine.any(Object));
            expect(jsonData.length).toBeGreaterThan(0);
        });
        
        // User clicked one of the discovery blocks
        expect(PAGES.loadResults(nsa.listen, false, true)).toEqual(undefined);
        PAGES.intentRank.updateClickStream();

        // Finally ensure everything took place
        runs(function(){
            expect(nsa.watch.callCount).toEqual(1);
            expect(nsa.intercept.callCount).toEqual(2);
        });
    });
});

// Advanced tests
describe("Advanced", function(){
    beforeEach(function() {
        nsa = jasmine.createSpyObj("nsa", ['watch', 'intercept']);
        jsonData = [];
    });

    function addToList ( arr ) {
        $.merge(jsonData, arr);
    }

    it("multiple_results", function(){
        for ( var i = 0; i < 10; i++ ) {
            Willet.mediator.fire('IR.getResults', [addToList]);
            PAGES.setLoadingBlocks(false);
            
            if (jsonData.length > 9) {
                break;
            }
        }
        
        waitsFor(function(){
            return jsonData.length > 9;
        }, 'PAGES.loadResults', 5000);

        runs(function(){
            expect(jsonData.length).toBeGreaterThan(9);
        });
    });
});