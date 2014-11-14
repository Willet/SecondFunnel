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
    // Enable mobile categories
    App.addRegions({
        'mobileCategoryArea': '#mobile-category-area'
    });

    var mc = new App.core.MobileCategoryCollectionView();
    App.mobileCategoryArea.show(mc);

    // Because the mobile categories follow a different pattern than desktop
    // we have to build the drop-downs
    // Convert categories into drop-downs
    var mobileCatEls = $("#mobile-category-area .category-area").children();
    
    var keepCatEls = mobileCatEls.slice(0,2), // 1st two will be our new categories
        subCatEls = mobileCatEls.slice(2); // the rest will be our sub-categories
    keepCatEls.append("<div class='sub-categories'></div>");
    subCatEls.removeClass('category').addClass('sub-category');

    while(subCatEls) {
        $(keepCatEls[0]).find('.sub-categories').append(subCatEls[0]);
        $(keepCatEls[1]).find('.sub-categories').append(subCatEls[1]);
    }

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

    // Enable sticky categories once document is ready
    $(document).ready(function() {
        var catArea = $("#category-area"),
            fixedCatArea = $("#category-area-fixed"),
            fixedContainer = fixedCatArea.find('.container'),
            mobileCatArea = $("#mobile-category-area"),
            fixedMobileCatArea = $("#mobile-category-area-fixed"),
            fixedMobileContainer = fixedMobileCatArea.find('.container');

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
        function is_mobile() {
            return ( $(window).width() < 581 );
        }
        // Initialize on pageload whichever nav is relevant
        if (is_mobile()) {
            mobileCatArea.show();
            initStickyNav(mobileCatArea, fixedMobileCatArea, fixedMobileContainer);
        } else {
            catArea.show();
            initStickyNav(catArea, fixedCatArea, fixedContainer);
        }
    });
})();