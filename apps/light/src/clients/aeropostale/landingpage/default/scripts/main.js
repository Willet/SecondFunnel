/**
 *  AEROPOSTALE PAGE
 **/
"use strict";

var $ = require('jquery');
require('jquery-deparam');
require("jquery-waypoints"); // register $.fn.waypoint
require("jquery-waypoints-sticky"); // register $.fn.waypoint
var _ = require('underscore');

var Page = require('landingpage'),
    App = Page.App;

// Import client customizations
App.module('core', require('./core.views'));
App.module('utils', require('./utils'));

// Run Application
App.init.initialize();
App.start();

(function () {
    // Custom Aero theme implementation
    
    // Hero area complete, show categories
    $("#category-area").show().waypoint('sticky');

    // Fix for the font rendering strangley on anything but windows
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

    // If Flash is disabled/not installed or Safari browser, don't show Grooveshark player
    var hasFlash = false,
        isSafari = false;
    try {
        hasFlash = Boolean(new ActiveXObject('ShockwaveFlash.ShockwaveFlash'));
    } catch(exception) {
        hasFlash = ('undefined' != typeof navigator.mimeTypes['application/x-shockwave-flash']);
    }
    isSafari = navigator.userAgent.search("Safari") >= 0 && navigator.userAgent.search("Chrome") < 0;
    if (isSafari || !hasFlash) {
        $('head').append([
                '<style type="text/css">',
                '.tile.grooveshark,',
                '.grooveshark-tile-overlay {',
                '    display: none !important;',
                '}',
                '</style>'
            ].join(" "));
    }
    
    $(document).ready(function() {
        // Aero wants their own tracking
        window.ga('create', 'UA-53950735-1', 'auto', {'name': 'aeroTracker'});
        window.ga('aeroTracker.send', 'pageview');
    });
})();
