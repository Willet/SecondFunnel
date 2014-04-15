{% load raven %}
// Sentry config; log on to getsentry.com for more details
try {
    if (typeof Raven !== 'undefined') {
        // "log all": http://stackoverflow.com/a/21551597/1558430
        window.onerror = Raven.process;

        Raven.config('{% sentry_public_dsn %}', {
            // can be regexes or strings
            //raven-js.readthedocs.org/en/latest/config/index.html?highlight=whitelisturls
            'whitelistUrls': [
                // any of our domains, including "secondfunnel.com"
                /secondfunnel\.com/,
                // any of our buckets
                /elasticbeanstalk-us-(east|west)-\d-056265713214/
            ]
        }).install();

        {% if session_id %}
            {# track errors across user if possible #}
            Raven.setUser({
                'sessionId': '{{ session_id }}'
            });
        {% endif %}
    }
} catch (err) {

}
