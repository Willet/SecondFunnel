"use strict";

/**
 * Router for landing pages
 *
 * Before calling module.initialize, routes can be added to module.AppRouter
 * After calling module.initialize, the module is overwritten into a Backbone.Router instance
 *
 * @param app
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

	// Route app to home
	var return_home = function () {
		if (App.option('debug', false)) {
            console.error('Router failed to find tile, redirecting to home');
        }

        App.previewLoadingScreen.hide();
        App.previewArea.close();

        App.router.navigate('', {
            trigger: true,
            replace: true
        });
    };

    /* 
     * Attempt to retrieve tile, then execute success_cb or failure_cb
     *   tileId - <string>
     *   success_cb - <function> (<Tile>)
     *   failure_cb - <function>: ()
     */
    var get_tile = function (tileId, success_cb, failure_cb) {
    	var isNumber = /^\d+$/.test(tileId);

        if (isNumber) {
        	if (App.option('debug', false)) {
                console.warn('Router getting tile: '+tileId);
            }
            var tile = App.discovery && App.discovery.collection ?
                App.discovery.collection.tiles[tileId] :
                undefined;

            if (tile !== undefined) {
                success_cb(tile);
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

                success_cb(tile);
            }).fail(failure_cb);
        } else {
        	failure_cb();
        }
	};

	// Hook to add routes before initialization
	module.AppRouter = Backbone.Router.extend({
		routes: {
			'': 					 'home',
			'tile/:tile_id':  		 'tile', // tile hero area
			'preview/:tile_id': 	 'preview', // preview pop-up
			'category/:category_id': 'category'
		},
		home: function () {
	        App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': '#'
	        }));
	        //http://stackoverflow.com/a/5298684
	        var loc = window.location;
	        if (loc.href.indexOf('#') > -1) {
	            if ('replaceState' in window.history) {
	                window.history.replaceState('', document.title, loc.pathname + loc.search);
	            } else {
	                //Fallback for IE 8 & 9
	                window.location = loc.href.split('#')[0];
	            }
	        }

	        // Setting that we have been home
	        if (App.initialPage) {
	            App.initialPage = '';
	        }

	        App.previewArea.close();
	        App.intentRank.changeCategory('');
	    },
	    tile: function (tileId) {
	    	App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': window.location.hash
	        }));

	        var feature_tile = function (tile) {
	        	var heroArea = new App.core.HeroAreaView(tile.attributes);
	            App.heroArea.show(heroArea);
	        };

	        // Ensure any preview area is closed
	        App.previewArea.close();
	        App.previewLoadingScreen.hide();
	        get_tile(tileId, feature_tile, return_home);
	    },
	    preview: function (tileId) {
	        App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': window.location.hash
	        }));

	        var preview_tile = function (tile) {
	        	var preview = new App.core.PreviewWindow({
                    'model': tile
                });
                App.previewArea.show(preview);
            };

            App.previewLoadingScreen.show();
            get_tile(tileId, preview_tile, return_home);
	    },
	    category: function (category) {
	    	App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': window.location.hash
	        }));
	        // Ensure any preview area is closed
	        App.previewArea.close();

			if (category) {
		        if (App.option('debug', false)) {
		            console.error('Router changing category: ' + category);
		        }

		        // Update regions
		        // this emits a 'category:change' event that triggers updates
		        // of the other regions
		        App.intentRank.changeCategory(category);
		    } else {
		    	App.router.navigate('', {
	                trigger: true,
	                replace: true
	            });
		    }
	    }
	});

	// initializes replaces the module with the Router
	module.initialize = function () {
		App.router = new module.AppRouter();

		// Start history
	   	Backbone.history.start();
	};
};
