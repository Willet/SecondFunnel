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
    // Wrap links with CJ link
    var re = /^https?\:\/\/www\.ebags\.com/i;
    $('a').each(function (el) {
        if (this.href.match(re)) {
            $(this).on('click', function () {
                App.vent.trigger("tracking:page:externalUrlClick", this.href, "nav");
                App.utils.openUrl(this.href, "_top");
                return false;
            });
        }
    });

    var searchSubmit = function ($this) {
        var searchUrl,
            baseUrl = "http://www.ebags.com/search?term=",
            $searchBar = $this.is('#search-bar') ? $this : $this.parents('#search-bar'),
            $inputBox = $searchBar.find('input').first();
        searchUrl = baseUrl + $inputBox.val();
        App.vent.trigger("tracking:page:externalUrlClick", searchUrl, "search-bar");
        App.utils.openUrl(searchUrl, "_top");
        return false;
    };

    // Send search bar inqueries to ebags.com
    $('#search-bar button').click(function (ev){
        searchSubmit($(this));
    });
    $('#search-bar').keypress(function (ev) {
        // Enter button
        if(ev.keyCode == 13){
            searchSubmit($(this));
            ev.preventDefault();
            return false;
        }
    });

    // Close categories if clicked
    var $catCloser = $('<div/>', { id: 'category-closer' }).appendTo('#category-area');
    $catCloser.on('click', function () {
        $catCloser.hide();
        $('.category.expanded').removeClass('expanded');
    });
    App.vent.on('categories:expanded', function () { $catCloser.show() });
    App.vent.on('categories:contracted', function () { $catCloser.hide() });
}());
