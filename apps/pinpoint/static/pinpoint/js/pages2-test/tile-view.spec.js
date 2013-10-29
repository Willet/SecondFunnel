xdescribe("Tile View:", function () {
    // Our views are different in that they don't really do much with the model
    // However, we still may want a model instance to verify rendering

    // Modelled after code from this post:
    //  http://open.bekk.no/maintainable-tests-for-backbone-views

    var createTestTileView,
        TileView = Page.core.TileView;

    createTestTileView = function(options) {
        options = options || {};

        // Test views always use an in-memory element
        // unless we've said otherwise
        options.el = options.el || $('<div></div>');

        return new TileView(options);
    };

    beforeEach(function(){
        this.app = Page;
        this.app.start();
        loadFixtures('templates.html');
    });

    afterEach(function(){
        this.resetApp(this.app);
    })

    describe("Initialization:", function() {
        it("should exist", function() {
            expect(TileView).toBeDefined();
        });

        it("should be possible to create an instance", function() {
            expect(createTestTileView).not.toThrow();
        });

        it("should be possible to render an instance with a template", function() {
            var view = createTestTileView();
        });

        describe('Specification:', function() {
            it("Error Handling 3.2. That template must not " +
                "be rendered otherwise", function() {
                var view, renderFn;

                view = createTestTileView({
                    template: '#doesnotexist'
                });

                spyOn(view, 'close');

                renderFn = function() {
                    view.render();
                };

                expect(renderFn).not.toThrow();
                expect(view.close).toHaveBeenCalled();
            });
        });

        xit("", function() {

        });
    });

    describe("Functional requirements:", function() {
        it("should have regions for social buttons, " +
            "tile indicators, and so on", function() {
            var tileView = createTestTileView();

            expect(tileView.buttonsIndicator).toBeDefined();
            expect(tileView.loadingIndicator).toBeDefined();
            expect(tileView.tapIndicator).toBeDefined();

            // TODO: Verify that these areas are regions
        });

        it("should be loading by default", function() {
            var tileView = createTestTileView();

            expect(tileView.loading).toBeTruthy();
        });

        describe('Specification:', function() {
            beforeEach(function(){
                this.tileView  = createTestTileView();
                this.tileView.render();

                // In order for most of jquery-jasmine matchers to work,
                // needs to be appended to DOM. Don't worry, it'll clean itself up
                // Still, would be handy if we could just keep everythign in memory.
                appendSetFixtures(this.tileView.$el);
            });

            it("Behaviour 1.1. (When a user activates a tile, that tile must) " +
                "[t]ake its activation action", function() {
                expect(this.tileView.activate).toBeDefined();

                // Normally, we'd test the *behaviour* (e.g. what should happen)
                // However, since that action can change, we check
                // that the activation function fired... for now.
                spyOn(this.tileView, 'activate');

                // Redelegate events so that our spy works, AFAIK
                // http://stackoverflow.com/a/7930247
                this.tileView.delegateEvents();


                this.tileView.$el.click();

                expect(this.tileView.activate).toHaveBeenCalled();
            });

            it("Behaviour 1.2. (When a user activates a tile, that tile must) " +
                "[l]oad related results from the source URL", function() {
                var spy = jasmine.createSpy();
                expect(this.tileView.activate).toBeDefined();

                this.app.vent.on('fetch:related', spy);

                this.tileView.$el.click();

                expect(spy).toHaveBeenCalledWith();
            });

            it("Usability 5.1. If an image is loading, the user should see " +
                "some indication that some action is taking place", function() {
                expect(this.tileView.loading).toBeTruthy();

                this.tileView.render();
                expect(this.tileView.loadingIndicator.$el).toBeVisible();

                this.tileView.setLoading(false);
                expect(this.tileView.loading).toBeFalsy();

                expect(this.tileView.loadingIndicator.$el).not.toBeVisible();
            });

            xit("Usability 5.2. If an image is loading, a placeholder image " +
                "should be displayed with the dominant colour as the " +
                "background colour", function() {

            });

            // TODO: Deal with mobile / non-mobile
            xit("Usability 3.1. For non-mouse enabled devices, this indicator " +
                "should be an element overlayed on the tile", function() {

            });

            xit("Usability 3.2. For mouse enabled devices," +
                "this indicator should be a mouse pointer", function() {
            });

            xit("Usability 6.1. (A tile must not be rendered if) [t]he tile " +
                "contains images that are broken", function () {

            });

            xit("Usability 6.1. (A tile must not be rendered if) [t]he tile " +
                "does not meet ‘acceptable tile’ criteria", function () {

            });

            xit("Error Handling 5.2. (If an error occurs during an " +
                "activation action), landing pages should fall back to taking " +
                "some default action ", function() {
                // On activation fail, do whatever is defined in defaults
            });
        });

        it("", function() {

        });

        xit("", function() {

        });

        // Good candidates for tests (in general):
        // - Check that default template exists
        // - Check that social buttons are present (worry about 'if enabled' later)
        // - Check that certain regions exist?
        // - Using the right templates, etc.

        // Good candidates for tests (from spec):
        // ?Performance 5. Images rendered in tiles and preview should load at size appropriate for the effective resolution of the device
        // Behaviour 3. Developers and designers must be able to create listeners for important events including, but not limited to:
        //      - hovering over a tile,
        //      - hovering over a social button,
        //      - sharing using a social button,
        //      - page scrolling,
        //      - preview activation / deactivation,
        //      - product clickthrough,
        //      - page exit,
        //      - tiles added to the landing page,
        //      - tiles finished loading,
        //      - window resized,
        //      - dependencies loaded,
        //      - page complete load,
        //      - pre-page complete load
    });
});