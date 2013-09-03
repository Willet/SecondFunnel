/*global $, _, SecondFunnel, broadcast*/
// SecondFunnel initializers.

SecondFunnel.addInitializer(function (options) {
    window.SecondFunnel = SecondFunnel;

    SecondFunnel.getModifiedTemplateName = function (name) {
        return name.replace(/(styld[\.\-]by|tumblr|pinterest|facebook|instagram)/i,
            'image');
    };
});

SecondFunnel.addInitializer(function (options) {
    // delegated analytics bindings
    var defaults = new SecondFunnel.classRegistry.EventManager(SecondFunnel.tracker.defaultEventMap),
        customs = new SecondFunnel.classRegistry.EventManager(options.events);
});

SecondFunnel.addInitializer(function (options) {
    if (SecondFunnel.option('debug', false) > 5) {
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

SecondFunnel.addInitializer(function (options) {
    try {
        var fa = new SecondFunnel.classRegistry.FeaturedAreaView();
        fa.render();
        broadcast('featureAreaRendered', fa);
    } catch (err) {
        // marionette throws an error if no hero templates are found or needed.
        // it is safe to ignore it.
        broadcast('featureAreaNotRendered');
    }
});

SecondFunnel.addInitializer(function (options) {
    // Add our initializer, this allows us to pass a series of tiles
    // to be displayed immediately (and first) on the landing page.
    broadcast('beforeInit', options, SecondFunnel);

    $('.brand-label').text(options.store.displayName ||
                           _.capitalize(options.store.name) ||
                           'Brand Name');

    SecondFunnel.discovery = new SecondFunnel.classRegistry.Discovery(options);
    SecondFunnel.tracker.init();
    broadcast('finished', options, SecondFunnel);
});