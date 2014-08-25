'use strict';

var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');

/**
 * Given an instance of  Marionette Application, add initializers to it.
 * @param app
 */
module.exports.reinitialize = function (App) {

    // setup regions if not already
    if (!App.heroArea) {
        App.addRegions({
            'heroArea': '#hero-area',
            'categoryArea': '#category-area',
            'discoveryArea': '#discovery-area',
            'previewArea': '#preview-area'
        });
    }

    // from davidsulc/marionette-gentle-introduction
    App.navigate = App.navigate || function (route, options) {
        options = options || {};
        Backbone.history.navigate(route, options);
    };

    // from davidsulc/marionette-gentle-introduction
    App.getCurrentRoute = App.getCurrentRoute || function () {
        return Backbone.history.fragment;
    };

    App.addInitializer(function () {
        // set its width to whatever it began with.
        App.options.initialWidth = $(window).width();
        if (App.optimizer) { // TODO: move to optimizer
            App.optimizer.initialize();
        }
        if (App.tracker) { // TODO: move to tracker
            App.tracker.initialize();
        }
    });

    App.addInitializer(function () {
        var ca = new App.core.CategoryCollectionView();
        App.categoryArea.show(ca);
    });

    App.addInitializer(function () {
        // there isn't an "view.isOpen", so this checks if the feed element
        // exists, and if it does, close the view.
        if(App.discovery && App.discovery.$el) {
            // Why is this necessary?
            App.discovery.$el.empty();
            App.discovery.close();
            delete App.discovery;
        }
    });

    App.addInitializer(function () {
        // Add our initializer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.

        $('.brand-label').text(App.option('store:displayName') ||
                               _.capitalize(App.option('store:name')) ||
                               'Brand Name');

        $(document).ajaxError(function (event, request, settings) {
            App.vent.trigger('ajaxError', settings.url, App);
        });
    });

    App.vent.on('initRouter', function () {
        var loc = window.location.href, // reference to current url
            previewLoadingScreen = $('#preview-loading');
        App.router = new Backbone.Router();

        //TODO: put these routes into their own file?
        /**
         * Home route
         */
        App.router.route('', 'home', function () {
            App.utils.postExternalMessage(JSON.stringify({
                'type': 'hash_change',
                'hash': '#'
            }));
            //http://stackoverflow.com/a/5298684
            var loc = window.location;
            if (loc.href.indexOf('#') !== -1) {
                if ('replaceState' in window.history) {
                    window.history.replaceState('', document.title, loc.pathname + loc.search);
                } else {
                    //Fallback for IE 8 & 9
                    window.location = loc.href.split('#')[0];
                }
            }
            //END http://stackoverflow.com/a/5298684

            //Setting that we have been home
            if (App.initialPage) {
                App.initialPage = '';
            }

            App.previewArea.close();
        });

        /**
         * Adding the router for tile views
         */
        App.router.route(':tile_id', 'tile', function (tileId) {
            App.utils.postExternalMessage(JSON.stringify({
                'type': 'hash_change',
                'hash': window.location.hash
            }));

            var tile = App.discovery && App.discovery.collection ?
                App.discovery.collection.tiles[tileId] :
                undefined;

            previewLoadingScreen.show();

            if (tile !== undefined) {
                var preview = new App.core.PreviewWindow({
                    'model': tile
                });
                App.previewArea.show(preview);
                return;
            }

            console.debug('tile not found, fetching from IR.');

            tile = new App.core.Tile({
                'tile-id': tileId
            });

            tile.fetch().done(function () {
                var TileClass = App.utils.findClass('Tile',
                        tile.get('type') || tile.get('template'), App.core.Tile);
                tile = new TileClass(TileClass.prototype.parse.call(this, tile.toJSON()));

                var preview = new App.core.PreviewWindow({
                    'model': tile
                });
                App.previewArea.show(preview);
            }).fail(function () {
                previewLoadingScreen.hide();
                App.router.navigate('', {
                    trigger: true,
                    replace: true
                });
            });
        });

        Backbone.history.start();

        //Making sure we know where we came from.
        App.initialPage = window.location.hash;
        if (App.initialPage !== '' && App.support.mobile()) {
            // if on mobile push the state to the history stack
            if ('replaceState' in window.history) {
                // back button closes the popup
                window.history.replaceState('', document.title, loc.split('#')[0]);
                window.history.pushState({}, '', loc);
            }
        }
    });

    // from davidsulc/marionette-gentle-introduction
    App.addInitializer(function () {
        // create a discovery area with tiles in it
        App.vent.trigger('beforeInit', App.options, App);

        App.store = new App.core.Store(App.options.store);

        App.discovery = new App.feed.MasonryFeedView({
            options: App.options
        });
        App.discoveryArea.show(App.discovery);

        App.vent.trigger('initRouter', App.options, App);

        App.vent.trigger('finished', App.options, App);

        var fa = new App.core.HeroAreaView();
        App.heroArea.show(fa);
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
