var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
var waypoints = require("jquery-waypoints") // register $.fn.waypoint

var Page = require('landingpage'),
    App = Page.App;
App.module('core', require('./views'));

(function () {
    // Custom Aero theme implementation

    // Fix for the font rendering strangley on anything but windows
    if (navigator.platform.toLowerCase().indexOf('win') != 0) {
        $('head').append(
            [
                '<style type="text/css">',
                '.tile .buy .button, .previewContainer .buy .button {',
                '	padding-top: 18px;',
                '}',
                '@media (max-width: 768px) {',
                '	.tile .buy .button, .previewContainer .buy .button {',
                '		padding-top: 16px;',
                '	}',
                '}',
                '</style>'
            ].join(" ")
        );
    }

    // If Flash is disabled/not installed, don't show Grooveshark player
    var hasFlash = false;
    try {
        hasFlash = Boolean(new ActiveXObject('ShockwaveFlash.ShockwaveFlash'));
    } catch(exception) {
        hasFlash = ('undefined' != typeof navigator.mimeTypes['application/x-shockwave-flash']);
    }
    if (!hasFlash) {
        $('head').append([
                '<style type="text/css">',
                '.tile.grooveshark,',
                '.grooveshark-tile-overlay {',
                '    display: none !important;',
                '}',
                '</style>'
            ].join(" "));
    }

    // ### Aero mobile nav ###
    // requires a new change category function because sub-categories
    // are categories, not filters on categories
    App.intentRank.changeMobileCategory = function (category) {

        var intentRank = App.intentRank;

        if ($('.category-area span').length < 1) {
            return intentRank;
        }
        if (category === '') {
            if (App.option("categoryHome") && App.option("categoryHome").length ) {
                category = App.option("categoryHome");
            } else {
                category = $('.category-area span:first').attr('data-name');
            }
        }

        if (intentRank.options.category === category) {
            return intentRank;
        }

        // Change the category, category is a string passed to data
        intentRank.options.category = category;
        intentRank.options.IRReset = true;
        App.tracker.changeCategory(category);

        App.vent.trigger('change:category', category, category);

        App.discovery = new App.feed.MasonryFeedView({
            options: App.options
        });
        $(".loading").show();
        App.discoveryArea.show(App.discovery);

        var categorySpan = $('.category-area span[data-name="' + category + '"]');
        categorySpan.trigger("click");

        return intentRank;
    };

    // Helper function for Aero sticky nav
    function initStickyNav (home_hook, fixed_holder, fixed_hook) {
        // To avoid the page shifting when categories are removed from their container
        home_hook.css('height', home_hook.css('height'));
        home_hook.waypoint(function (direction) {
            if (direction === 'down') {
                // If scrolling down, attach the categories to the fixed container
                fixed_hook.append(home_hook.children().detach());
                fixed_holder.show();
            } else if (direction === 'up') {
                // If scrolling back up, reattach the categories to the page
                fixed_holder.hide();
                home_hook.append(fixed_hook.children().detach());
            }

        });
    }

    var catArea, fixedCatArea, fixedContainer;
    //if ($.browser && $.browser.mobile && !App.support.isAniPad()) {
    if (true) {
        // Enable mobile categories
        App.addRegions({
            'mobileCategoryArea': '#mobile-category-area'
        });
        App.mobileCategoryArea.show(new App.core.MobileCategoryCollectionView());
        // Mobile device
        catArea = $("#mobile-category-area");
        fixedCatArea = $("#mobile-category-area-fixed");
        fixedContainer = $(".mobile-fixed-container");
        App.categoryArea.reset(); // Remove other category from view
        App.intentRank.changeCategory = App.intentRank.changeMobileCategory;
    } else {
        // Desktop/tablet
        catArea = $("#category-area");
        fixedCatArea = $("#category-area-fixed");
        fixedContainer = fixedCatArea.find('.container');
        catArea.show(); // It loads as display: none;
    }

    // Enable sticky categories once document is ready
    $(document).ready(function() {
        // Initialize on pageload whichever nav is relevant
        initStickyNav(catArea, fixedCatArea, fixedContainer);
    });
})();
