/**
 *  SUR LA TABLE PAGE
 **/
"use strict";

var $ = require('jquery');
var _ = require('underscore');
var waypoints = require("jquery-waypoints") // register $.fn.waypoint

var Page = require('landingpage'),
    App = Page.App;

// Import client customizations
App.module('utils', require('./utils'));
App.module('core', require('./core.views'));
App.module('core', require('./core.views.tiles'));

App.core.HeroAreaView = App.core.SLTHeroAreaView;

// Run Application
App.init.initialize();
App.start();

(function () {
}());
