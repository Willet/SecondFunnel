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
    // Send search bar inqueries to surlatable.com
    $('#submit-search').click(function(ev){
        var searchUrl,
            $this = $(this),
            $inputBox = $this.siblings().first(),
            $topNavSearch = $this.parents('#search-bar');
        if ($topNavSearch.length && $inputBox.length) {
            searchUrl = $topNavSearch.data('nonsecureurl') + "?Ntt=" + $inputBox.val();
            App.utils.openUrl(searchUrl, "_top");
        }
        return false;
    });
    $('#searchQuestionDisplayed').keypress(function(ev) {
        // Enter button
        if(event.keyCode == 13){
            $('#submit-search').click();
        }
    });
}());
