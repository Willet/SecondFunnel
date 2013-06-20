var pagesTracking = (function ($, window, document) {
    var mediator,
        isBounce = true, videosPlayed = [],

        referrerName = function () {
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
                + "storeid=" + window.PAGES_INFO.store.id + "|"
                + "campaignid=" + window.PAGES_INFO.page.id + "|"
                + "referrer=" + referrerName() + "|"
                + "domain=" + parseUri(window.location.href).host;

            _gaq.push(['_trackEvent', category, o.action, o.label, o.value || undefined]);
        },

        registerEvent = function (o) {
            var actionData = [
                "network=" + o.network || "",
                "actionType=" + o.type,
                "actionSubtype=" + o.subtype || "",
                "actionScope=" + pagesTracking.socialShareType,
            ];

            notABounce(o.type);

            trackEvent({
                "action": actionData.join("|"),
                "label": o.label || pagesTracking.socialShareUrl
            });
        },


        setCustomVar = function(o) {
            var conf = o || {},
                slotId = o.slotId,
                name = o.name,
                value = o.value,
                scope = o.scope || 3; // 3 = page-level

            if (!(slotId && name && value)) {
                return;
            }

            _gaq.push(['_setCustomVar', slotId, name, value, scope]);
        },

        setSocialShareVars = function (o) {
            if (o && o.url && o.sType) {
                pagesTracking.socialShareUrl = o.url;
                pagesTracking.socialShareType = o.sType;
            } else {
                pagesTracking.socialShareUrl = $("#featured_img").data("url");
                pagesTracking.socialShareType = "featured";
            }
        },

        clearTimeout = function () {
            if (typeof pagesTracking._pptimeout == "number") {
                window.clearTimeout(pagesTracking._pptimeout);

                // TODO remove this? not valid in strict mode
                delete pagesTracking._pptimeout;
            }
        },

        setTrackingDomHooks = function () {
            // reset tracking scope: hover into featured product area
            $(".featured").hover(function() {
                pagesTracking.clearTimeout();
                pagesTracking.setSocialShareVars();
            }, function() {});

            $(".header a").click(function() {
                pagesTracking.registerEvent({
                    "type": "clickthrough",
                    "subtype": "header",
                    "label": $(this).attr("href")
                });
            });

            // buy now event
            $(document).on("click", "a.buy", function(e) {
                pagesTracking.registerEvent({
                    "type": "clickthrough",
                    "subtype": "buy",
                    "label": $(this).attr("href")
                });
            });

            // popup open event: product click
            $(document).on("click", ".discovery-area > .block.product, .discovery-area > .block.combobox .product", function(e) {
                pagesTracking.registerEvent({
                    "type": "inpage",
                    "subtype": "openpopup",
                    "label": $(this).data("label")
                });
            });

            // lifestyle image click
            $(document).on("click", ".discovery-area > .block.combobox .lifestyle, .discovery-area > .block.image", function(e) {
                pagesTracking.registerEvent({
                    "type": "content",
                    "subtype": "openpopup",
                    "label": $(this).data("label")
                });
            });

            // featured pinterest click event
            // pinterest doesn't have an API for us to use
            $(".pinterest").click(function() {
                pagesTracking.registerEvent({
                    "network": "Pinterest",
                    "type": "share",
                    "subtype": "clicked"
                });
            });

            // social hover and popup pinterest click events
            $(document).on("click", ".pinterest", function(e) {
                pagesTracking.registerEvent({
                    "network": "Pinterest",
                    "type": "share",
                    "subtype": "clicked"
                });
            });
        },

        registerTwitterListeners = function() {
            twttr.ready(function (twttr) {
                twttr.events.bind('tweet', function(event) {
                    pagesTracking.registerEvent({
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
                    pagesTracking.registerEvent({
                        "network": "Twitter",
                        "type": "share",
                        "subtype": sType
                    });
                });
            });
        },

        notABounce = function (how) {
            // visitor already marked as "non-bounce"
            if (!isBounce) {
                return;
            }

            isBounce = false;

            registerEvent({
                "type": "visit",
                "subtype": "noBounce",
                "label": how
            });
        },

        videoStateChange = function (video_id, event) {
            if (videosPlayed.indexOf(video_id) !== -1) {
                return;
            }

            if (event.data == YT.PlayerState.PLAYING) {
                videosPlayed.push(video_id);

                pagesTracking.registerEvent({
                    "type": "content",
                    "subtype": "video",
                    "label": video_id
                });
            }
        },

        changeCampaign = function(campaignId) {
            setCustomVar({
                'slotId': 2,
                'name': 'CampaignID',
                'value': '' + campaignId
            });
        },

        init = function () {
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

    // add mediator triggers if the module exists.
    if (window.Willet && window.Willet.mediator) {
        mediator = window.Willet.mediator;
        mediator.on('tracking.init', init);
        mediator.on('tracking.registerEvent', registerEvent);
        mediator.on('tracking.setSocialShareVars', setSocialShareVars);
        mediator.on('tracking.clearTimeout', clearTimeout);
        mediator.on('tracking.registerTwitterListeners', registerTwitterListeners);
        mediator.on('tracking.notABounce', notABounce);
        mediator.on('tracking.videoStateChange', videoStateChange);
        mediator.on('tracking.changeCampaign', changeCampaign);
    } else {
        mediator.fire('error', ['Could not add tracking.js hooks to mediator']);
    }

    return {
        "init": init,
        "registerEvent": registerEvent,
        "setSocialShareVars": setSocialShareVars,
        "clearTimeout": clearTimeout,
        "registerTwitterListeners": registerTwitterListeners,
        "notABounce": notABounce,
        "videoStateChange": videoStateChange,
        "changeCampaign": changeCampaign
    }

}($, window, document));

pagesTracking.init();
