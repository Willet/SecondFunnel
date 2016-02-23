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
            var tileId;

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
                App.discovery.destroy();
                delete App.discovery;
            }

            // Prevent categories from reloading
            if (!App.categoryArea.currentView) {
                // Get appropriate categories for this page
                var catArr = App.option("page:categories", []),
                    mobileCatArr = App.option("page:mobileCategories", [])
                if (App.support.mobile() && _.isArray(mobileCatArr) && !_.isEmpty(mobileCatArr)) {
                    catArr = mobileCatArr;
                }

                var categoriesView = new App.core.CategoryCollectionView({categories: catArr});
                if (categoriesView.collection.length) {
                    App.categoryArea.show(categoriesView);
                }
                // Global reference to the category collection
                App.categories = categoriesView.collection;
            }

            // Initialize IntentRank
            // will create new discovery feed
            var homeCat = App.option('page:home:category', '');
            if (App.support.mobile() && App.option('page:mobileHome:category', '')) {
                homeCat = App.option('page:mobileHome:category');
            }
            App.intentRank.initialize({
                'category': App.option('page:init:category', homeCat),
                'trigger': true
            });

            // Now that App.feed is set up, preload tile models
            // Must happen before hero initialization
            if (window.PRELOAD && _.isArray(window.PRELOAD.tiles)) {
                _.each(window.PRELOAD.tiles, function (tile) {
                    App.core.Tile.cacheTile(tile);
                });
            }

            // Prevent hero image from resetting to first category on reload
            if (!App.heroArea.currentView) {
                var homeHero = App.option('page:home:hero', null);
                if (App.support.mobile() && App.option('page:mobileHome:hero', null)) {
                    homeHero = App.option('page:mobileHome:hero');
                }

                tileId = App.option('page:init:hero', homeHero);
                if (App.utils.isNumber(tileId)) {
                    App.heroArea.show(new App.core.HeroAreaView({tileId: tileId}));
                } else {
                    // load the category or default hero image
                    App.heroArea.show(new App.core.HeroAreaView());
                }
            }

            if (App.option('page:init:preview')) {
                tileId = App.option('page:init:preview');
                var preview_tile = function (tile) {
                    var preview = new App.core.PreviewWindow({
                        'model': tile
                    });
                    App.previewArea.show(preview);
                };
                var close_preview = function () {
                    App.previewLoadingScreen.hide();
                };
                App.previewLoadingScreen.show();
                App.core.Tile.getById(tileId, preview_tile, close_preview);
            }

            App.vent.trigger('afterInit', App.options, App);
        });

        App.vent.on('afterInit', function () {
            var loc = window.location.href; // reference to current url
            
            App.router.initialize();

            // Making sure we know where we came from
            App.initialPage = App.utils.getRoute();
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
