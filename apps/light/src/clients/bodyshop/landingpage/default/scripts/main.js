/**
 *  BODY SHOP PAGE
 **/
"use strict";

var $ = require('jquery');
require('jquery-deparam');
require("jquery-waypoints"); // register $.fn.waypoint
require("jquery-waypoints-sticky"); // register $.fn.waypoint
var _ = require('underscore');

var Page = require('landingpage'),
    App = Page.App;

// Import client customizations
App.module('core', require('./views'));

// Run Application
App.init.initialize();
App.start();

(function () {
    // Custom Body Shop theme implementation
    var catArea = $("#category-area"),
        $snowflakes = $(document.createElement('div')).addClass('snowflakes');

    // Insert snowflakes
    catArea.append( $snowflakes.append( catArea.children().detach() ) );
    // Make category area sticky
    catArea.waypoint('sticky');

    App.utils.addUrlTrackingParameters = function (url) {
        var trackingCode = {
            'for-her':                 'for_her',
            'for-him':                 'for_him',
            'under-$10':               'under_10',
            'under-$20':               'under_20',
            'stocking-stuffers':       'stocking_stuffers'
        };
        var params = { 
            'utm_source': 'giftguide',
            'utm_medium': 'site',
            'utm_campaign': trackingCode[ App.intentRank.options.category ] || 'for_her'
        };

        return App.utils.urlAddParams(url, params);
    };
}());
