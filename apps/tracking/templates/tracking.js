{% if request.COOKIES.visited == 'true' %}
(function(){
    try {
        // Load Perfect Audience
        (function() {
            window._pa = window._pa || {};

            // TODO: Make PA script configurable
            // i.e. can't always use 52fd209b01a11d23fd000004.js;
            // will probably vary per client
            var pa = document.createElement('script');
            pa.type = 'text/javascript';
            pa.async = true;
            pa.src = ('https:' == document.location.protocol ? 'https:' : 'http:') + "//tag.perfectaudience.com/serve/52fd209b01a11d23fd000004.js";

            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(pa, s);
        })();

        // Track Perfect Audience Events
        window._pq = window._pq || [];
        _pq.push(['track', 'Purchase']);
    } catch (error) {
        //if something goes wrong, do not affect the rest of the page.
    }
}());
{% endif %}