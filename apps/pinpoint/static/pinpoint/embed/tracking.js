(function(){
    try {
        var accountId, storeId, pageId;

        accountId = 'UA-XXXX-Y';  // Our Google Analytics ID
        storeId = '38';           // Store 38 = Gap
        pageId = '95';            // Page 95 = Lived In

        // Load Google Analytics
        (function (o, g, r, a, m) {
            window.GoogleAnalyticsObject = 'ga';
            window.ga = window.ga || function () {
                (window.ga.q = window.ga.q || []).push(arguments);
            };
            window.ga.l = Number(new Date());
            a = document.createElement(o);
            a.async = 1;
            a.src = g;

            m = document.getElementsByTagName(o)[0];
            m.parentNode.insertBefore(a, m);
        }('script', '//www.google-analytics.com/analytics.js', 'ga'));

        // Create a tracker separate from any others on the page
        window.ga('create', accountId, 'auto', {
            'name': 'SecondFunnel'
        });

        // Set custom variables
        window.ga('SecondFunnel.set', 'dimension2', storeId);
        window.ga('SecondFunnel.set', 'dimension3', storeId);
        window.ga('SecondFunnel.set', 'dimension4', pageId);
        window.ga('SecondFunnel.set', 'dimension5', pageId);

        // Track Google Analytics Events
        window.ga(
            'SecondFunnel.send',
            'event',
            category,
            action,
            label,
            value || undefined,
            {'nonInteraction': true}
        );

        // Load Perfect Audience
        (function() {
            window._pa = window._pa || {};

            var pa = document.createElement('script');
            pa.type = 'text/javascript';
            pa.async = true;
            pa.src = ('https:' == document.location.protocol ? 'https:' : 'http:') + "//tag.perfectaudience.com/serve/52fd209b01a11d23fd000004.js";

            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(pa, s);
        })();

        // Track Perfect Audience Events
        window._pq = window._pq || [];
        _pq.push(['track', eventName]);
    } catch (error) {
        //if something goes wrong, do not affect the rest of the page.
    }
}())