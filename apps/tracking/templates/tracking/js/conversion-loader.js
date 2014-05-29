/*global window, document, undefined*/
;(function (window, document, undefined) {
    "use strict";

    // conversion id for nastygal
    window.WILLET_CONVERSION_ID = '271C54CB40964B26BD0593C4E24EF1C3';

    if (document === undefined) {
        // the thing that ran this script was not a browser.
        return;
    }

    try {
        var scriptTag = document.createElement('script'),
            // load script from https domain
            scriptSrc = 'https://s3-us-west-2.amazonaws.com/static-misc-secondfunnel/js/conversion/nastygal.js',
            firstScriptTag = document.getElementsByTagName('script')[0];

        scriptTag.async = 1;

        if (window.WILLET_CONVERSION_ID) {
            scriptTag.src = scriptSrc + "?id=" + window.WILLET_CONVERSION_ID;
        } else {
            scriptTag.src = scriptSrc;
        }

        firstScriptTag.parentNode.insertBefore(scriptTag, firstScriptTag);
    } catch (err) {
        // script loading failed
    }
}(window, window && window.document));
