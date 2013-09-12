SecondFunnel.module("tracker", function (tracker, SecondFunnel) {
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
        VIDEO_BASE_URL = 'http://www.youtube.com/watch?v=',
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

        addItem = function () {
            // wrap _gaq.push to obey our tracking
            if (window._gaq && SecondFunnel.option('enableTracking', true)) {
                _gaq.push.apply(_gaq, arguments);
            }
        },

        trackEvent = function (o) {
            // category       - type of object that was acted on
            // action         - type of action that took place (e.g. share, preview)
            // label          - Data specific to event (e.g. product, URL)
            // value          - Optional numeric data
            // nonInteraction - if true, don't count in bounce rate
            //                  by default, events are interactive
            addItem(['_trackEvent',
                o.category,
                o.action,
                o.label,
                o.value || undefined,
                !!o.nonInteraction || undefined
            ]);
        },

        setCustomVar = function (o) {
            var slotId = o.slotId,
                name = o.name,
                value = o.value,
                scope = o.scope || GA_CUSTOMVAR_SCOPE.PAGE; // 3 = page-level

            if (!(slotId && name && value)) {
                return;
            }

            addItem(['_setCustomVar', slotId, name, value, scope]);
        },

        getTrackingInformation = function(model, isPreview) {
            // Given a model, return information for tracking purposes
            var category,
                label;

            if (!model) {
                throw 'Lost reference to model ' +
                      '(check if correct template is used)';
            }

            // Convert model to proper category?
            switch (model.get('template')) {
                case 'product':
                case 'combobox':
                    category = 'Product';
                    label = model.get('name');
                    break;
                default:
                    category = 'Content';
                    // TODO: Need a method to get URL
                    label = model.get('image');
                    break;
            }

            if (isPreview) {
                category += ' Preview';
            }

            return {
                'category': category,
                'label': label
            }
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

    tracker.registerFacebookListeners = function () {
        if (!window.FB) {
            return;
        }

        window.FB.Event.subscribe('edge.create', function (url, elem) {
            var $button, $previewContainer, isPreview, modelId, model,
                trackingInfo;

            $button = $(elem);
            $previewContainer = $button.parents('.template.target > div');
            isPreview = $previewContainer.length > 0;

            if (isPreview) {
                modelId = $previewContainer.attr('id') || "";
                modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            } else {
                modelId = $(this).parents('.tile').attr('id');
            }

            model = SecondFunnel.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model, isPreview);

            trackEvent({
                'category': trackingInfo.category,
                'action': 'Facebook',
                'label': trackingInfo.label
            });
        });
    };

    tracker.registerTwitterListeners = function () {
        if (!window.twttr) {
            return;
        }
        window.twttr.ready(function (twttr) {
            twttr.events.bind('tweet', function (event) {
                var $button, $previewContainer, isPreview, modelId, model,
                    trackingInfo;

                $button = $(event.target);
                $previewContainer = $button.parents('.template.target > div');
                isPreview = $previewContainer.length > 0;

                if (isPreview) {
                    modelId = $previewContainer.attr('id') || "";
                    modelId = modelId.replace('preview-', ''); // Remove prefix, if present
                } else {
                    modelId = $(this).parents('.tile').attr('id');
                }

                model = SecondFunnel.discovery.collection.get(modelId);
                trackingInfo = getTrackingInformation(model, isPreview);

                trackEvent({
                    'category': trackingInfo.category,
                    'action': 'Twitter',
                    'label': trackingInfo.label
                });
            });

            // Do we care about click vs tweet?
//            twttr.events.bind('click', function (event) {
//                var sType;
//                if (event.region === "tweet") {
//                    sType = "clicked";
//                } else if (event.region === "tweetcount") {
//                    sType = "leftFor";
//                } else {
//                    sType = event.region;
//                }
//            });
        });
    };

    tracker.videoStateChange = function (videoId, event) {
        broadcast('videoStateChange', videoId, event, tracker);

        // TODO: Do we only want to measure one event per video?
        if (videosPlayed.indexOf(videoId) !== -1) {
            // not that video
            return;
        }

        if (event.data === window.YT.PlayerState.PLAYING) {
            videosPlayed.push(videoId);

            trackEvent({
                'category': 'Content',
                'action': 'Video Play',
                'label': VIDEO_BASE_URL + videoId //Youtube URL
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

    tracker.on('start', function () {  // this = tracker
        if (SecondFunnel.option('debug', SecondFunnel.NONE) > SecondFunnel.NONE) {
            // debug mode.
            addItem(['_setDomainName', 'none']);
        }

        addItem(['_setAccount', SecondFunnel.option('gaAccountNumber')]);
        addItem(['_setCustomVar',
            1,                               // slot id
            'StoreID',                       // name
            SecondFunnel.option('store:id'), // value
            3                                // scope: page-level
        ]);
        addItem(['_setCustomVar', 2, 'CampaignID',
            SecondFunnel.option('campaign'),  // <int>
            3
        ]);
        addItem(['_trackPageview']);

        tracker.setSocialShareVars();

        // TODO: If these are already set on page load, do we need to set them
        // again here? Should they be set here instead?
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

        // TODO: Need a better way to determine internal v. external visitor
        // By that I mean we should be able to segment out internal visitors
        setCustomVar({
            'slotId': 3,
            'name': 'Internal Visitor', // Name?
            'value': true ? 'Yes' : 'No', // How to determine?
            'scope': GA_CUSTOMVAR_SCOPE.VISITOR
        });

        // referrer? domain?

        broadcast('trackerInitialized', tracker);
        // setTrackingDomHooks() on $.ready
    });

    // Generally, we have views handle event tracking on their own.
    // However, it can be expensive to bind events to every single view.
    // So, to avoid the performance penalty, we do most of our tracking via
    // delegated events.

    // TODO: Of the events that we broadcast, which are actually used?

    // Backbone format: { '(event) (selectors)': function(ev), ...  }
    tracker.defaultEventMap = {
        // Events that we care about:
        // Content Preview
        // Product Preview
        'click .tile': function() {
            var modelId = $(this).attr('id'),
                model = SecondFunnel.discovery.collection.get(modelId) ||
                        // {cXXX} models could be here instead, for some reason
                        SecondFunnel.discovery.collection._byId[modelId],
                trackingInfo = getTrackingInformation(model);

            trackEvent({
                'category': trackingInfo.category,
                'action': 'Preview',
                'label': trackingInfo.label
            });
        },

        // Content Share
        // Product Share
        //
        // Note:    FB and Twitter tracking are handled separately because we
        //          can't actually capture those events)
        "click .social-buttons .button": function (e) {
            var modelId, model, trackingInfo, network, classes, $previewContainer;

            // A bit fragile, but should do
            $previewContainer = $(this).parents('.template.target > div');
            if ($previewContainer) {
                modelId = $previewContainer.attr('id') || "";
                modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            } else {
                modelId = $(this).parents('.tile').attr('id');
            }

            model = SecondFunnel.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model);

            classes = $(this).getClasses();
            network = _.first(_.without(classes, 'button'));

            trackEvent({
                'category': trackingInfo.category,
                'action': network,
                'label': trackingInfo.label
            });
        },

        // Content Play (Video)
        // Note:    Handled by `videoStateChange`

        // Purchase Actions (Buy / Find in Store)
        // buy now event
        "click a.buy": function () {
            var modelId, model, trackingInfo, $previewContainer, isPreview;

            broadcast('buyClick');

            // A bit fragile, but should do
            $previewContainer = $(this).parents('.template.target > div');
            isPreview = $previewContainer.length > 0;

            if (isPreview) {
                modelId = $previewContainer.attr('id') || "";
                modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            } else {
                modelId = $(this).parents('.tile').attr('id');
            }

            model = SecondFunnel.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model, isPreview);

            trackEvent({
                'category': trackingInfo.category,
                'action': 'Purchase',
                'label': trackingInfo.label
            });
        },

        // TODO: Fragile selector
        "click .find-store, .in-store": function (e) {
            var modelId, model, trackingInfo, $previewContainer, action,
                $button = $(e.currentTarget),
                isFindStore = $button.hasClass('find-store'),
                isInStore = $button.hasClass('in-store');

            // Honestly, what's the difference between these two?
            // Is one a purchase? Is one a clickthrough?
            //      'Find in Store'
            //      'Shop on GAP.com'
            if (isFindStore) {
                broadcast('findStoreClick', $button);
                action = 'Find in Store';
            }
            if (isInStore) {
                broadcast('inStoreClick', $button);
                action = 'Purchase';
            }

            $previewContainer = $(this).parents('.template.target > div');
            modelId = $previewContainer.attr('id') || "";
            modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            model = SecondFunnel.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model, true);

            trackEvent({
                'category': trackingInfo.category,
                'action': action,
                'label': trackingInfo.label
            });
        },


        // Content Impressions
        // Product Impressions

        // Exit
        "click header a": function (ev) {
            var link = $(this).attr('href');
            trackEvent({
                'category': 'Header',
                'action': 'Clickthrough', // Exit?
                'label': link
            });
        },

        "click .hero-area a": function (ev) {
            var link = $(this).attr('href');
            trackEvent({
                'category': 'Hero Area',
                'action': 'Clickthrough', // Exit?
                'label': link
            });
        },

        // Extension Points

        // TODO: Any event below this is likely subject to be deleted
        // reset tracking scope: hover into featured product area
        "hover .featured": function () {
            // this = window because that's what $el is
            broadcast('featuredHover');
            tracker.setSocialShareVars();
        },

        "hover .tile": function (ev) {
            // this = window because that's what $el is
            broadcast('tileHover', ev.currentTarget);
        },

        "click .previewContainer .close": function () {
            broadcast('popupClosed');
        },

        "hover .social-buttons .button": function (e) {
            var $button = $(e.currentTarget);
            broadcast('socialButtonHover', $button);
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
        'tracking:trackEvent': trackEvent,
        'tracking:setSocialShareVars': tracker.setSocialShareVars,
        'tracking:registerTwitterListeners': tracker.registerTwitterListeners,
        'tracking:registerFacebookListeners': tracker.registerFacebookListeners,
        'tracking:videoStateChange': tracker.videoStateChange,
        'tracking:changeCampaign': tracker.changeCampaign
    });
});