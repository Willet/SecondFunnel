var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
require('jquery-deparam');

var Ad = require('ad'),
	App = Ad.App;

App.module('core', require('./views'));

(function () {
    var urlParse = function (url) {
    	// Trick to parse url is to use location object of a-tag
        var a = document.createElement('a'),
            search = '';
        a.href = url;

        if (a.search) {
            search = a.search.substr(1);  // remove '?'
        }

        return {
            'href': a.href,
            'host': a.host,
            'hostname': a.hostname,
            'pathname': a.pathname,
            'search': search,
            'hash': a.hash,
            'protocol': a.protocol + "//"
        };
    };

	App.utils.generateAdClickUrl = function (url) {
		var click_url, redirect_url, dest_url, paramStr,
			parts = urlParse(url),
            params = $.deparam(parts.search),
            windowParams = App.options.urlParams;

        // Ad server will pass us a click-tracking url
        // append our redirect url to the click-tracking url
        if (windowParams['click']) {
        	redirect_url = decodeURI( windowParams['click'] );
        	delete windowParams['click'];
        }

        params = $.extend({}, params, windowParams || {});
        paramStr = params ? '?' + $.param(params) : '';
        alert(JSON.stringify(parts));
    	dest_url = parts.protocol +  // http://
           		    parts.host +      // google.com:80
           		    parts.pathname +  // /foobar?
           		    paramStr +   // baz=kek
           		    parts.hash;  // #hello

        // Do we need to pass through a redirect?
        if (redirect_url) {
            redirect_url += encodeURIComponent(dest_url);
            click_url = redirect_url;
        } else {
            click_url = dest_url;
        }
        return click_url;
    };

    // Update top bar
    $topbar = $('#topbar a');
    $topbar.attr('href', App.utils.generateAdClickUrl( $topbar.attr('href') ) );
}());
