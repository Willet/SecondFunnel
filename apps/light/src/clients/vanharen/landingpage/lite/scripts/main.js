/**
 *  GAP PAGE
 **/
"use strict";

var $ = require('jquery');
var _ = require('underscore');
var waypoints = require("jquery-waypoints") // register $.fn.waypoint

var Page = require('landingpage'),
    App = Page.App;

// Import client customizations
App.module('utils', require('./utils'));
App.module('tracker', require('./tracker'));
App.module('core', require('./core.views'));
App.module('core', require('./core.models'));

// Run Application
App.init.initialize();
App.start();
