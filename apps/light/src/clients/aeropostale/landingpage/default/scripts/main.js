var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
var waypoints = require("jquery-waypoints") // register $.fn.waypoint

var Page = require('landingpage');
Page.App.module('core', require('./views'));

// This should be refactored toggle classes & keep style info in css
(function() {
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
})();

$(document).ready(function() {

    var category_area = $("#category-area"),
        fixed_category_area = $("#category-area-fixed"),
        fixed_container = fixed_category_area.find('.container');

    // To avoid the page shifting when categories are removed from their container
    category_area.css('height', category_area.css('height'));

    category_area.waypoint(function (direction) {
        if (direction === 'down') {
            // If scrolling down, attach the categories to the fixed container
            fixed_container.append(category_area.children().detach());
            fixed_category_area.show();
        } else if (direction === 'up') {
            // If scrolling back up, reattach the categories to the page
            fixed_category_area.hide();
            category_area.append(fixed_container.children().detach());
        }

    });
});
