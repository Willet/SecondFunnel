/*global $, _, SecondFunnel, Backbone, broadcast*/

/**
 * Given an instance of  Marionette Application, add initializers to it.
 * @param app
 */
function reInitialize(app) {
    "use strict";

    broadcast('beforeInit', app.options, app);

    app.addRegions({
        'heroArea': '#hero-area',
        'discoveryArea': '#discovery-area',
        'previewArea': '#preview'
    });

    // from davidsulc/marionette-gentle-introduction
    app.navigate = function (route, options) {
        options = options || {};
        Backbone.history.navigate(route, options);
    };

    // from davidsulc/marionette-gentle-introduction
    app.getCurrentRoute = function () {
        return Backbone.history.fragment;
    };

    app.addInitializer(function () {
        // set its width to whatever it began with.
        app.options.initialWidth = $(window).width();
    });

    app.addInitializer(function () {
        if (app.option('debug', false) >= app.ALL) {
            $(document).ready(function () {
                // don't use getScript, firebug needs to know its src path
                // and getScript removes the tag so firebug doesn't know what to do
                var tag = document.createElement('script'),
                    firstScriptTag;
                tag.src = "https://getfirebug.com/firebug-lite.js";

                firstScriptTag = document.getElementsByTagName('script')[0];
                firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
                broadcast('firebugLoaded');
            });
        }
    });

    app.addInitializer(function () {
        var fa = new app.core.HeroAreaView();
        app.heroArea.show(fa);

        broadcast('heroAreaRendered', fa);
    });

    app.addInitializer(function () {
        app.vent.on('beforeInit', function (details) {
            var pubDate;
            if (details && details.page && details.page.pubDate) {
                pubDate = details.page.pubDate;
            }
            console.log(  // feature, not a bug
                '____ ____ ____ ____ _  _ ___     ____ _  _ ' +
                '_  _ _  _ ____ _    \n[__  |___ |    |  | |' +
                '\\ | |  \\    |___ |  | |\\ | |\\ | |___ | ' +
                '   \n___] |___ |___ |__| | \\| |__/    |   ' +
                ' |__| | \\| | \\| |___ |___ \n' +
                '           Published ' + pubDate);
        });
    });

    app.addInitializer(function () {
        // Add our initializer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.

        $('.brand-label').text(app.option("store:displayName") ||
                               _.capitalize(app.option("store:name")) ||
                               'Brand Name');

        $(document).ajaxError(function (event, request, settings) {
            broadcast('ajaxError', settings.url, app);
        });
    });

    // from davidsulc/marionette-gentle-introduction
    app.on("initialize:after", function () {
        if (Backbone.history) {
            // although not used as extensively as it should be (e.g.
            // show tile preview, show specific category, etc.), it is here
            // for the future
            Backbone.history.start();

            if (this.getCurrentRoute() === "") {
                // create a discovery area with tiles in it
                app.store = new SecondFunnel.core.Store(app.options.store);

                app.discovery = new SecondFunnel.core.Feed({
                    options: app.options
                });
                SecondFunnel.discoveryArea.show(app.discovery);

                broadcast('finished', app.options, app);
            }
        }
    });

    app.vent.on('finished', function () {
        if (SecondFunnel.support.isAniPad()) {
            $('html').addClass('ipad');
        }
    });
}

// auto-initialise existing instance on script inclusion
reInitialize(window.SecondFunnel);