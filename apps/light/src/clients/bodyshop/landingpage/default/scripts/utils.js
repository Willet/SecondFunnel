'use strict';

/**
 * @module utils
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

    module.addUrlTrackingParameters = function (url) {
        var params = { 
            "utm_source":   "SecondFunnel",
            "utm_medium":   "ReferringDomains",
            "utm_campaign": "online gift guide",
            "utm_term":     "SecondFunnel",
            "utm_content":  "12HolidayPhaseI"
        };
        return module.urlAddParams(url, params);
    };
};
