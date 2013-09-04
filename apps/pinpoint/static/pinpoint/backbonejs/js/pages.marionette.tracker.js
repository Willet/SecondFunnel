SecondFunnel.module("tracker", function (tracker) {
    "use strict";

    var $document = $(document),
        $window = $(window),
        isBounce = true,  // this flag set to false once user scrolls down
        videosPlayed = [],
        GA_CUSTOMVAR_SCOPE = {
            'PAGE': 3,
            'EVENT': 3,
            'SESSION': 2,
            'VISITOR': 1
        },
        parseUri = function (str) {
            // parseUri 1.2.2
            // (c) Steven Levithan <stevenlevithan.com>
            // MIT License
            var o = parseUri.options,
                m = o.parser[o.strictMode ? "strict"
                    : "loose"].exec(str),
                uri = {},
                i = 14;

            while (i--) {
                uri[o.key[i]] = m[i] || "";
            }

            uri[o.q.name] = {};
            uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
                if ($1) {
                    uri[o.q.name][$1] = $2;
                }
            });

            return uri;
        },

        referrerName = function () {
            var host;

            if (document.referrer === "") {
                return "noref";
            }

            host = parseUri(document.referrer).host;
            // want top level domain name (i.e. tumblr.com, not site.tumblr.com)
            host = host.split(".").slice(host.split(".").length - 2,
                host.split(".").length).join(".");

            if (host === "") {
                return "noref";
            }

            return host;
        },

        trackEvent = function (o) {
            // category       - type of object that was acted on
            // action         - type of action that took place (e.g. share, preview)
            // label          - Data specific to event (e.g. product, URL)
            // value          - Optional numeric data
            // nonInteraction - if true, don't count in bounce rate
            //                  by default, events are interactive

            if (SecondFunnel.option('enableTracking', true)) {
                if (window._gaq) {
                    window._gaq.push(['_trackEvent',
                        o.category,
                        o.action,
                        o.label,
                        o.value || undefined,
                        !!o.nonInteraction || undefined
                    ]);
                }
                broadcast('eventTracked', o, o.category);
            }
        },

        setCustomVar = function (o) {
            var slotId = o.slotId,
                name = o.name,
                value = o.value,
                scope = o.scope || GA_CUSTOMVAR_SCOPE.PAGE; // 3 = page-level

            if (!(slotId && name && value)) {
                return;
            }

            if (window._gaq && SecondFunnel.option('enableTracking', true)) {
                window._gaq.push(['_setCustomVar', slotId, name, value, scope]);
            }
        };

    tracker.registerEvent = function (o) {
        var actionData = [
            "network=" + o.network || "",
            "actionType=" + o.type,
            "actionSubtype=" + o.subtype || "",
            "actionScope=" + tracker.socialShareType
        ];

        // We can mark non-bounces in a more correct way
//        tracker.notABounce(o.type);

        trackEvent({
            "action": actionData.join("|"),
            "label": o.label || tracker.socialShareUrl
        });
    };

    tracker.setSocialShareVars = function (o) {
        if (o && o.url && o.sType) {
            tracker.socialShareUrl = o.url;
            tracker.socialShareType = o.sType;
        } else {
            tracker.socialShareUrl = $("#featured_img").data("url");
            tracker.socialShareType = "featured";
        }
    };

    // TODO: Unused: Remove?
//    tracker.registerTwitterListeners = function () {
//        if (!window.twttr) {
//            return;
//        }
//        window.twttr.ready(function (twttr) {
//            twttr.events.bind('tweet', function (event) {
//                tracker.registerEvent({
//                    "network": "Twitter",
//                    "type": "share",
//                    "subtype": "shared"
//                });
//
//                tracker.trackEvent({
//                    'category': '',
//                    'action': 'Twitter',
//                    'label': ''
//                })
//            });
//
//            twttr.events.bind('click', function (event) {
//                var sType;
//                if (event.region === "tweet") {
//                    sType = "clicked";
//                } else if (event.region === "tweetcount") {
//                    sType = "leftFor";
//                } else {
//                    sType = event.region;
//                }
//                tracker.registerEvent({
//                    "network": "Twitter",
//                    "type": "share",
//                    "subtype": sType
//                });
//            });
//        });
//    };

    // TODO: Remove: Pointless?
//    tracker.notABounce = _.once(function (how) {
//        // visitor already marked as "non-bounce"
//        // this function becomes nothing after it's first run, even
//        // after re-initialisation, or if the function throws an exception.
//        broadcast('notABounce', how, tracker);
//
//        tracker.registerEvent({
//            "type": "visit",
//            "subtype": "noBounce",
//            "label": how
//        });
//    });

    tracker.videoStateChange = function (videoId, event) {
        broadcast('videoStateChange', videoId, event, tracker);

        if (videosPlayed.indexOf(videoId) !== -1) {
            // not that video
            return;
        }

        if (event.data === window.YT.PlayerState.PLAYING) {
            videosPlayed.push(videoId);

//            tracker.registerEvent({
//                "type": "content",
//                "subtype": "video",
//                "label": videoId
//            });

            tracker.trackEvent({
                'category': 'Content',
                'action': 'Video Play',
                'label': '' //Youtube URL
            });
        }
    };

    tracker.changeCampaign = function (campaignId) {
        setCustomVar({
            'slotId': 2,
            'name': 'CampaignID',
            'value': '' + campaignId
        });

        broadcast('trackerChangeCampaign', campaignId, tracker);
    };

    tracker.init = function () {
        // this = SecondFunnel.vent
        // arguments = args[1~n] when calling .trigger()
        tracker.setSocialShareVars();

        setCustomVar({
            'slotId': 1,
            'name': 'Store',
            'value': SecondFunnel.option('store:id'),
            'scope': GA_CUSTOMVAR_SCOPE.PAGE
        });

        setCustomVar({
            'slotId': 2,
            'name': 'Page',
            'value': SecondFunnel.option('page:id'),
            'scope': GA_CUSTOMVAR_SCOPE.PAGE
        });

        setCustomVar({
            'slotId': 3,
            'name': 'Internal Visitor', // Name?
            'value': true ? 'Yes' : 'No', // How to determine?
            'scope': GA_CUSTOMVAR_SCOPE.VISITOR
        });

        // referrer? domain?

        broadcast('trackerInitialized', tracker);
        // setTrackingDomHooks() on $.ready
    };

    // Generally, we have views handle event tracking on their own.
    // However, it can be expensive to bind events to every single view.
    // So, to avoid the performance penalty, we do most of our tracking via
    // delegated events.

    // TODO: Of the events that we broadcast, which are actually used?

    // Backbone format: { '(event) (selectors)': function(ev), ...  }
    tracker.defaultEventMap = {
        // reset tracking scope: hover into featured product area
        "hover .featured": function () {
            // this = window because that's what $el is
            broadcast('featuredHover');
            tracker.setSocialShareVars();
        },

        "hover .tile": function (ev) {
            // this = window because that's what $el is
            broadcast('tileHover', ev.currentTarget);
            // No need to track tile hover
        },

        "click .header a": function (ev) {
            broadcast('headerHover', ev.currentTarget);
//            tracker.registerEvent({
//                "type": "clickthrough",
//                "subtype": "header",
//                "label": $(this).attr("href")
//            });

            tracker.trackEvent({
                'category': 'Header',
                'action': 'Clickthrough'
//                'label': '' // Do we need a label? Info should be included in segment
            });
        },

        "click .previewContainer .close": function () {
            broadcast('popupClosed');
            // No need to track preview closed
        },

        // buy now event
        "click a.buy": function () {
            broadcast('buyClick');
//            tracker.registerEvent({
//                "type": "clickthrough",
//                "subtype": "buy",
//                "label": $(this).attr("href")
//            });

            tracker.trackEvent({
                'category': '', // What tile type?
                'action': 'Purchase',
                'label': '' // Product name
            });
        },

        // popup open event: product click
        "click .tile.product, .tile.combobox .product": function (e) {
            // TODO: data('label') === ?
            broadcast('tileClick');
//            tracker.registerEvent({
//                "type": "inpage",
//                "subtype": "openpopup",
//                "label": $(this).data("label")
//            });

            tracker.trackEvent({
                'category': 'Product',
                'action': 'Preview',
                'label': '' // Product name
            });
        },

        // lifestyle image click
        "click .tile.combobox .lifestyle, .tile.image, .tile>img": function (e) {
            broadcast('lifestyleTileClick');
//            tracker.registerEvent({
//                "type": "content",
//                "subtype": "openpopup",
//                "label": $(this).data("label")
//            });

            tracker.trackEvent({
                'category': '', // Tile type?
                'action': 'Purchase',
                'label': '' // Product / URL
            });
        },

        "hover .social-buttons .button": function (e) {
            var $button = $(e.currentTarget);
            broadcast('socialButtonHover', $button);
            // No need to track social buttons hover
        },

        "click .social-buttons .button": function (e) {
            // insert code here
            tracker.trackEvent({
                'category': '', // What tile type?
                'action': 'Purchase',
                'label': '' // Product name
            });
        },

        // core metrics: 'Shop Now', 'Find in Store' or similar
        "click .find-store, .in-store": function (e) {
            var $button = $(e.currentTarget),
                isFindStore = $button.hasClass('find-store'),
                isInStore = $button.hasClass('in-store');
            if (isFindStore) {
                broadcast('findStoreClick', $button);
//                tracker.registerEvent({
//                    "type": "inpage",
//                    "subtype": "clickFindStore",
//                    "label": "???"  // TODO: decide on a label
//                });
                tracker.trackEvent({
                    'category': '', // What tile type?
                    'action': 'Purchase',
                    'label': '' // Product name
                });
            }
            if (isInStore) {
                broadcast('inStoreClick', $button);
//                tracker.registerEvent({
//                    "type": "inpage",
//                    "subtype": "clickInStore",
//                    "label": "???"  // TODO: decide on a label
//                });
                tracker.trackEvent({
                    'category': '', // What tile type? Preview?
                    'action': 'Clickthrough',
                    'label': '' // Product name
                });
            }
        }
    };

    // more events can be declared by the theme without EventManager instances
    $.extend(true, tracker.defaultEventMap,
             SecondFunnel.option('eventMap', {}));

    parseUri.options = {
        'strictMode': false,
        'key': [
            "source", "protocol", "authority", "userInfo", "user", "password",
            "host", "port", "relative", "path", "directory", "file", "query", "anchor"],
        'q': {
            'name': "queryKey",
            'parser': /(?:^|&)([^&=]*)=?([^&]*)/g
        },
        'parser': {
            'strict': /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
            'loose': /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
        }
    };

    this.socialShareType = undefined;
    this.socialShareUrl = undefined;

    // add mediator triggers if the module exists.
    SecondFunnel.vent.on({
        'tracking:init': tracker.init,
        'tracking:registerEvent': tracker.registerEvent,
        'tracking:trackEvent': tracker.trackEvent,
        'tracking:setSocialShareVars': tracker.setSocialShareVars,
        'tracking:registerTwitterListeners': tracker.registerTwitterListeners,
//        'tracking:notABounce': tracker.notABounce,
        'tracking:videoStateChange': tracker.videoStateChange,
        'tracking:changeCampaign': tracker.changeCampaign
    });

    // the app initializer init()s it
});