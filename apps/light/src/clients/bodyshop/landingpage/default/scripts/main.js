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
App.module('utils', require('./utils'));
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
}());
