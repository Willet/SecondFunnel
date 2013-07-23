// Order matters!
// This is the base JS file, the first file that is called when we test the
// sauce for the SecondFunnel project.  It instantiates the needed modules.
describe("Setup", function() {
    it("initialize Pages", function() {
        (Willet.browser=Willet.browser||{}).mobile = true;
        PAGES.init();

        $(document).bind("mobileinit", function () {
            $.mobile.autoInitializePage = false;
        });

        if (Willet.browser.mobile) {
            $(function () {
                $.mobile.initializePage();
            }); 
        }   
    
        // Check that Pages, IntentRank and the Mediator are up to go
        expect(PAGES.intentRank).toEqual(jasmine.any(Object));
        expect(Willet.mediator).toBeDefined();
    });

});
