var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
require('landingpage');
(function() {
    if (navigator.platform.toLowerCase().indexOf('windows') == -1) {
        $(".tile .buy .button, .previewContainer .buy .button").css({'padding-top': '18px'});
    }
})()
