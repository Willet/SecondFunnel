/*global $, _, SecondFunnel, broadcast*/
// SecondFunnel initializers.

/**
 * Given an instance of  Marionette Application, add initializers to it.
 * @param app
 */
function reInitialize(app) {
    "use strict";

    if (app === undefined) {
        return;
    }

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
        try {
            var fa = new app.core.HeroAreaView();
            fa.render();
            broadcast('heroAreaRendered', fa);
        } catch (err) {
            // marionette throws an error if no hero templates are found or needed.
            // it is safe to ignore it.
            broadcast('heroAreaNotRendered');
        }
    });

    app.addInitializer(function () {
        if (window.console) {
            app.vent.on('log', function () {
                try {  // console.log is an object in IE...?
                    console.log.apply(console, arguments);
                } catch (e) {}
            });
            app.vent.on('warn', function () {
                try {
                    console.warn.apply(console, arguments);
                } catch (e) {}
            });
            app.vent.on('error', function () {
                try {
                    console.error.apply(console, arguments);
                } catch (e) {}
            });

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
        }
    });

    app.addInitializer(function () {
        // Add our initializer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        broadcast('beforeInit', app.options, app);

        $('.brand-label').text(app.option("store:displayName") ||
                               _.capitalize(app.option("store:name")) ||
                               'Brand Name');

        $(document).ajaxError(function (event, request, settings) {
            broadcast('ajaxError', settings.url, app);
        });

        app.discovery = new SecondFunnel.core.Discovery(app.options);
        broadcast('finished', app.options, app);
    });

    app.addInitializer(function () {
        // set its width to whatever it began with.
        app.options.initialWidth = $(window).width();
    });
}

// auto-initialise existing instance on script inclusion
reInitialize(window.SecondFunnel);