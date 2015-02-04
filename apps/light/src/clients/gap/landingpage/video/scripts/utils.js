"use strict";

require('jquery-deparam');

module.exports = function (module, App, Backbone, Marionette, $, _) {
    /**
     *
     * @param {string} url
     *
     * @returns {string} url
     */
    module.generateAdClickUrl = function (dest_url) {
        var redirect_url = App.option('clickUrl');
        redirect_url += encodeURIComponent(dest_url);
        return redirect_url;
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

        //click_url = module.generateAdClickUrl(dest_url);
        window.open(dest_url, "_blank");
        return;
    };
};