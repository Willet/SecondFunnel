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
	// Hook to add routes before initialization
	module.AppRouter = Backbone.Router.extend({
		routes: {
			'': 					 'home',
			':tile_id':				 'preview', // deprecating for /tile/:tile_id
			'preview/:tile_id': 	 'preview',
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

	        //Setting that we have been home
	        if (App.initialPage) {
	            App.initialPage = '';
	        }

	        App.previewArea.close();
	        App.intentRank.changeCategory('');
	    },
	    preview: function (tileId) {
	        App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': window.location.hash
	        }));
	        var isNumber = /^\d+$/.test(tileId);

	        if (isNumber) { // Preview the tile
	            if (App.option('debug', false)) {
	                console.warn('Router opening tile preview: '+tileId);
	            }
	            var tile = App.discovery && App.discovery.collection ?
	                App.discovery.collection.tiles[tileId] :
	                undefined;

	            App.previewLoadingScreen.show();

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
	                App.previewLoadingScreen.hide();
	                App.router.navigate('', {
	                    trigger: true,
	                    replace: true
	                });
	            });
	        } else { 
	        	// DEPRECATE THIS: Change category
	            var category = tileId;
	            if (App.option('debug', false)) {
		            console.error('Router changing category: ' + category);
		        }
		        // Ensure any preview area is closed
		        App.previewArea.close();
		        App.intentRank.changeCategory(category);
	        }
	    },
	    category: function (category) {
			if (category) {
		        if (App.option('debug', false)) {
		            console.error('Router changing category: ' + category);
		        }
		        // Ensure any preview area is closed
		        App.previewArea.close();

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
