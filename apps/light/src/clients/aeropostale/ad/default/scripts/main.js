var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
require('jquery-deparam');

var Ad = require('ad'),
	App = Ad.App;

App.module('core', require('./views'));

(function () {
    // Update top bar
    $topbar = $('#topbar a');
    $topbar.attr('href', App.utils.generateAdClickUrl( $topbar.attr('href') ) );
}());
