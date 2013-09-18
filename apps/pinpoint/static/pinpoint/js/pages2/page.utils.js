Page.module("utils", function(utils, page, B, M, $, _) {
    // WARNING: Untested
    utils.createApplication = function (options, initializers, regions) {
        var i,
            app = M.Application(options);

        app.addRegions(regions);

        for(i = 0; i < initializers.length; i++) {
            app.addInitializer(initializers[i]);
        }

        return app;
    };
});