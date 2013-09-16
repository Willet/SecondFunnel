/*global $, _, SecondFunnel, broadcast*/
// SecondFunnel initializers.

SecondFunnel.addInitializer(function (options) {
    // delegated analytics bindings
    var defaults = new SecondFunnel.classRegistry.EventManager(SecondFunnel.tracker.defaultEventMap),
        customs = new SecondFunnel.classRegistry.EventManager(options.events);
});

SecondFunnel.addInitializer(function (options) {
    if (SecondFunnel.option('debug', false) >= SecondFunnel.ALL) {
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

    if (SecondFunnel.option('debug', false) >= SecondFunnel.VERBOSE) {
        setInterval(function () {
            // highlight elements
            $('div').css('outline', '1px rgba(255,0,0,0.5) dotted');
            $('span').css('outline', '1px rgba(0,255,0,0.5) dotted');
            $('img').css('outline', '1px rgba(0,255,0,0.5) dotted');
        }, 5000);
    }
});

SecondFunnel.addInitializer(function (options) {
    try {
        var fa = new SecondFunnel.classRegistry.HeroAreaView();
        fa.render();
        broadcast('heroAreaRendered', fa);
    } catch (err) {
        // marionette throws an error if no hero templates are found or needed.
        // it is safe to ignore it.
        broadcast('heroAreaNotRendered');
    }
});

SecondFunnel.addInitializer(function (options) {
    if (window.console) {
        SecondFunnel.vent.on('log', function () {
            try {  // console.log is an object in IE...?
                console.log.apply(console, arguments);
            } catch (e) {}
        });
        SecondFunnel.vent.on('warn', function () {
            try {
                console.warn.apply(console, arguments);
            } catch (e) {}
        });
        SecondFunnel.vent.on('error', function () {
            try {
                console.error.apply(console, arguments);
            } catch (e) {}
        });

        SecondFunnel.vent.on('beforeInit', function (details) {
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

SecondFunnel.addInitializer(function (options) {
    // Add our initializer, this allows us to pass a series of tiles
    // to be displayed immediately (and first) on the landing page.
    broadcast('beforeInit', options, SecondFunnel);

    $('.brand-label').text(SecondFunnel.option("store:displayName") ||
                           _.capitalize(SecondFunnel.option("store:name")) ||
                           'Brand Name');

    $(document).ajaxError(function (event, request, settings) {
        broadcast('ajaxError', settings.url, SecondFunnel);
    });

    SecondFunnel.discovery = new SecondFunnel.classRegistry.Discovery(options);
    broadcast('finished', options, SecondFunnel);
});