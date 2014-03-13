/*global $, _, Backbone, beforeEach, afterEach, expect, describe, it, runs, spyOn, loadFixtures, App*/
// Nick is letting perfection get in the way of getting things done.
// So don't worry about what the spec says. Just do what we need to do,
// Then worry about the spec, and categorizing everything, ok?
describe("(just fucking get things done)! IS THAT SO HARD TO UNDERSTAND?!", function () {
    "use strict";

    beforeEach(function () {
        this.app = App;
    });

    describe("Page Load:", function () {
        beforeEach(function () {
            loadFixtures('pageTemplate.html', 'templates.html');
            reinitialize(this.app);
            // loads masonry on this view
            this.app.layoutEngine.initialize(this.app.discovery, this.app.options);
        });

        afterEach(function () {
            // this.resetApp(this.app);
        });

        it("Should show the 'hero area' and " +
            "'discovery area' on page load", function () {
            this.app.start();

            expect(this.app.heroArea.$el).toBeDefined();
            expect(this.app.discoveryArea.$el).toBeDefined();
        });

        it("Should load initial tiles into the collection", function () {
            var options = {models: []},
                numTiles,
                i = 10;

            while (i > 0) {
                this.app.discovery.collection.add(this.generateTile());
                i--;
            }

            this.app.start();

            numTiles = this.app.discovery.collection.models.length;
            expect(numTiles).toEqual(10);

            expect(this.app.discoveryArea.$el).not.toBeEmpty();
            expect(this.app.discoveryArea.$el.find('.tile')).toHaveLength(10);
        });
    });

    describe("Other Page events:", function () {
        beforeEach(function () {
            loadFixtures('pageTemplate.html', 'templates.html');

            this.server = sinon.fakeServer.create();
            this.server.autoRespond = true;
            this.server.respondWith(
                this.response(this.fixtures.TileCollection.valid)
            );
        });

        afterEach(function () {
            this.resetApp(this.app);
            this.server.restore();
        });

        // collection loads more results on page scroll
        xit("Should load more results on page scroll", function () {
            var numTiles,
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


            // We can avoid calling server.respond IF we make requests
            // synchronous. That may be plausible for testing purposes
            // OR we'll need to use a different abstraction.
            this.app.discoveryArea.currentView.pageScroll();
            this.server.respond();

            numTiles = this.app.discoveryArea.$el.find('.tile').length;
            expect(this.app.discoveryArea.$el).not.toBeEmpty();
            expect(numTiles).toBeGreaterThan(0);

            App.discoveryArea.currentView.pageScroll();
            this.server.respond();

            expect(this.app.discoveryArea.$el.find('.tile').length)
                .toBeGreaterThan(numTiles);

            // TODO: Should only add new tiles when scrolling near the bottom
        });

        // collection loads more results when fetch related is called
        xit("Should load more results when an item is clicked", function () {
            this.app.start({
                'fetchMode': 'json'
            });

            // What would be better would be triggering
            // a tile's 'activate' method

            spyOn(this.app.intentRank, 'fetch').andCallThrough();

            this.app.intentRank.getResults();

            expect(this.app.intentRank.fetch).toHaveBeenCalled();
            // Always need to call respond when using
            // fake server asynchronously...
            this.server.respond();

            expect(this.app.discoveryArea.$el.find('.tile').length)
                .toBeGreaterThan(0);
        });
    });

    xdescribe("Page Templates:", function () {
        it("Should not render views that don't have a template", function () {
            var self = this,
                renderTemplatesOnStart = function () {
                    self.app.start();
                };
            expect(renderTemplatesOnStart).not.toThrow();
        });
    });

    describe("Tile Models:", function () {
        // ???
    });

    xdescribe("Tile Loading:", function () {
        beforeEach(function () {
            loadFixtures('pageTemplate.html');
        });

        afterEach(function () {
            this.resetApp(this.app);
        });

        // don't render tiles that don't have a template
        it("Should not render tiles that don't have a template", function () {
            var tileView;
            this.app.start();

            tileView = new this.app.core.TileView({model: {}});
            tileView.render();
            expect(tileView.$el).toBeEmpty();

            // loadFixtures wipes out any previously loaded fixtures
            loadFixtures('templates.html');
            tileView = new this.app.core.TileView({model: {}});
            tileView.render();
            expect(tileView.$el).not.toBeEmpty();
        });

        // show loading indicator when loading
        it("Should show a loading indicator when loading tiles", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start();

            tileView = new this.app.core.TileView({model: {}});
            tileView.render();

            expect(tileView.loading).toBeTruthy();
            expect(tileView.loadingIndicator.$el).not.toBeEmpty();

            tileView.setLoading(false);

            // Actually removes the indicator entirely.
            expect(tileView.loading).toBeFalsy();
            expect(tileView.loadingIndicator.$el).toBeUndefined();
        });

        // TODO: Should not show buttons if loading
        // TODO: Should eventually not be loading

        it("Should show a tap indicator if on mobile", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start({
                mobile: true
            });

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            expect(tileView.tapIndicator.$el).toBeDefined();
            expect(tileView.tapIndicator.$el).not.toBeEmpty();
        });

        it("Should not show a tap indicator if not on mobile", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start();

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            expect(tileView.tapIndicator.$el).toBeUndefined();
        });

        // show mouse hints if not on mobile
        it("Should show mouse hints if not on mobile", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start({
                mobile: true
            });

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            expect(tileView.$el).not.toHaveClass('mouse-hint');
        });

        it("Should not show mouse hints if not on mobile", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start();

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            expect(tileView.$el).toHaveClass('mouse-hint');
        });
    });

    xdescribe("Tile Interaction:", function () {
        afterEach(function () {
            this.resetApp(this.app);
        });

        // We'll settle for 'called its activate method'
        it("Should launch a preview when clicking on a tile", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start();

            expect(this.app.previewArea).toBeDefined();
            expect(this.app.previewArea.$el).toBeUndefined();

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            spyOn(tileView, 'activate').andCallThrough();
            // Redelegate events so that our spy works, AFAIK
            // http://stackoverflow.com/a/7930247
            tileView.delegateEvents();
            tileView.$el.click();
            expect(tileView.activate).toHaveBeenCalled();

            // TODO: change so that preview is the default action,
            // but `activate` can be overridden
            expect(this.app.previewArea.$el).toBeDefined();
            expect(this.app.previewArea.$el).not.toBeEmpty();
        });

        // buttons only appear on hover on desktop
        it("Buttons should only appear on hover", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start();

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            expect(tileView.buttonsIndicator.$el).not.toBeDefined();

            tileView.$el.mouseenter();

            expect(tileView.buttonsIndicator.$el).toBeDefined();
            expect(tileView.buttonsIndicator.$el).not.toBeEmpty();

            tileView.$el.mouseleave();
            expect(tileView.buttonsIndicator.$el).not.toBeDefined();
        });

        // buttons don't appear on mobile
        it("Buttons should not appear at all on mobile", function () {
            var tileView;

            loadFixtures('templates.html');

            this.app.start({
                mobile: true
            });

            tileView = new this.app.core.TileView({
                el: $('<div></div>')
            });
            tileView.render();

            expect(tileView.buttonsIndicator.$el).not.toBeDefined();

            // not really possible on mobile, but lets try!
            tileView.$el.mouseenter();
            expect(tileView.buttonsIndicator.$el).not.toBeDefined();

            // not really possible on mobile, but lets try!
            tileView.$el.mouseleave();
            expect(tileView.buttonsIndicator.$el).not.toBeDefined();
        });

        // TODO: Test that tap equivalents do not trigger hover.

        // hover events shouldn't be registered at all on mobile

        // specific buttons render depending on page settings? (Here or elsewhere)

    });

    xdescribe("Tile Collection:", function () {
        beforeEach(function () {
            loadFixtures('pageTemplate.html', 'templates.html');

            this.server = sinon.fakeServer.create();
            this.server.autoRespond = true;
            this.server.respondWith(
                this.response([
                    this.generateTile({type: 'video'}),
                    this.generateTile()
                ])
            );
        });

        afterEach(function () {
            this.resetApp(this.app);
            this.server.restore();
        });

        // tile type renders dependent on data / model
        it("Should render different views depending on the model", function () {
            // fill collection with two different models.
            // check the views
            var options = {
                fetchMode: 'json' // dirty hack
            };

            this.app.start(options);

            // Apparently, Nick got lazy
            this.app.discovery.collection.fetch({dataType: 'json'});
            this.server.respond();

            expect(this.app.discoveryArea.$el).not.toBeEmpty();
            expect(this.app.discoveryArea.$el.find('.tile').length).toEqual(2);
            expect(this.app.discoveryArea.$el.find('.tile.video').length).toEqual(1);
        });
    });

    xdescribe("Layout:", function () {
        beforeEach(function () {
            loadFixtures('pageTemplate.html', 'templates.html');

            this.server = sinon.fakeServer.create();
            this.server.autoRespond = true;
            this.server.respondWith(
                this.response([
                    this.generateTile({type: 'video'}),
                    this.generateTile()
                ])
            );
        });

        afterEach(function () {
            this.resetApp(this.app);
            this.server.restore();
        });

        // TODO: These two tests are not great; they check that things are called on masonry.
        // really, we should check that some behaviour has happened (e.g. a tile is at some location
        // or some properties are set on tiles).
        it("Should layout the tiles initially", function () {
            var options = {
                fetchMode: 'json' // dirty hack
            };

            spyOn(Masonry.prototype, 'layout');
            this.app.start(options);

            expect(this.app.discoveryArea.currentView.layoutManager.layout).toHaveBeenCalled();
            this.fail("Above expectation should have failed, but didn't. `layout()` called somehow?")
        });

        it("Should add and layout the tiles when new results are fetched", function () {
            var options = {
                fetchMode: 'json' // dirty hack
            };

            spyOn(Masonry.prototype, 'layout');
            spyOn(Masonry.prototype, 'appended');

            this.app.start(options);
            expect(this.app.layoutEngine.layout).toHaveBeenCalled();

            // Apparently, Nick got lazy
            this.app.discovery.collection.fetch({dataType: 'json'});
            this.server.respond();

            // Should we verify that `appended` and `layout` are only called once?
            // Right now, they're called once per item, as I don't think we have an event to notice
            // when all items have loaded
            expect(this.app.layoutEngine.append).toHaveBeenCalled();
            expect(this.app.layoutEngine.layout).toHaveBeenCalled();
        });
    });

    describe("Preview:", function () {
        // preview displays data from tile model
        // something about closing tile
    });

    describe("Tile Layout:", function () {
        // tiles injected near activated tile
        // tiles injected at the bottom of the page on scroll
    });

    describe("Tracking:", function () {

    });

    describe("Display modes:", function () {

    });
});
