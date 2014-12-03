/**
 *  BODY SHOP AD UNIT
 **/
"use strict";

var $ = require('jquery');
require('jquery-deparam');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile

var Ad = require('ad'),
	App = Ad.App;

// Import client customizations
App.module('core', require('./views'));

// Start Application
App.init.initialize();
App.start();

(function () {
    // Update top bar
    var $topbar = $('#topbar a');
    $topbar.attr('href', App.utils.generateAdClickUrl( $topbar.attr('href') ) );
}());
