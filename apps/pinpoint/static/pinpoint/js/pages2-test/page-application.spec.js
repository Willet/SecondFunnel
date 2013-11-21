xdescribe("Page Application:", function () {
    beforeEach(function() {
        this.app = SecondFunnel;
    });

    afterEach(function() {
        this.resetApp(this.app);
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
            expect(this.app.defaults.LOG).toBeDefined();
            // TODO: Set other default values

            expect(this.app.defaults.fruit).not.toBeDefined()
        });

        it("should have a `getOption` function", function() {
            expect(this.app.getOption).toBeDefined();
            // TODO: Verify that this is a function
        });

        it("should populate options from passed in options", function() {
            var default_log,
                options = {
                    'fruit': 'banana'
                };

            default_log = this.app.defaults.LOG
            this.app.start(options);

            expect(this.app.getOption('fruit')).toEqual(options.fruit);
            expect(this.app.getOption('LOG')).toEqual(default_log);
        });

        // TODO: Move PAGE_INFO (or equivalent) to fixtures.js?
        // TODO: List relevant requirement
        it("should add initial elements to collection", function() {
            var options = {
                    models: []
                },
                i = 10;

            while(i > 0) {
                options.models.push(this.generateTile());
                i--;
            }

            this.app.start(options);

            expect(this.app.tiles).toBeDefined();

            // Spec says only load 4 tiles initially... we can change as necessary
            expect(this.app.tiles.length).toEqual(4);
        });

        // should add initial elements to collection (.reset, reset event), and render
        // what event is fired on fetch?
        //  - Uses set (add)
        //      - could pass {reset: true}, but would that replace the entire collection
    });
});