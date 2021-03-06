/*global window, document, undefined*/
/**
 * Copyright (c) 2014  SecondFunnel
 *
 * Second Funnel conversion tracking tag
 *
 */
;(function (window, document, undefined) {
    "use strict";

    // conversion id for clickmeter
    window.SECONDFUNNEL_CONVERSION_ID = '271C54CB40964B26BD0593C4E24EF1C3';

    if (document === undefined) {
        // the thing that ran this script was not a browser.
        return;
    }

    try {
        var scriptTag = document.createElement('script'),
            // load script from https domain
            scriptSrc = 'https://s3-us-west-2.amazonaws.com/static-misc-secondfunnel/js/conversion/nastygal/conversion.js',
            firstScriptTag = document.getElementsByTagName('script')[0];

        scriptTag.async = 1;

        if (window.SECONDFUNNEL_CONVERSION_ID) {
            scriptTag.src = scriptSrc + "?id=" + window.SECONDFUNNEL_CONVERSION_ID;
        } else {
            scriptTag.src = scriptSrc;
        }

        firstScriptTag.parentNode.insertBefore(scriptTag, firstScriptTag);
    } catch (err) {
        // script loading failed
    }
}(window, window && window.document));
