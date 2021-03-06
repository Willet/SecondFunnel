/*global window, document, undefined*/
/**
 * Copyright (c) 2014  SecondFunnel
 *
 * Second Funnel conversion tracking tag
 *
 */
;(function (window, document, undefined) {
    "use strict";
    var guessPrice,
        loadPage;

    if (document === undefined) {
        // the thing that ran this script was not a browser.
        return;
    }

    guessPrice = function () {
        var price,
            hybrisVars = window.s_amc_hb;

        // First attempt to find prices from hybris variables.
        if (hybrisVars) {
            price = hybrisVars.hb_orderData_totalPrice ||
                    hybrisVars.hb_cartData_totalPrice;
            if (!price && hybrisVars.contextData) {
                price = hybrisVars.contextData.hb_orderData_totalPrice ||
                        hybrisVars.contextData.hb_cartData_totalPrice;
            }
        } else if (window.dataLayer && window.dataLayer.length >= 1) {
        // Then attempt to find prices from Google Tag Manager.
            price = window.dataLayer[0].transactionTotal;
        } else if (window.google_conversion_value) {
        // Then attempt to find prices from Google AdWords.
            price = window.google_conversion_value;
        }

        try {
            return price.toString();
        } catch (e) {}
        return "0.00";
    };

    // Loads the iframe that loads a script inside the iframe to record the
    // conversion.
    loadPage = function () {
        var clickMeterConversionValue = guessPrice(),
            clickMeterConversionId = window.SECONDFUNNEL_CONVERSION_ID ||
                '{{ clickmeter_conversion_id }}',
            clickMeterConversionParameter = 'empty',
            conversionBase = 'https://clickmeter.com/conversion.aspx',
            convValue,
            iframe = document.createElement('iframe'),
            index,
            myScript,
            panel = document.createElement('div'),
            params = '',
            scripts;

        if (clickMeterConversionValue !== null) {
            convValue = parseFloat(clickMeterConversionValue.replace(',', '.'));
            if (!isNaN(convValue)) {
                params = '&val=' + convValue;
            }
        }
        params = params + '&param=' + clickMeterConversionParameter;

        panel.setAttribute('id', 'conversion_container');
        panel.style.height = '0px';
        panel.style.width = '0px';
        panel.style.overflow = 'hidden';

        if ("https:" === document.location.protocol) {
            iframe.setAttribute('src', conversionBase + '?id=' +
                clickMeterConversionId + params);
        } else {
            iframe.setAttribute('src', conversionBase + '?id=' +
                clickMeterConversionId + params);
        }

        iframe.setAttribute('frameborder', '0');
        iframe.setAttribute('height', '0');
        iframe.setAttribute('width', '0');
        iframe.setAttribute('noresize', '0');
        iframe.setAttribute('id', 'convframe');
        iframe.setAttribute('name', 'convframe');
        iframe.setAttribute('allowtransparency', 'true');

        scripts = document.getElementsByTagName('script');
        index = scripts.length - 1;
        myScript = scripts[index];
        panel.appendChild(iframe);
        myScript.parentNode.appendChild(panel);
    };

    try {
        loadPage();
    } catch (err) {
        // #fail
    }
}(window, window && window.document));
