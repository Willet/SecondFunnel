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
	App.vent.on('route', function (route, name) {
		if (App.option('debug', false)) {
            console.warn('Route: '+route+' Name: '+name);
        }
	});
	
	// Route app to home
	var return_home = function () {
		if (App.option('debug', false)) {
            console.error('Router failed to find tile, redirecting to home');
        }

        App.previewLoadingScreen.hide();
        App.previewArea.empty();

        App.router.navigate('', {
            trigger: true,
            replace: true
        });
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
			// Update category to home
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

	        App.previewArea.empty();
	        App.previewLoadingScreen.hide();
	        App.intentRank.changeCategory('');
	    },
	    tile: function (tileId) {
	    	// Load tile into hero area
	    	App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': window.location.hash
	        }));

	        var feature_tile = function (tile) {
	        	var heroArea = new App.core.HeroAreaView({tile: tile.attributes});
	            App.heroArea.show(heroArea);
	        };

	        // Ensure any preview area is closed
	        App.previewArea.empty();
	        App.previewLoadingScreen.hide();
	        App.core.Tile.getTileById(tileId, feature_tile, return_home);
	    },
	    preview: function (tileId) {
	    	// Load tile in pop-up preview
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
            App.core.Tile.getTileById(tileId, preview_tile, return_home);
	    },
	    category: function (category) {
	    	// Load category
	    	App.utils.postExternalMessage(JSON.stringify({
	            'type': 'hash_change',
	            'hash': window.location.hash
	        }));
	        // Ensure any preview area is closed
	        App.previewArea.empty();
	        App.previewLoadingScreen.hide();

			if (category) {
		        if (App.option('debug', false)) {
		            console.warn('Router changing category: ' + category);
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
	   	Backbone.history.start({
	   		'pushState': true,
	   		'root': '/' + App.option('page:slug')
	   	});
	};
};
