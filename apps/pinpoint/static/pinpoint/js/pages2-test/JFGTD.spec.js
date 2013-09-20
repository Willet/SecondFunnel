// Nick is letting perfection get in the way of getting things done.
// So don't worry about what the spec says. Just do what we need to do,
// Then worry about the spec, and categorizing everything, ok?
describe("JUST DO WHAT I EXPECT! IS THAT SO HARD TO UNDERSTAND?!", function () {
    beforeEach(function() {
        this.app = Page;
    });

    describe("Page Load:", function() {
        beforeEach(function() {
            loadFixtures('pageTemplate.html', 'templates.html');
        });

        afterEach(function() {
            this.resetApp(this.app);
        });

        it("Should show the 'hero area' and " +
            "'discovery area' on page load", function() {
            this.app.start();

            expect(this.app.heroArea.$el).toBeVisible();
            expect(this.app.discoveryArea.$el).toBeVisible();
        });

        it("Should load initial tiles into the collection", function() {
            var options = {models: []},
                numTiles,
                i = 10;

            while(i > 0) {
                options.models.push(this.generateTile());
                i--;
            }

            this.app.start(options);

            numTiles = this.app.tiles.length;
            expect(numTiles).toEqual(4);

            expect(this.app.discoveryArea.$el).not.toBeEmpty();
            expect(this.app.discoveryArea.$el.find('.tile')).toHaveLength(4);
        });
    });

    describe("Other Page events:", function() {
        beforeEach(function() {
            loadFixtures('pageTemplate.html', 'templates.html');

            this.server = sinon.fakeServer.create();
            this.server.autoRespond = true;
            this.server.respondWith(
                this.response(this.fixtures.TileCollection.valid)
            );
        });

        afterEach(function() {
            this.resetApp(this.app);
            this.server.restore();
        });

        // collection loads more results on page scroll
        it("Should load more results on page scroll", function() {
            var numTiles,
                // How can we avoid using JSONP in test, in general?
                // Maybe pass in a testing collection that extends the
                // regular collection?
                options = {
                    window: $('<div></div>'),
                    fetchMode: 'json' // dirty hack
                };

            // Extra divs generated by backbone. More details on how
            // to potentially remove them here:
            //      http://stackoverflow.com/a/11189626


            // Ideally, we would check to see if the currentView is
            // the empty view, but apparently I don't know how to do that.
            //      (Note, at the time of writing, the emptyView was
            //       the LoadingIndicator)
            this.app.start(options);
            expect(this.app.discoveryArea.currentView.$el).toContain('.loading');


            // We can avoid calling server.respond IF we make requests
            // synchronous. That may be plausible for testing purposes
            // OR we'll need to use a different abstraction.
            options.window.scroll();
            this.server.respond();

            numTiles = this.app.discoveryArea.$el.find('.tile').length;
            expect(this.app.discoveryArea.$el).not.toBeEmpty();
            expect(numTiles).toBeGreaterThan(0);

            options.window.scroll();
            this.server.respond();

            expect(this.app.discoveryArea.$el.find('.tile').length)
                .toBeGreaterThan(numTiles);
        });

        // collection loads more results when fetch related is called
        it("Should load more results when an item is clicked", function () {
            this.app.start({
                'fetchMode': 'json'
            });

            // What would be better would be triggering
            // a tile's 'activate' method

            spyOn(this.app.tiles, 'fetch').andCallThrough();

            this.app.vent.trigger('fetch:related', this.app);

            expect(this.app.tiles.fetch).toHaveBeenCalled();
            // Always need to call respond when using
            // fake server asynchronously...
            this.server.respond();

            expect(this.app.discoveryArea.$el.find('.tile').length)
                .toBeGreaterThan(0);
        });
    });

    describe("Page Templates:", function() {
        it("Should not render views that don't have a template", function() {
            var self = this,
                renderTemplatesOnStart = function() {
                self.app.start();
            }
            expect(renderTemplatesOnStart).not.toThrow();
        });
    });

    describe("Tile Models:", function() {
        // ???
    });

    describe("Tile Loading:", function() {
        beforeEach(function() {
            loadFixtures('pageTemplate.html');
        });

        // don't render tiles that don't have a template
        it("Should not render tiles that don't have a template", function() {
            var tileView;
            this.app.start();

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();
            expect(tileView.$el).toBeEmpty();

            // loadFixtures wipes out any previously loaded fixtures
            loadFixtures('templates.html');
            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();
            expect(tileView.$el).not.toBeEmpty();
        });

        // show loading indicator when loading
        // show tap indicator if on mobile
        // show mouse hints if not on mobile
    });

    describe("Tile Interaction: ", function() {
        // clicking tile launches preview
        // more results are fetched on tile click
        // tile type renders dependent on data / model
        // buttons appear on hover
        // buttons don't appear on mobile
        // specific buttons render depending on page settings? (Here or elsewhere)
        // different tile types (e.g. video, etc.)
    });

    describe("Preview: ", function() {
        // preview displays data from tile model
        // something about closing tile
    });

    describe("Tile Layout: ", function() {
        // tiles injected near activated tile
        // tiles injected at the bottom of the page on scroll
    });

    describe("Tracking: ", function() {

    });

    describe("Display modes: ", function() {

    });
});