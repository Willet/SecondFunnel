/* Tests related to the pinpoint app go here. */
var jsonData,
// Our NSA WatchDog
    nsa; 

// Basic Functionality tests
describe('The Basics', function() {
    // IntentRank
    it('intentrank_more_results', function() {
        var callback = jasmine.createSpy();
        PAGES.intentRank.getMoreResults(callback);

        waitsFor(function() {
            return callback.callCount > 0;
        }, "call to /intentrank/get-results to respond", 5000);

        runs(function() {
            expect(callback).toHaveBeenCalled();
        });
    });

    it('intentrank_valid_json', function() {
        var jsonInspector = jasmine.createSpy("jsonInspector");
        PAGES.intentRank.getMoreResults(jsonInspector);

        waitsFor(function() {
            return jsonInspector.callCount > 0;
        }, "call to /intentrank/get-results to respond", 5000);

        runs(function() {
            jsonData = jsonInspector.mostRecentCall.args[0];
            expect(jsonData).toEqual(jasmine.any(Array));
        });
    });

    it('intentrank_loading', function() {
        PAGES.setLoadingBlocks(true);
        expect(PAGES.intentRank.getMoreResults()).toEqual(undefined);
        PAGES.setLoadingBlocks(false);
    });


    // Mediator tests
    it('mediator_on_off', function() {
        var nsa = jasmine.createSpyObj('nsa', ['survelliance']);
        
        Willet.mediator = Willet.mediator.on('openEmail', nsa.survelliance);
        Willet.mediator.fire('openEmail');

        expect(nsa.survelliance.callCount).toEqual(1);

        Willet.survelliance = (function () {
            function autoOpenEmail () {
                return;
            }
            
            return {
                'autoOpenEmail': autoOpenEmail
            };
        })();

        spyOn(Willet.survelliance, 'autoOpenEmail').andCallFake(function() {
            return "Opened email!";
        });

        Willet.mediator.fire('openEmail');
        expect(nsa.survelliance.callCount).toEqual(2);
        expect(Willet.survelliance.autoOpenEmail()).toEqual("Opened email!");

        delete Willet.survelliance;
        Willet.mediator.off('openEmail');
        Willet.mediator.fire('openEmail');

        expect(nsa.survelliance.callCount).toEqual(2);
    });

    it('mediator_callback', function() {
        var callback = jasmine.createSpy('callback');
        Willet.mediator.on('fake', callback);
        expect(typeof Willet.mediator.callback("fake")).toEqual("function");
        
        Willet.mediator.callback("fake")();
        expect(callback.callCount).toEqual(1);
        
        Willet.mediator.getResult('fake');
        expect(callback.callCount).toEqual(2);

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
        nsa = jasmine.createSpyObj("nsa", ['listen', 'watch', 'intercept']);
        var intercept = function() { nsa.intercept(); };

        spyOn(pagesTracking, 'notABounce').andCallFake(intercept);
        spyOn(PAGES.intentRank, 'updateClickStream').andCallFake(intercept);
        spyOn(PAGES.intentRank, 'updateContentStream').andCallFake(intercept);
    });

    it('session1', function(){
        // User is not a bounce
        pagesTracking.notABounce();
        PAGES.loadMoreResults(nsa.watch, true);
        
        // Load more results below the fold
        waitsFor(function(){
            return nsa.watch.callCount > 0;
        }, 'PAGES.loadMoreResults', 5000);

        runs(function(){
            jsonData = nsa.watch.mostRecentCall.args[0];
            expect(jsonData.error).toBeUndefined();
            expect(jsonData).toEqual(jasmine.any(Object));
            expect(jsonData.length).toBeGreaterThan(0);
        });
        
        // User clicked one of the discovery blocks
        expect(PAGES.loadMoreResults(nsa.listen, false, true)).toEqual(undefined);
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
        jsonData = [];
    });

    function addToList ( arr ) {
        setTimeout(function(){
            $.extend(jsonData, arr);
        }, 1);
    }

    it("no_dupes", function(){
        for ( var i = 0; i < 10; i++ ) {
            Willet.mediator.fire('IR.getMoreResults', [addToList]);
            PAGES.setLoadingBlocks(false);
        }
        
        waitsFor(function(){
            return jsonData.length > 9;
        }, 'PAGES.loadMoreResults', 5000);

        runs(function(){
            var dupes = false;
            for ( var i = 0; i < jsonData.length; ++i ) {
                var elem = jsonData[i];
                for ( var j = i + 1; j < jsonData.length; ++j ) {
                    var compare = jsonData[j];
                    for (var key in elem) {
                        if (compare[key] && compare[key] == elem[key]) {
                            dupes = true;
                            break;
                        }
                    }
                    if (dupes) break;
                }
                if (dupes) break;
            }
            expect(dupes).toBe(false);
            expect(jsonData.length).toBeGreaterThan(9);
        });
    });
});