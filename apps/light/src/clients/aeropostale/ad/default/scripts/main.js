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
            windowParams = $.extend({}, App.options.urlParams);

        // Ad server will pass us a click-tracking url (usually encoded once)
        // append our redirect url to the click-tracking url
        // For more information:
        // - https://support.google.com/adxbuyer/answer/3187721?hl=en
        // - https://support.google.com/dfp_premium/answer/1242718?hl=en
        if (windowParams['click']) {
        	redirect_url = decodeURI( windowParams['click'] );
        	delete windowParams['click'];
        }

        params = $.extend({}, params, windowParams);
        paramStr = _.isEmpty(params) ? '' : '?' + $.param(params);
        
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
