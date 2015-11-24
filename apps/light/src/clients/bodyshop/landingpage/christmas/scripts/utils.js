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
    module.openUrl = function (url, target) {
        if (!_.contains(['_blank','_top','_parent','_self'], target)) {
            target = module.openInWindow();
        }
        App.vent.trigger("tracking:click", url);
        url = module.addUrlTrackingParameters(url);
        window.open(url, target);
        return;
    };

    module.addUrlTrackingParameters = function (url) {
        var params = { 
            "cvosrc":       "affiliate.linkshare.PUBLISHER-ID",
            "cvo_campaign": "Holiday2015GiftGuide",
            "utm_source":   "SecondFunnel",
            "utm_medium":   "Affiliate",
            "utm_term":     "Link",
            "utm_content":  "Holiday",
            "utm_campaign": "Holiday2015GiftGuide"
        };
        return module.urlAddParams(url, _.extend({}, params, App.option["urlParams"]));
    };
};
