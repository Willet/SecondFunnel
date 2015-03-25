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
			} else {
				$this.addClass('expanded').siblings().removeClass('expanded');
			}
			return false;
		}
	});

	// Remove the top level click handler for this page
	// We want nav links to open in this window
	$(document).off('click');
	// Hide categories when something is clicked
	$(document).click(function () {
		$topNavWrappers.removeClass('expanded');
		$categories.removeClass('expanded');
		return true;
	});
}());
