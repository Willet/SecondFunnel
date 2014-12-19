"use strict";

/**
 * Given an instance of  Marionette Application, add initializers to it.
 * @param app
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

    // Run this before App.start();
    module.initialize = function () {
        // setup regions if not already
        if (!App._initialized) {
            App.addRegions({
                'heroArea': '#hero-area',
                'categoryArea': '#category-area',
                'discoveryArea': '#discovery-area',
                'previewArea': '#preview-area'
            });
            App._initialized = true;
        }

        // TODO investigate turning into region?
        // Toggle with .show() and .hide()
        App.previewLoadingScreen = $('#preview-loading');

        App.vent.on('initRouter', function () {
            var loc = window.location.href; // reference to current url
            
            App.router.initialize();

            // Making sure we know where we came from.
            App.initialPage = window.location.hash;
            if (App.initialPage !== '' && App.support.mobile()) {
                // If on mobile push the state to the history stack
                if ('replaceState' in window.history) {
                    // back button closes the popup
                    window.history.replaceState('', document.title, loc.split('#')[0]);
                    window.history.pushState({}, '', loc);
                }
            }
        });


        App.addInitializer(function () {
            // set its width to whatever it began with.
            App.options.initialWidth = $(window).width();
            if (App.optimizer) { // TODO: move to optimizer
                App.optimizer.initialize();
            }
            if (App.tracker) { // TODO: move to tracker
                App.tracker.initialize();
            }

            App.categories = new App.core.CategoryCollectionView();
            App.categoryArea.show(App.categories);

            // there isn't an "view.isOpen", so this checks if the feed element
            // exists, and if it does, close the view.
            if(App.discovery && App.discovery.$el) {
                // Why is this necessary?
                App.discovery.$el.empty();
                App.discovery.close();
                delete App.discovery;
            }

            // Add our initializer, this allows us to pass a series of tiles
            // to be displayed immediately (and first) on the landing page.

            $('.brand-label').text(App.option('store:displayName') ||
                                   _.capitalize(App.option('store:name')) ||
                                   'Brand Name');

            $(document).ajaxError(function (event, request, settings) {
                App.vent.trigger('ajaxError', settings.url, App);
            });
        });


        // from davidsulc/marionette-gentle-introduction
        App.addInitializer(function () {
            // create a discovery area with tiles in it
            App.vent.trigger('beforeInit', App.options, App);

            App.store = new App.core.Store(App.options.store);

            App.discovery = new App.feed.MasonryFeedView( App.options );
            App.discoveryArea.show(App.discovery);

            App.vent.trigger('initRouter', App.options, App);

            App.vent.trigger('finished', App.options, App);

            // prevent hero image from resetting to first category on reload
            if (!App.heroArea.currentView) {
                // load the default hero image
                App.heroArea.show(new App.core.HeroAreaView());
            }
        });

        App.vent.on('finished', function (data) {

            if (App.support.isAniPad()) {
                $('html').addClass('ipad');
            }
            if ($.browser && $.browser.mobile && !App.support.isAniPad()) {
                $('html').addClass('mobile-phone');
            }

            if (App.support.isAniPad() || App.support.isAnAndroid()) {
                $('html').addClass('tablet');
            }

            $(window).scroll(function () {
                $('body').addClass('disable-hover');
            });

            App.vent.on('scrollStopped', function () {
                $('body').removeClass('disable-hover');
            });
        });
    };
};
