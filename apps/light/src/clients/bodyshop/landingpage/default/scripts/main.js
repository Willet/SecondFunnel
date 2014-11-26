/**
 *  BODY SHOP PAGE
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
    // Custom Body Shop theme implementation

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