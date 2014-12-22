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
App.module('core', require('./core.views'));
App.core.HeroAreaView = App.core.SLTHeroAreaView;

// Run Application
App.init.initialize();
App.start();

(function () {
	var $topNavWrappers = $('.topNavWrapper'),
		$categories = $('.category'),
		$subcategories = $('.sub-categories');

	// Enable drop-down nav categories
	$topNavWrappers.click(function () {
		var $this = $(this);
		$this = $this.hasClass('topNavWrapper') ? $this : $this.parents('.topNavWrapper');
		if ($this.hasClass('topNavHref')) {
			return true;
		} else {
			if ($this.hasClass('expanded')) {
				$this.removeClass('expanded');
			} else {
				$this.addClass('expanded').siblings().removeClass('expanded');
			}
			return false;
		}
	});

	$(document).click(function () {
		$topNavWrappers.removeClass('expanded');
		$categories.removeClass('expanded');
	});
}());
