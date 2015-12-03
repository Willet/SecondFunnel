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

        var destinationUrl = module.addUrlTrackingParameters(url);
        
        if (App.option("useAffiliateLinks")) {
            destinationUrl = module.buildAffiliateLink(destinationUrl);
        }
        window.open(destinationUrl, target);
        return;
    };

    module.addUrlTrackingParameters = function (url) {
        var params = {};
        return module.urlAddParams(url, _.extend({}, params, App.option("page:urlParams")));
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
                "RD_PARM1":  encodeURI(destinationUrl)
            },
            re = /^https?\:\/\/(?:www|m)\.thebodyshop-usa\.com\/search.aspx/i;
        if (destinationUrl.match(re)) {
            params['tmpid'] = "2254";
        }
        return module.urlAddParams(baseUrl, params);
    }
};
