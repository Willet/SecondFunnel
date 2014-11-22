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
		var click_url, redirect_url, paramStr,
			parts = urlParse(url),
            params = $.deparam(parts.search),
            windowParams = App.options.urlParams;

        // Ad server will pass us a click-tracking url
        // append our redirect url to the click-tracking url
        if (windowParams['click']) {
        	click_url = decodeURI( windowParams['click'] );
        	delete windowParams['click'];

	        params = $.extend({}, params, windowParams, App.options.urlParams || {});
	        paramStr = '?' + $.param(params);

			redirect_url = parts.protocol +  // http://
	               		   parts.host +      // google.com:80
	               		   parts.pathname +  // /foobar
	               		   paramStr +   // ?baz=kek
	               		   parts.hash;  // #hello
	        click_url += encodeURIComponent(redirect_url);
	    } else {
        	click_url = parts.protocol +  // http://
               		    parts.host +      // google.com:80
               		    parts.pathname +  // /foobar?
               		    paramStr +   // baz=kek
               		    parts.hash;  // #hello
        }
        return click_url;
    };
}());
