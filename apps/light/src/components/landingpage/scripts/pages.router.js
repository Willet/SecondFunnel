"use strict";

/**
 * Router for landing pages
 * @param app
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {
	module.initialize = function () {
		module = new Backbone.Router({
			'': 					 'home',
			':tile_id':				 'preview', // deprecating for /tile/:tile_id
			'preview/:tile_id': 	 'preview',
			'category/:category_id': 'category'
		});

	    module.home = function () {
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
	    };

	   	module.preview = function (tileId) {
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
	        } else { 
	        	// Deprecated: Change category
	            module.category(tileId);
	        }
	    };

		module.category = function (category) {
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
	    };

	    // Start history
	   	Backbone.history.start();
	};
};
