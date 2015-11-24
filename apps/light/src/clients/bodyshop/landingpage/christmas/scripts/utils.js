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
        var destinationUrl = module.addUrlTrackingParameters(url),
            affiliateUrl = module.buildAffiliateLink(destinationUrl);
        window.open(affiliateUrl, target);
        return;
    };

    module.addUrlTrackingParameters = function (url) {
        var params = {};
        return module.urlAddParams(url, _.extend({}, params, App.option["urlParams"]));
    };

    module.buildAffiliateLink = function (destinationUrl) {
        var baseUrl = "http://click.linksynergy.com/fs-bin/click",
            params = {
            "id":        "ijwfSa0syf8",
            "subid":     "0",
            "offerid":   "395685.1",
            "type":      "10",
            "tmpid":     "7629",
            "u1":        App.option("page:slug"),
            "RD_PARM1":  encodeURIComponent(destinationUrl)
        };
        return module.urlAddParams(baseUrl, params);
    }
};
