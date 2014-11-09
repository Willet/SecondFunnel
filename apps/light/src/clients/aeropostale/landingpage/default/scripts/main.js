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
        var category_area = $("#category-area");
        var category_area_fixed = $("#category-area-fixed")
        var height = navbar.offset().top;
        if ($(window).scrollTop() + parseInt(navbar.css('margin-top')) >= height) {
            category_area_fixed.css({'display': 'block'});
            category_area_fixed.append(category_area.detach('span, div'));

        } else {
            category_area_fixed.css({'display': 'none'});
            category_area.append(category_area_fixed.detach('span, div'));
        }
    });
});