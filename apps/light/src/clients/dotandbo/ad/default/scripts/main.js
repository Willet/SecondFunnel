/**
 *  DOT & BO AD UNIT
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

// Start Application
App.init.initialize();
App.start();