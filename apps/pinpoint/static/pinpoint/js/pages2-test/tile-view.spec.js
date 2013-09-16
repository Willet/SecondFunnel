describe("Tile View:", function () {
    describe("Initialization:", function() {
        it("should exist", function() {
            expect(TileView).toBeDefined();
        });

        xit("should be possible to create an instance", function() {
            var createTileCollection = function() {
                return new TileView();
            };

            expect(createTileCollection).not.toThrow();
        });
    });
});