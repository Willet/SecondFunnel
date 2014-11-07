var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
require('landingpage');
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
    $(document).on('scroll', function(){
        var navbar = $("#category-area");
        if ($(window).scrollTop() > navbar.offset().top + parseInt(navbar.css('margin-top'))) {
            navbar.addClass('stuck');
        } else {
            navbar.removeClass('stuck');
        }
    });
});