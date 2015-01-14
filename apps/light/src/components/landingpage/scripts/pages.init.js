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
        
        App.addInitializer(function () {
            // set its width to whatever it began with.
            App.options.initialWidth = $(window).width();
            if (App.optimizer) { // TODO: move to optimizer
                App.optimizer.initialize();
            }
            if (App.tracker) { // TODO: move to tracker
                App.tracker.initialize();
            }

            App.vent.trigger('beforeInit', App.options, App);

            // Set up regions
            App.store = new App.core.Store(App.options.store);

            // Close any existing discoveryArea view
            if (App.discovery && App.discovery.$el) {
                // Why is this necessary?
                App.discovery.$el.empty();
                App.discovery.close();
                delete App.discovery;
            }

            // Initialize IntentRank
            // will create new discovery feed
            // TODO: refactor intentRank options
            App.intentRank.initialize({
                'category': '',
                'trigger': true
            });

            // Prevent categories from reloading
            if (!App.categoryArea.currentView) {
                var categoriesView = new App.core.CategoryCollectionView();
                App.categoryArea.show(categoriesView);
                // Global reference to the category collection
                App.categories = categoriesView.collection;
            }

            // Prevent hero image from resetting to first category on reload
            if (!App.heroArea.currentView) {
                // load the category or default hero image
                App.heroArea.show(new App.core.HeroAreaView());
            }

            App.vent.trigger('afterInit', App.options, App);
        });

        App.vent.on('afterInit', function () {
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

        App.vent.on('afterInit', function () {

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

        // On an Ajax request error, fire event
        $(document).ajaxError(function (event, request, settings) {
            App.vent.trigger('ajaxError', settings.url, App);
        });
    };
};
