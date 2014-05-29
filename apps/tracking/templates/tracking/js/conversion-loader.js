/*global window, document, undefined*/
;(function (window, document, undefined) {
    "use strict";

    if (document === undefined) {
        // the thing that ran this script was not a browser.
        return;
    }

    try {
        var scriptTag = document.createElement('script'),
            scriptSrc = 'http://secondfunnel.com/tracker/conversion.js',
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
