var pinpointTracking = (function ($, window, document) {
    var referrerName = function () {
        var host;

        if (document.referrer === "") {
            return "noref";
        }

        host = parseUri(document.referrer).host;
        // want top level domain name (i.e. tumblr.com, not site.tumblr.com)
        host = host.split(".").slice(host.split(".").length - 2, host.split(".").length).join(".");

        if (host === "") {
            return "noref";
        }

        return host;
    },

    trackEvent = function (o) {
        console.log('trackEvent: ', category, o.action, o.label, o.value || undefined);
    },

    registerShare = function (o) {
        var action, url;

        trackEvent({
            "action": "share|" + o.network + "|" + o.type + "|" + pinpointTracking.socialShareType,
            "label": pinpointTracking.socialShareUrl
        });
    },

    setSocialShareVars = function (o) {
        if (o.default === true) {
            pinpointTracking.socialShareUrl = $("#featured_img").data("url");
            pinpointTracking.socialShareType = "featured";
        } else {
            pinpointTracking.socialShareUrl = o.url;
            pinpointTracking.socialShareType = o.sType;
        }
    },

    clearTimeout = function () {
        if (typeof pinpointTracking._pptimeout == "number") {
          window.clearTimeout(pinpointTracking._pptimeout);

          // TODO remove this? not valid in strict mode
          delete pinpointTracking._pptimeout;
        }
    },

    init = function() {
        setSocialShareVars({"default": true});

        // load scripts
        window.twttr = (function (d,s,id) {
            var t, js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return; js=d.createElement(s); js.id=id;
            js.src="//platform.twitter.com/widgets.js"; js.onload="pinpointTracking.registerTwitterListeners"; fjs.parentNode.insertBefore(js, fjs);
            return window.twttr || (t = { _e: [], ready: function(f){ t._e.push(f) } });
        }(document, "script", "twitter-wjs"));

        twttr.ready(function(twttr) {
            twttr.events.bind('tweet', function(event) {
                pinpointTracking.registerShare({
                    "network": "Twitter",
                    "type": "shared"
                });
            });

            twttr.events.bind('click', function(event) {
                var sType;
                if (event.region == "tweet") {
                    sType = "clicked";
                } else if (event.region == "tweetcount") {
                    sType = "leftFor";
                } else {
                    sType = event.region;
                }
                pinpointTracking.registerShare({
                    "network": "Twitter",
                    "type": sType
                });
            });
        });
    },


    // parseUri 1.2.2
    // (c) Steven Levithan <stevenlevithan.com>
    // MIT License

    parseUri = function (str) {
        var o   = parseUri.options,
            m   = o.parser[o.strictMode ? "strict" : "loose"].exec(str),
            uri = {},
            i   = 14;

        while (i--) uri[o.key[i]] = m[i] || "";

        uri[o.q.name] = {};
        uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
            if ($1) uri[o.q.name][$1] = $2;
        });

        return uri;
    };

    parseUri.options = {
        strictMode: false,
        key: ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"],
        q:   {
            name:   "queryKey",
            parser: /(?:^|&)([^&=]*)=?([^&]*)/g
        },
        parser: {
            strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
            loose:  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
        }
    };

    this.socialShareType = undefined;
    this.socialShareUrl  = undefined;
    this._pptimeout      = undefined;

    return {
        "init": init,
        "registerShare": registerShare,
        "trackEvent": trackEvent,
        "setSocialShareVars": setSocialShareVars,
        "clearTimeout": clearTimeout
    }

}($, window, document));

pinpointTracking.init();