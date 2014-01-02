xdescribe("Tile Collection:", function () {
    var Tile = App.core.Tile;
        TileCollection = App.core.TileCollection;

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

    // TODO: Since JSONP is a weird hack, can't use sinon to test it
    // We can, however, stub out $.ajax, but that seems way grosser
    describe("Functional requirements:", function() {

        beforeEach(function() {
            this.tileCollection = new TileCollection();
            this.server = sinon.fakeServer.create();
            this.server.respondWith(
                this.response(this.fixtures.TileCollection.valid)
            );
        });

        afterEach(function() {
            this.server.restore();
        });

        // Pass? What?
        it("should fetch model instances", function() {
            var initialSize = this.tileCollection.length;

            // TODO: shouldn't be overriding this, but have no choice at the moment.
            this.tileCollection.fetch({
                'dataType': 'json'
            });
            this.server.respond();

            expect(this.tileCollection.length).toBeGreaterThan(initialSize);
            // TODO: Should verify it gets the exact right model instances
        });

        it("should not remove existing model instances when fetching", function() {
            var model, initialLength;

            this.tileCollection.add({
                'key': 'value'
            });

            expect(this.tileCollection.length).toEqual(1);

            model = this.tileCollection.at(0);

            this.tileCollection.fetch({
                'dataType': 'json'
            });
            this.server.respond();

            expect(this.tileCollection.get(model.cid)).toBe(model);
            expect(this.tileCollection.length).toBeGreaterThan(1);
        });

        it("should 'allow duplicates' (e.g. fire the 'add' event on duplicates)", function() {
            var counter = 0,
                numElements = this.fixtures.TileCollection.valid.length;

            this.tileCollection.on('add', function() {
                counter += 1;
            });

            this.tileCollection.fetch({
                'dataType': 'json'
            });
            this.server.respond();
            initialLength = this.tileCollection.length;

            // Fetch again
            this.tileCollection.fetch({
                'dataType': 'json'
            });
            this.server.respond();

            expect(counter).toEqual(2*numElements);
        });

        // TODO: When a model is fetched, whether it exists or not, create a new view for it.

        // TODO: Use different URL depending on environment, settings, etc.

        // TODO: More thorough tests for fetch

        // TODO: No throwing exceptions when fetching?
    });
});
