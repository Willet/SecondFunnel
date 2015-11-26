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
App.module('core', require('./core.models'));
App.module('core', require('./core.views'));

// Run Application
App.init.initialize();
App.start();

(function () {
    // Wrap links with click handler
    var re = /^https?\:\/\/(?:www|m)\.thebodyshop-usa\.com/i,
        onclick = function (el) {
            App.utils.openUrl(this.href, "_top");
            return false;
        };
    $('a').each(function (el) {
        if (this.href.match(re)) {
            this.click = onclick;
        }
    });

    // Send search bar inqueries to thebodyshop-usa.com
    $('#submit-search').click(function(ev){
        var searchUrl,
            domain = App.support.mobile() ? "m" : "www",
            baseUrl = "http://" + domain + ".thebodyshop-usa.com/search.aspx",
            $this = $(this),
            $inputBox = $this.siblings().first(),
            $topNavSearch = $this.parents('#search-bar');
        if ($topNavSearch.length && $inputBox.length) {
            searchUrl = baseUrl + "?q=" + $inputBox.val();
            App.vent.trigger("tracking:page:externalUrlClick", searchUrl, "search-bar");
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

    // Open mobile category menu
    $('.category-menu').click(function(ev){
        $('#category-area').addClass('visible');
        setTimeout("$('#category-area').addClass('expanded');", 10);
        App.vent.trigger('categories:expanded')
    });

    // Close categories if clicked
    var $catCloser = $('<div/>', { id: 'category-closer' }).appendTo('#category-area');
    $catCloser.on('click', function () {
        App.vent.trigger('categories:contracted');
    });
    App.vent.on('categories:expanded', function () { $catCloser.show() });
    App.vent.on('categories:contracted', function () { 
        $catCloser.hide();
        $('#category-area.expanded').removeClass('expanded');
        setTimeout("$('#category-area').removeClass('visible');", 300);
    });
}());
