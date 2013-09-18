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

    app.addInitializer(function (options) {
        // delegated analytics bindings
        var defaults = new app.classRegistry.EventManager(app.tracker.defaultEventMap),
            customs = new app.classRegistry.EventManager(options.events);
    });

    app.addInitializer(function (options) {
        // set its width to whatever it began with.
        app.options.initialWidth = $(window).width();
    });

    app.addInitializer(function (options) {
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

        if (app.option('debug', false) >= app.VERBOSE) {
            setInterval(function () {
                // highlight elements
                $('div').css('outline', '1px rgba(255,0,0,0.5) dotted');
                $('span').css('outline', '1px rgba(0,255,0,0.5) dotted');
                $('img').css('outline', '1px rgba(0,255,0,0.5) dotted');
            }, 5000);
        }
    });

    app.addInitializer(function (options) {
        try {
            var fa = new app.classRegistry.HeroAreaView();
            fa.render();
            broadcast('heroAreaRendered', fa);
        } catch (err) {
            // marionette throws an error if no hero templates are found or needed.
            // it is safe to ignore it.
            broadcast('heroAreaNotRendered');
        }
    });

    app.addInitializer(function (options) {
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

    app.addInitializer(function (options) {
        // Add our initializer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        broadcast('beforeInit', options, app);

        $('.brand-label').text(app.option("store:displayName") ||
                               _.capitalize(app.option("store:name")) ||
                               'Brand Name');

        $(document).ajaxError(function (event, request, settings) {
            broadcast('ajaxError', settings.url, app);
        });

        app.discovery = new app.classRegistry.Discovery(options);
        broadcast('finished', options, app);
    });

    app.addInitializer(function (options) {
        // set its width to whatever it began with.
        app.options.initialWidth = $(window).width();
    });
}

// auto-initialise existing instance on script inclusion
reInitialize(window.SecondFunnel);