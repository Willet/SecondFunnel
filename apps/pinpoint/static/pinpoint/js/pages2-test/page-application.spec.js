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
        });

        it("should create a TileCollection on start", function() {
            this.app.start();

            expect(this.app.tiles).toBeDefined();

            // TODO: Verify that the collection is actually a collection
        });
    });
});