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
App.module('core', require('./core.views.tiles'));

// Run Application
App.init.initialize();
App.start();

(function () {
    // Wrap SLT links with CJ link
    var re = /^https?\:\/\/www\.surlatable\.com/i;
    $('a').each(function (el) {
        if (this.href.match(re)) {
            this.href = 'http://www.qksrv.net/links/7774943/type/am/sid/' +
                        App.option('page:slug') + '/' + this.href;
        }
    });

    var $topNavWrappers = $('.topNavWrapper'),
        $topSecNavWrappers = $('.topSecNavWrapper'),
        $topProductSecNavPromo = $('.topProductSecNavPromo'),
        $categories = $('.category'),
        $subcategories = $('.sub-categories');

    // Enable drop-down nav categories
    $topNavWrappers.click(function (ev) {
        var $topNavHref,
            $this = $(this),
            $target = $(ev.target),
            $topNavWrapper = $this.hasClass('topNavWrapper') ? $this : $this.parents('.topNavWrapper');
        // Redirect tab
        if ($topNavWrapper.hasClass('topNavHref')) {
            return true;
        }
        // Drop-down tab
        $topNavHref = $target.hasClass('topNavHref') ? $target : $target.parents('.topNavHref');
        if ($topNavHref.length > 0) {
            // if the clicked item is part of a topNavHref, then redirect
            return true;
        } else {
            // the topNavWrapper was clicked, expand/hide the drop-down
            if ($this.hasClass('expanded')) {
                $this.removeClass('expanded');
                $this.find('.expanded').removeClass('expanded');
            } else {
                $('.topNavWrapper').removeClass('expanded');
                $this.addClass('expanded');
            }
            return false;
        }
    });

    // Enable tertiary side tab for 2nd navbar
    $topSecNavWrappers.click(function (ev) {
        var $topNavHref,
            $this = $(this),
            $target = $(ev.target),
            $topNavWrapper = $this.hasClass('topNavWrapper') ? $this : $this.parents('.topNavWrapper');
        // Redirect tab
        if ($topNavWrapper.hasClass('topNavHref')) {
            return true;
        }
        // Side tab
        $topNavHref = $target.hasClass('topNavHref') ? $target : $target.parents('.topNavHref');
        if ($topNavHref.length) {
            // if the clicked item is part of a topNavHref, then redirect
            return true;
        } else {
            // the topNavWrapper was clicked, expand/hide the drop-down
            if ($this.hasClass('expanded')) {
                $this.removeClass('expanded');
            } else {
                $('.topSecNavWrapper').removeClass('expanded');
                $this.addClass('expanded');
            }
            return false;
        }
    });

    $topProductSecNavPromo.click(function (ev) {
        App.utils.openUrl(this.href, "_top");
        return false;
    });

    // Send search bar inqueries to surlatable.com
    $('#submit-search').click(function(ev){
        var searchUrl,
            baseUrl = "http://www.anrdoezrs.net/links/7774943/sid/" +
                      App.option('page:slug') +
                      "/type/dlg/http://www.surlatable.com/search/search.jsp",
            $this = $(this),
            $inputBox = $this.siblings().first(),
            $topNavSearch = $this.parents('#topNavSearch');
        if ($topNavSearch.length && $inputBox.length) {
            searchUrl = baseUrl + "?Ntt=" + $inputBox.val();
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
    
    // Hide categories when something is clicked
    $(document).click(function () {
        $topNavWrappers.removeClass('expanded');
        $categories.removeClass('expanded');
        return true;
    });
}());
