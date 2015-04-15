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

// Run Application
App.init.initialize();
App.start();

(function () {
	var $topNavWrappers = $('.topNavWrapper'),
		$topSecNavWrappers = $('.topSecNavWrapper'),
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

	// Send search bar inqueries to surlatable.com
	$('#submit-search').click(function(ev){
		var searchUrl,
			$this = $(this),
			$inputBox = $this.siblings().first(),
			$topNavSearch = $this.parents('#topNavSearch');
		if ($topNavSearch.length && $inputBox.length) {
			searchUrl = $topNavSearch.data('nonsecureurl') + "?Ntt=" + $inputBox.val();
			App.utils.openUrl(searchUrl, "_top");
		}
		return false;
	});
	
	// Hide categories when something is clicked
	$(document).click(function () {
		$topNavWrappers.removeClass('expanded');
		$categories.removeClass('expanded');
		return true;
	});
}());
