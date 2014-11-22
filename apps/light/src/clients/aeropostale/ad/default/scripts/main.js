var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var Marionette = require('backbone.marionette');
var bootstrap = require('bootstrap.dropdown'); // for menu-bar drop down on mobile
var deparam = require('jquery-deparam');
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

	App.utils.addUrlParams = function (url) {
		var click_url, redirect_url, paramStr,
			parts = urlParse(url),
            params = deparam(parts.search),
            window_params = deparam(window.location.search.substr(1));
        
        if (window_params['click']) {
        	click_url = decodeURI( window_params['click'] );
        	delete window_params['click'];
	        
	        params = $.extend({}, params, window_params, App.options.urlParams || {});
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
