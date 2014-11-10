var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
require('landingpage');
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
    $(document).on('scroll', function(){
        function scrolled_beyond_navbar() {
            return $(window).scrollTop() + parseInt(category_area.css('margin-top')) > category_area.offset().top;
        }

        var category_area = $("#category-area"),
            fixed_category_area = $("#category-area-fixed"),
            fixed_container = fixed_category_area.find('.container');
        
        if (scrolled_beyond_navbar()) {
            fixed_container.append(category_area.children().detach());
            fixed_category_area.show();
        } else {
            fixed_category_area.hide();
            category_area.append(fixed_container.children().detach());
        }
    });
});