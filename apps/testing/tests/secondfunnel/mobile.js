// Order matters!
// This is the base JS file, the first file that is called when we test the
// sauce for the SecondFunnel project.  It instantiates the needed modules.
describe("Setup", function() {
    it("initialize Pages", function() {
        (Willet.browser=Willet.browser||{}).mobile = true;

        $(document).bind("mobileinit", function () {
            $.mobile.autoInitializePage = false;
        });

        if (Willet.browser.mobile) {
            $(function () {
                $.mobile.initializePage();
            }); 
        }   
        // Want to disable Page Scrolling for our Unit Tests
        PAGES.__pageScroll__ = PAGES.pageScroll;
        PAGES.pageScroll = function() { return; };    
        PAGES.attachListeners();
        
        var callback = jasmine.createSpy("init");
        expect(Willet.mediator.fire).toBeDefined();

        runs(function(){
            Willet.mediator.fire('IR.init', []);
            Willet.mediator.fire('IR.changeSeed', []);
            Willet.mediator.fire('IR.getInitialResults', [callback]);
        });

        waitsFor(function() {
            return callback.callCount > 0;
        }, "initial results to load", 5000); 

        runs(function(){
            expect(callback.callCount).toEqual(1);
        });
    });
});
