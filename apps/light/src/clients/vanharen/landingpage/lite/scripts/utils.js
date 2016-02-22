"use strict";

require('jquery-deparam');

module.exports = function (module, App, Backbone, Marionette, $, _) {
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

        window.open(dest_url, "_blank");
        return;
    };

    module.addUrlTrackingParameters = function (url) {
        var params = {
            "campaign":   "TRENDSPAGE"
        };
        return module.urlAddParams(url, _.extend({}, params, App.option("page:urlParams")));
    };
};