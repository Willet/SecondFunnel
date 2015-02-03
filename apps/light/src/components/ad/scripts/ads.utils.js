"use strict";

require('jquery-deparam');

module.exports = function (module, App, Backbone, Marionette, $, _) {
    /**
     * REQUIRED! Every ad click url should pass throught this function!
     *
     * Returns ad click-tracking redirect url
     *
     * Ad server will pass us a click-tracking url as url param 'click' (usually encoded once)
     * Use this url for clicks w/ our redirect url appended to the end
     *
     * For more information:
     *  - https://support.google.com/adxbuyer/answer/3187721?hl=en
     *  - https://support.google.com/dfp_premium/answer/1242718?hl=en
     *
     * @param {string} url
     *
     * @returns {string} url
     */
    module.generateAdClickUrl = function (dest_url) {
        var click_url, redirect_url,
            windowParams = $.extend({}, $.deparam( window.location.search.substr(1) ));
        
        if (windowParams['click']) {
            redirect_url = decodeURI( windowParams['click'] );
        }

        // Do we need to pass through a redirect?
        if (redirect_url) {
            redirect_url += encodeURIComponent(dest_url);
            click_url = redirect_url;
        } else {
            click_url = dest_url;
        }
        return click_url;
    };

    /**
     * ALL CLICKS TO EXTERNAL URLS SHOULD GO THROUGH THIS FUNCTION
     * 
     * Opens url in correct window w/ tracking parameters appended & Emits tracking event
     *
     * @param {string} url
     */
    module.openUrl = function (targetUrl) {
        var click_url, dest_url,
            windowParams = $.extend({}, $.deparam( window.location.search.substr(1) ));

        // The unique ad click passthrough url is irrelvant for tracking
        if (windowParams['click']) {
            delete windowParams['click'];
        }

        dest_url = module.urlAddParams(targetUrl, windowParams);
        dest_url = module.addUrlTrackingParameters(dest_url);
        
        // Track destination url
        App.vent.trigger("tracking:click", dest_url);

        click_url = module.generateAdClickUrl(dest_url);
        window.open(click_url, "_blank");
        return;
    };
};
