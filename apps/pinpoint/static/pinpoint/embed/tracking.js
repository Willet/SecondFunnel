(function(){
    try {
        var createCookie, readCookie, eraseCookie;

        // Cookie code from: http://www.quirksmode.org/js/cookies.html
        createCookie = function (name,value,days) {
            if (days) {
                var date = new Date();
                date.setTime(date.getTime()+(days*24*60*60*1000));
                var expires = "; expires="+date.toGMTString();
            }
            else var expires = "";
            document.cookie = name+"="+value+expires+"; path=/";
        }

        readCookie = function readCookie (name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        eraseCookie = function (name) {
            createCookie(name, "", -1);
        }
        // End cookie code

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
        _pq.push(['track', 'Purchase']);
    } catch (error) {
        //if something goes wrong, do not affect the rest of the page.
    }
}())