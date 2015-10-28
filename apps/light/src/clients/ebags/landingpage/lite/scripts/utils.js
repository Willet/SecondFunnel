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
        // Add CJ page-id tracking parameter
        url = App.utils.urlAddParams(url, {'sid': App.option('page:slug')});
        url = App.utils.addUrlTrackingParameters(url)
        window.open(url, target);
        return;
    };

    module.addUrlTrackingParameters = function (url) {
        var params = { 
            "utm_source":   "SecondFunnel",
            "utm_medium":   "Pages",
            "utm_campaign": App.option("page:slug")
        };
        return module.urlAddParams(url, _.extend({}, params, App.option["urlParams"]));
    };
};
