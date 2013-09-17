describe("Page Application:", function () {
    beforeEach(function() {
        this.app = Page;
    });

    describe("Functional requirements:", function() {
        it("should exist", function() {
            expect(this.app).toBeDefined();
        });

        it("should have defined regions", function() {
            expect(this.app.heroArea).toBeDefined();
            expect(this.app.discoveryArea).toBeDefined();

            // TODO: Verify that regions actually exist on the page.
        });

        // TODO: How to handle regions throwing exceptions?
        // Alternatively, how to ensure that they exist?

        it("should render its child views on start", function () {
            // TODO: Use .andCallThrough whenever possible

            spyOn(this.app.heroArea, 'show').andCallThrough();
            spyOn(this.app.discoveryArea, 'show').andCallThrough();

            this.app.start();

            expect(this.app.heroArea.show).toHaveBeenCalled();
            expect(this.app.discoveryArea.show).toHaveBeenCalled();

            // TODO: Verify that areas rendered?
        });

        it("should create a TileCollection on start", function() {
            this.app.start();

            expect(this.app.tiles).toBeDefined();

            expect(this.app.tiles.length).toEqual(0);
        });

        it("should have default options", function() {
            expect(this.app.defaults).toBeDefined();

            expect(this.app.defaults.unchanged_default).toBeDefined();
            expect(this.app.defaults.unchanged_default).toEqual('unchanged');
            // TODO: Set other default values
        });

        it("should have a `getOption` function", function() {
            expect(this.app.getOption).toBeDefined();

            // TODO: Verify that this is a function
        });

        // TODO: Should not hardcode values like this
        // TODO: Fall back to default if selected option not found
        it("should populate options from PAGES_INFO", function() {
            expect(this.app.getOption('fruit'), 'banana');
            expect(this.app.getOption('unchanged_default')).toEqual('unchanged');
        });

//        it("should create add initial elements to collection", function() {
//            this.app.start();
//
//            expect(this.app.tiles).toBeDefined();
//
//            expect(this.app.tiles.length).toEqual(0);
//        });

        // should add initial elements to collection (.reset, reset event), and render
        // what event is fired on fetch?
        //  - Uses set (add)
        //      - could pass {reset: true}, but would that replace the entire collection
    });
});