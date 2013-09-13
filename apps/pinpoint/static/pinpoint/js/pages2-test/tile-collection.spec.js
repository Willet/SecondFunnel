describe("Tile Collection:", function () {
    describe("Initialization:", function() {
        it("should exist", function() {
            expect(TileCollection).toBeDefined();
        });

        it("should be possible to create an instance", function() {
            var createTileCollection = function() {
                return new TileCollection();
            };

            expect(createTileCollection).not.toThrow();
        });

        it("should be a collection of Tile instances", function() {
            var tileCollection = new TileCollection();

            expect(tileCollection.model).toBe(Tile);
        });

        it ("should default to fetching results from local server", function () {
             var tileCollection = new TileCollection();

            expect(tileCollection.url).toBe('http://localhost:8000/intentrank/store/nativeshoes/campaign/32/getresults');
        });
    });

    // Tile models are just vessels: They do not sync
    describe("Functional requirements:", function() {
        var tileCollection;

        beforeEach(function() {
            tileCollection = new TileCollection();
        });

        afterEach(function() {
            tileCollection = null; // Necessary? Probably not.
        });

        // Pass? What?
        it("should fetch model instances", function() {
            var self = this;
            var initialSize = tileCollection.length;

            // TODO: Is this how we should test, or should we use Jasmine's
            // latch / async stuff?
            tileCollection.on('sync', function (collection) {
                expect(collection.length).toBeGreaterThan(initialSize);
            });

            tileCollection.on('error', function() {
                self.fail('Unexpected: There was an error fetching.');
            });

            // TODO: Bake these options into the collection?
            tileCollection.fetch();
        });

        xit("should not remove existing model instances when fetching", function() {
            var self = this;

            // example data
            tileCollection.add({
                'key': 'value'
            });
            var initialSize = tileCollection.length;

            // TODO: Is this how we should test, or should we use Jasmine's
            // latch / async stuff?
            tileCollection.on('sync', function (collection) {
                expect(collection.length).toBeGreaterThan(initialSize);
            });

            tileCollection.on('error', function() {
                self.fail('Unexpected: There was an error fetching.');
            });

            tileCollection.fetch();
        });

        xit("should not merge existing model instances when fetching", function() {
            var self = this;
            var initialSize = tileCollection.length;

            // example data
            tileCollection.add({
                'key': 'value'
            });

            // TODO: Is this how we should test, or should we use Jasmine's
            // latch / async stuff?
            tileCollection.on('sync', function (collection) {
                expect(collection.length).toBeGreaterThan(initialSize);
            });

            tileCollection.on('error', function() {
                self.fail('Unexpected: There was an error fetching.');
            });

            // TODO: Bake these options into the collection?
            tileCollection.fetch();
        });

        // TODO: When a model is fetched, whether it exists or not, create a new view for it.

        // TODO: Use different URL depending on environment, settings, etc.

        // TODO: More thorough tests for fetch

        // TODO: No throwing exceptions when fetching?
    });
});