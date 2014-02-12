/*global $, _, Backbone */

/**
 * Given an instance of  Marionette Application, add initializers to it.
 * @param app
 */
function reinitialize(app) {
    "use strict";

    // setup regions if not already
    if (!app.heroArea) {
        app.addRegions({
            'heroArea': '#hero-area',
            'discoveryArea': '#discovery-area',
            'previewArea': '#preview-area'
        });
    }

    // from davidsulc/marionette-gentle-introduction
    app.navigate = app.navigate || function (route, options) {
        options = options || {};
        Backbone.history.navigate(route, options);
    };

    // from davidsulc/marionette-gentle-introduction
    app.getCurrentRoute = app.getCurrentRoute || function () {
        return Backbone.history.fragment;
    };

    app.addInitializer(function () {
        // set its width to whatever it began with.
        app.options.initialWidth = $(window).width();
    });

    app.addInitializer(function () {
        var fa = new app.core.HeroAreaView();
        app.heroArea.show(fa);

        app.vent.trigger('heroAreaRendered', fa);
    });

    app.addInitializer(function () {
        // there isn't an "view.isOpen", so this checks if the feed element
        // exists, and if it does, close the view.
        if(app.discovery && app.discovery.$el) {
            // Why is this necessary?
            app.discovery.$el.empty();
            app.discovery.close();
            delete app.discovery;
        }
    });

    app.addInitializer(function () {
        // Add our initializer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.

        $('.brand-label').text(app.option("store:displayName") ||
                               _.capitalize(app.option("store:name")) ||
                               'Brand Name');

        $(document).ajaxError(function (event, request, settings) {
            app.vent.trigger('ajaxError', settings.url, app);
        });
    });

    // from davidsulc/marionette-gentle-introduction
    app.addInitializer(function () {
        // create a discovery area with tiles in it
        app.vent.trigger('beforeInit', app.options, app);

        app.store = new app.core.Store(app.options.store);

        app.discovery = new app.core.Feed({
            options: app.options
        });
        app.discoveryArea.show(app.discovery);

        app.vent.trigger('finished', app.options, app);
    });

    app.vent.on('finished', function (data) {

        if (app.support.isAniPad()) {
            $('html').addClass('ipad');
        }
        if ($.browser.mobile && !app.support.isAniPad()) {
            $('html').addClass('mobile-phone');
        }
    });

    app.vent.on('finished',  function () {
        $(window).scroll(function () {
            var body = document.body;

            // IE
            if (!body.classList) {
                return;
            }

            if (!body.classList.contains('disable-hover')) {
                body.classList.add('disable-hover');
            }

            app.vent.on('scrollStopped', function () {
                body.classList.remove('disable-hover');
            });
        });
    });

    app.vent.on('finished', function () {
        app.router = new Backbone.Router();

        //TODO: put these routes into their own file?
        /**
         * Home route
         */
        app.router.route('', 'home', function () {
            //http://stackoverflow.com/a/5298684
            var loc = window.location;
            if (loc.href.indexOf('#') !== -1) {
                if ("replaceState" in window.history) {
                    window.history.replaceState("", document.title, loc.pathname + loc.search);
                } else {
                    //Fallback for IE 8 & 9
                    window.location = window.location.href.split('#')[0];
                }
            }
            //END http://stackoverflow.com/a/5298684

            //Setting that we have been home
            if (app.initial_page) {
                app.initial_page = '';
            }

            if (app.support.mobile()) {
                if (app.previewArea.$el.children()) {
                    $(app.previewArea.$el.children()[0]).swapWith(
                        app.discoveryArea.$el.parent());
                }

                app.layoutEngine.layout(app.discovery);
            }
            app.previewArea.close();
        });

        /**
         * Adding the router for tile views
         */
        app.router.route(':tile_id', 'tile', function (tile_id) {
            var tile = new app.core.Tile({
                'tile-id': tile_id
            });

            tile.fetch().done(function () {
                var TileClass = app.utils.findClass('Tile',
                        tile.get('type') || tile.get('template'), app.core.Tile);
                tile = new TileClass(TileClass.prototype.parse.call(this, tile.toJSON()));

                var preview = new app.core.PreviewWindow({
                    'model': tile
                });
                app.previewArea.show(preview);
            }).fail(function () {
                app.router.navigate('', {
                    trigger: true,
                    replace: true
                });
            });
        });

        Backbone.history.start();
        //Making sure we know where we came from.
        app.initial_page = window.location.hash;
    });
}

// auto-initialise existing instance on script inclusion
reinitialize(window.App);
