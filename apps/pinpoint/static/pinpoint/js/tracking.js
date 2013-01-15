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
        var category = "appname=pinpoint|"
            + "storeid=" + window.PINPOINT_INFO.store.id + "|"
            + "campaignid=" + window.PINPOINT_INFO.campaign.id + "|"
            + "referrer=" + referrerName() + "|"
            + "domain=" + parseUri(window.location.href).host;

        // console.log(['_trackEvent', category, o.action, o.label, o.value || undefined]);
        _gaq.push(['_trackEvent', category, o.action, o.label, o.value || undefined]);
    },

    registerEvent = function (o) {
        var actionData = [
            "network=" + o.network || "",
            "actionType=" + o.type,
            "actionSubtype=" + o.subtype || "",
            "actionScope=" + pinpointTracking.socialShareType,
        ];

        trackEvent({
            "action": actionData.join("|"),
            "label": o.label || pinpointTracking.socialShareUrl
        });
    },

    setSocialShareVars = function (o) {
        if (o && o.url && o.sType) {
            pinpointTracking.socialShareUrl = o.url;
            pinpointTracking.socialShareType = o.sType;
        } else {
            pinpointTracking.socialShareUrl = $("#featured_img").data("url");
            pinpointTracking.socialShareType = "featured";
        }
    },

    clearTimeout = function () {
        if (typeof pinpointTracking._pptimeout == "number") {
            window.clearTimeout(pinpointTracking._pptimeout);

            // TODO remove this? not valid in strict mode
            delete pinpointTracking._pptimeout;
        }
    },

    setTrackingDomHooks = function () {
        // reset tracking scope: hover into featured product area
        $(".featured").hover(function() {
            pinpointTracking.clearTimeout();
            pinpointTracking.setSocialShareVars();
        }, function() {});

        // buy now event
        $(document).on("click", "a.buy", function(e) {
            pinpointTracking.registerEvent({
                "type": "clickthrough",
                "subtype": "buy",
                "label": $(this).attr("href")
            });
        });

        // popup open event
        $(document).on("click", ".discovery-area > .product", function(e) {
            pinpointTracking.registerEvent({
                "type": "inpage",
                "subtype": "openpopup",
                "label": $(this).data("url")
            });
        });

        // featured pinterest click event
        // pinterest doesn't have an API for us to use
        $(".pinterest").click(function() {
            pinpointTracking.registerEvent({
                "network": "Pinterest",
                "type": "share",
                "subtype": "clicked"
            });
        });

        // social hover and popup pinterest click events
        $(document).on("click", ".pinterest", function(e) {
            pinpointTracking.registerEvent({
                "network": "Pinterest",
                "type": "share",
                "subtype": "clicked"
            });
        });
    },

    registerTwitterListeners = function() {
        twttr.ready(function (twttr) {
            twttr.events.bind('tweet', function(event) {
                pinpointTracking.registerEvent({
                    "network": "Twitter",
                    "type": "share",
                    "subtype": "shared"
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
                pinpointTracking.registerEvent({
                    "network": "Twitter",
                    "type": "share",
                    "subtype": sType
                });
            });
        });
    },

    init = function() {
        setSocialShareVars();

        $(function() {
            setTrackingDomHooks();
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
    this.socialShareUrl = undefined;
    this._pptimeout = undefined;

    return {
        "init": init,
        "registerEvent": registerEvent,
        "setSocialShareVars": setSocialShareVars,
        "clearTimeout": clearTimeout,
        "registerTwitterListeners": registerTwitterListeners
    }

}($, window, document));

pinpointTracking.init();
