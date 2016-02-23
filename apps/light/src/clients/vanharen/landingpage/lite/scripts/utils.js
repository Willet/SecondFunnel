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
    module.openUrl = function (targetUrl, target) {
        var click_url, dest_url,
            windowParams = $.extend({}, $.deparam( window.location.search.substr(1) ));

        if (!_.contains(['_blank','_top','_parent','_self'], target)) {
            target = module.openInWindow();
        }

        dest_url = module.urlAddParams(targetUrl, windowParams);
        dest_url = module.addUrlTrackingParameters(dest_url);
        
        // Track destination url
        App.vent.trigger("tracking:click", dest_url);

        window.open(dest_url, target);
        return;
    };

    module.addUrlTrackingParameters = function (url) {
        var params = {
            "campaign":   "TRENDSPAGE"
        };
        return module.urlAddParams(url, _.extend({}, params, App.option("page:urlParams")));
    };
};