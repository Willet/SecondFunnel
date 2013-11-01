xdescribe("Tile Model:", function () {
    var Tile = SecondFunnel.core.Tile;

    describe("Initialization:", function() {
        it("should exist", function() {
            expect(Tile).toBeDefined();
        });

        it("should be possible to create an instance", function() {
            var createTile = function() {
                return new Tile();
            };

            expect(createTile).not.toThrow();
        });

        it("should have certain default values set", function() {
            var tile = new Tile();

            expect(tile.idAttribute).toEqual('db-id');

            expect(tile.get('content-type')).toEqual('product');
            // TODO: Set more defaults
        });
    });

    // Tile models are just vessels: They do not sync
    describe("Functional requirements:", function() {
        var tile;

        beforeEach(function() {
            tile = new Tile();
        });

        it("saving should have no effect on model values", function() {
            tile.set({'key': 'value'});

            tile.save();

            expect(tile.get('key')).toEqual('value');
        });

        // TODO: Is there an easy way to test this? Easy way to spy on ajax?
        xit("saving should not make any requests", function() {
        });

        // Responsibility of the tile collection, I guess
        // ... unless we have a URL to fetch this specific element?
        it("fetching should have no effect on model values", function() {
            tile.set({'key': 'value'});

            tile.fetch();

            expect(tile.get('key')).toEqual('value');
        });
    });
});