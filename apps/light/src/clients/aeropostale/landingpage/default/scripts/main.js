/**
 *  AEROPOSTALE PAGE
 **/
"use strict";

var $ = require('jquery');
require('jquery-deparam');
var _ = require('underscore');
var waypoints = require("jquery-waypoints") // register $.fn.waypoint

var Page = require('landingpage'),
    App = Page.App;

// Import client customizations
App.module('core', require('./views'));

// Run Application
App.init.initialize();
App.start();

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

    // If Flash is disabled/not installed or Safari browser, don't show Grooveshark player
    var hasFlash = false,
        isSafari = false;
    try {
        hasFlash = Boolean(new ActiveXObject('ShockwaveFlash.ShockwaveFlash'));
    } catch(exception) {
        hasFlash = ('undefined' != typeof navigator.mimeTypes['application/x-shockwave-flash']);
    }
    isSafari = navigator.userAgent.search("Safari") >= 0 && navigator.userAgent.search("Chrome") < 0;
    if (isSafari || !hasFlash) {
        $('head').append([
                '<style type="text/css">',
                '.tile.grooveshark,',
                '.grooveshark-tile-overlay {',
                '    display: none !important;',
                '}',
                '</style>'
            ].join(" "));
    }

    App.utils.addUrlTrackingParameters = function (url) {
        var trackingCode = {
            'for-her':                 'for_her',
            'for-him':                 'for_him',
            'under-$10':               'under_10',
            'under-$10|girls':         'under_10_for_her',
            'under-$10|guys':          'under_10_for_him',
            'under-$20':               'under_20',
            'under-$20|girls':         'under_20_for_her',
            'under-$20|guys':          'under_20_for_him',
            'stocking-stuffers':       'stocking_stuffers',
            'stocking-stuffers|girls': 'stocking_stuffers_for_her',
            'stocking-stuffers|guys':  'stocking_stuffers_for_him'
        };
        var params = { 
            'utm_source': 'giftguide',
            'utm_medium': 'site',
            'utm_campaign': trackingCode[ App.intentRank.options.category ] || 'for_her'
        };

        return App.utils.urlAddParams(url, params);
    };

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
    // Check if on mobile device (Bootstrap defines mobile as 768px wide and less)
    // Alternative check: $.browser && $.browser.mobile && !App.support.isAniPad()
    if ($(window).width() <= 768) {
        // Mobile device
        // Enable mobile categories
        App.addRegions({
            'mobileCategoryArea': '#mobile-category-area'
        });
        App.mobileCategoryArea.show(new App.core.MobileCategoryCollectionView());
        // Choose mobile elements for sticky nav
        catArea = $("#mobile-category-area");
        fixedCatArea = $("#mobile-category-area-fixed");
        fixedContainer = $(".mobile-fixed-container");
        // Remove other category from view
        App.categoryArea.reset();
        App.intentRank.changeCategory = App.intentRank.changeMobileCategory;
    } else {
        // Desktop/tablet
        // Choose mobile elements for sticky nav
        catArea = $("#category-area");
        fixedCatArea = $("#category-area-fixed");
        fixedContainer = fixedCatArea.find('.container');
        // Unhide categories
        catArea.show();
    }

    // Enable sticky categories once document is ready
    $(document).ready(function() {
        // Initialize on pageload whichever nav is relevant
        initStickyNav(catArea, fixedCatArea, fixedContainer);
    });

    // Aero wants their own tracking
    window.ga('create', 'UA-53950735-1', 'auto', {'name': 'aero-tracker'});
    window.ga('aero-tracker.send', 'pageview');
})();
