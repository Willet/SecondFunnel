/*global App, $, Backbone, Marionette, console */
/**
 * @module tracker
 */
App.module("tracker", function (tracker, App) {
    "use strict";

    var $document = $(document),
        $window = $(window),
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
            // wrap ga to obey our tracking
            if (!window.ga) {
                console.warn('Analytics library is not ready. %o', arguments);
                return;
            }

            if (!App.option('enableTracking', true)) {
                console.warn('addItem was either disabled by the client ' +
                             'or prevented by the browser. %o', arguments);
                return;
            }
            if (App.option('debug', App.QUIET) > App.QUIET) {
                console.warn('Debug mode disabled tracking. %o', arguments);
                return;
            }

            window.ga.apply(window, arguments);
        },

        trackEvent = function (o) {
            // category       - type of object that was acted on
            // action         - type of action that took place (e.g. share, preview)
            // label          - Data specific to event (e.g. product, URL)
            // value          - Optional numeric data
            // nonInteraction - if true, don't count in bounce rate
            //                  by default, events are interactive
            var nonInteraction = 0;
            if (o.nonInteraction) {
                nonInteraction = 1;
            }

            if (window.ga) {
                window.ga('send', 'event', o.category, o.action, o.label,
                    o.value || undefined, {'nonInteraction': nonInteraction});
            }
        },

        setCustomVar = function (o) {
            var slotId = o.slotId,
                name = o.name,
                value = o.value,
                scope = o.scope || GA_CUSTOMVAR_SCOPE.PAGE; // 3 = page-level

            if (!(scope && name && value)) {
                return;
            }

            if (window.ga) {
                // universal analytics accept only indexed dimensions with no
                // name, or named variables with no scope
                // https://developers.google.com/analytics/devguides/collection/upgrade/reference/gajs-analyticsjs#custom-vars
                // so scope + name is used to mimic that
                window.ga('set', scope + '.' + name + slotId, value);
            }
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
            };
        };

    /**
     * Top-level event binding wrapper. all events bubble up to this level.
     *
     * The theme can declare as many event handlers as they like by creating
     * their own new EventManager({ event: handler, event: ... })s.
     *
     * @constructor
     * @type {*}
     */
    this.EventManager = Backbone.View.extend({
        'el': $window.add($document),
        'initialize': function (bindings) {
            var self = this;
            _.each(bindings, function (func, key, l) {
                var event = key.substr(0, key.indexOf(' ')),
                    selectors = key.substr(key.indexOf(' ') + 1);
                self.$el.on(event, selectors, func);
                console.debug('regEvent ' + key);
            });
        }
    });

    /**
     * Registers facebook tracking events that are fired whenever a facebook
     * action is performed, which I believe to be mostly 'click on fb button'.
     *
     * This method does nothing if facebook is not present on the page.
     *
     * @returns undefined
     */
    this.registerFacebookListeners = function () {
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

            model = App.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model, isPreview);

            trackEvent({
                'category': trackingInfo.category,
                'action': 'Facebook',
                'label': trackingInfo.label
            });
        });
    };

    /**
     * Registers twitter tracking events that are fired whenever a user
     * completes a tweet.
     *
     * This method does nothing if twitter  is not present on the page.
     *
     * @returns undefined
     */
    this.registerTwitterListeners = function () {
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

                model = App.discovery.collection.get(modelId);
                trackingInfo = getTrackingInformation(model, isPreview);

                trackEvent({
                    'category': trackingInfo.category,
                    'action': 'Twitter',
                    'label': trackingInfo.label
                });
            });
        });
    };

    /**
     * Handles youtube tracking events that are fired whenever a youtube
     * video changes play state, e.g. pause, stop.
     *
     * This method has no effect on other types of videos.
     *
     * @param videoId {String}      the youtube video id.
     * @param event {Object}        a youtube event object.
     * @returns undefined
     */
    this.videoStateChange = function (videoId, event) {
        App.vent.trigger('videoStateChange', videoId, event, this);

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

    /**
     * Records the fact that the campaign has been changed.
     *
     * @param campaignId {Number}   A campaign ID served by this page.
     * @returns undefined
     */
    this.changeCampaign = function (campaignId) {
        setCustomVar({
            'slotId': 2,
            'name': 'CampaignID',
            'value': '' + campaignId
        });

        App.vent.trigger('trackerChangeCampaign', campaignId, this);
    };

    this.on('start', function () {  // this = tracker
        return this.initialize(App.options);
    });

    /**
     * Starts the module.
     * Sets up default tracking events.
     *
     * @alias tracker.start
     */
    this.initialize = function (options) {
        // this (reformatted) code creates window.ga
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

        this.setup(options);
    };

    this.setup = function (options) {
        if (App.option('debug', App.QUIET) > App.QUIET) {
            // do not run analytics when debugging (dev, test)
            App.vent.trigger('trackerInitialized', this);
            return;
        }
        if (window.ga) {
            window.ga('create', App.option('gaAccountNumber'), 'auto');
            window.ga('send', 'pageview');
        }

        console.debug("Registered page view.");

        setCustomVar({
            'slotId': 1,
            'name': 'StoreID',
            'value': App.option('store:id')
        });

        setCustomVar({
            'slotId': 2,
            'name': 'CampaignID',
            'value': App.option('campaign')
        });

        // TODO: If these are already set on page load, do we need to set them
        // again here? Should they be set here instead?
        setCustomVar({
            'slotId': 1,
            'name': 'Store',
            'value': App.option('store:id')
        });

        setCustomVar({
            'slotId': 2,
            'name': 'Page',
            'value': App.option('page:id')
        });

        // TODO: Need a better way to determine internal v. external visitor
        // By that I mean we should be able to segment out internal visitors
        setCustomVar({
            'slotId': 3,
            'name': 'Internal Visitor', // Name?
            'value': true ? 'Yes' : 'No', // How to determine?
            'scope': GA_CUSTOMVAR_SCOPE.VISITOR
        });

        // register event maps
        var defaults = new this.EventManager(this.defaultEventMap),
            customs = new this.EventManager(App.option('events'));

        App.vent.trigger('trackerInitialized', this);
        // setTrackingDomHooks() on $.ready
    };

    // Generally, we have views handle event tracking on their own.
    // However, it can be expensive to bind events to every single view.
    // So, to avoid the performance penalty, we do most of our tracking via
    // delegated events.

    // Backbone format: { '(event) (selectors)': function(ev), ...  }
    this.defaultEventMap = {
        // Events that we care about:
        // Content Preview
        // Product Preview
        'click .tile': function() {
            var modelId = $(this).attr('id'),
                model = App.discovery.collection.get(modelId) ||
                        // {cXXX} models could be here instead, for some reason
                        App.discovery.collection._byId[modelId],
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

            model = App.discovery.collection.get(modelId);
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

            App.vent.trigger('buyClick');

            // A bit fragile, but should do
            $previewContainer = $(this).parents('.template.target > div');
            isPreview = $previewContainer.length > 0;

            if (isPreview) {
                modelId = $previewContainer.attr('id') || "";
                modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            } else {
                modelId = $(this).parents('.tile').attr('id');
            }

            model = App.discovery.collection.get(modelId);
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
                App.vent.trigger('findStoreClick', $button);
                action = 'Find in Store';
            }
            if (isInStore) {
                App.vent.trigger('inStoreClick', $button);
                action = 'Purchase';
            }

            $previewContainer = $(this).parents('.template.target > div');
            modelId = $previewContainer.attr('id') || "";
            modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            model = App.discovery.collection.get(modelId);
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

        // TODO: Any event below this is likely subject to deletion
        // reset tracking scope: hover into featured product area
        "hover .featured": function () {
            // this = window because that's what $el is
            App.vent.trigger('featuredHover');
        },

        "hover .tile": function (ev) {
            // this = window because that's what $el is
            App.vent.trigger('tileHover', ev.currentTarget);
        },

        "click .previewContainer .close": function () {
            App.vent.trigger('popupClosed');
        },

        "hover .social-buttons .button": function (e) {
            var $button = $(e.currentTarget);
            App.vent.trigger('socialButtonHover', $button);
        }
    };

    // more events can be declared by the theme without EventManager instances
    $.extend(true, this.defaultEventMap,
             App.option('eventMap', {}));

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

    // add mediator triggers if the module exists.
    App.vent.on({
        'tracking:trackEvent': trackEvent,
        'tracking:registerTwitterListeners': this.registerTwitterListeners,
        'tracking:registerFacebookListeners': this.registerFacebookListeners,
        'tracking:videoStateChange': this.videoStateChange,
        'tracking:changeCampaign': this.changeCampaign
    });
});
