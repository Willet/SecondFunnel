/*global App, Backbone, console */
'use strict';

var _ = require('underscore');
var $ = require('jquery');

module.exports = function (utils, App) {

    /**
     *   REQUIRED: every ad click should pass through this function
     **/
    this.generateAdClickUrl = function (url) {
        var click_url, redirect_url, dest_url, paramStr,
            parts = utils.urlParse(url),
            params = $.deparam(parts.search),
            windowParams = $.extend({}, $.deparam( window.location.search.substr(1) ));
        
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
};
