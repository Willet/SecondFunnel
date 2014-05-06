/*global App, $, Backbone, Marionette, console, _ */
/**
 * @module tracker
 */
App.module("tracker", function (tracker, App) {
    "use strict";

    var self = this,
        $document = $(document),
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

            window.ga.apply(window, arguments);
        },

        /**
         * Semi-private function for wrapping trackTileClick and trackTileView
         */
        trackTile = function (interactionType, tileIds) {
            if (interactionType === 'view') {
                for (var i=0; i < tileIds.length; i++) {
                    try {
                        var model = App.discovery.collection.findWhere({
                            'tile-id': tileIds[i]
                        });
                        Keen.addEvent('impression', getKeenInfo(model));
                    } catch(err) {}
                }
            }

            // if gap sends us too many visitors --> track tiles less often.
            // 0.2 is arbitrary
            if (App.option('store:slug', '').toLowerCase() === 'gap' &&
                Math.random() < 0.2) {
                return $.Deferred().promise();
            }
            return $.ajax({
                'url': App.option('IRSource') + "/page/" +
                       App.option('page:id') + "/tile/" + interactionType,
                'type': 'POST',
                'data': {
                    'tile-ids': tileIds.join(',')
                }
            });
        },

        /**
         * real argument: {int} tileId
         * waits for a second, then tracks those tile ids
         */
        trackTileClick = _.buffer(function (tileIds) {
            return trackTile('click', tileIds);
        }, 1000),

        /**
         * real argument: {int} tileId
         * waits for a second, then tracks those tile ids
         */
        trackTileView = _.buffer(function (tileIds) {
            return trackTile('view', tileIds);
        }, 1000),

        trackPageView = function (hash) {
            var base = window.location.pathname + window.location.search,
                host = window.location.protocol +'//' + window.location.hostname;
            hash = hash || window.location.hash;
            addItem('send', 'pageview', {
                'page': base + hash,
                'location': host + base + hash
            });
        },

        trackEvent = function (o) {
            // category       - type of object that was acted on
            // action         - type of action that took place (e.g. share, preview)
            // label          - Data specific to event (e.g. product, URL)
            // value          - Optional numeric data
            // nonInteraction - if true, don't count in bounce rate
            //                  by default, events are interactive

            // https://developers.google.com/analytics/devguides/collection/analyticsjs/field-reference
            var nonInteraction = o.nonInteraction || false;

            addItem('send', 'event', o.category, o.action, o.label,
                    o.value || undefined, {'nonInteraction': nonInteraction});

            /* adb: disable scroll pageviews for now while we resolve pageview issues

            if (o.action === 'scroll') {
                var hash = '#page' + o.label;
                trackPageView(hash);
            }*/
        },

        getKeenInfo = function(model) {
            var related = _.isEmpty(model.get('tagged-products')) ?
                    model : model.get('tagged-products')[0];

            var analyticsProduct = _.pick(
                related.attributes || related,
                ['name', 'description', 'price', 'url']
            );

            var analyticsTile = {
                'url': model.get('image').url,
                'id': model.get('tile-id'),
                'type': model.get('template')
            };

            var analyticsPage = _.pick(
                App.options.page,
                ['id', 'name', 'pubDate']
            );

            analyticsPage['url'] = window.location.protocol
                + '//'
                + window.location.hostname
                + window.location.pathname;

            return {
                'store': App.options.store,
                'tile': analyticsTile,
                'product': analyticsProduct,
                'page': analyticsPage
            }
        },

        setCustomVar = function (o) {
            var index = o.index,
                type = o.type,
                value = o.value;

            if (!(index && value && type)) {
                console.warn("Missing one or more of: index, type, value");
                return;
            }

            // universal analytics accept only indexed dimensions with no
            // name, or named variables with no scope
            // https://developers.google.com/analytics/devguides/collection/upgrade/reference/gajs-analyticsjs#custom-vars
            // so scope + name is used to mimic that
            addItem('set', type + index, value);
        },

        getTrackingInformation = function (model, isPreview) {
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
                label = model.get('image');
                if (label.get) {
                    label = label.get('url');
                }

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
     * Records the fact that the category has been changed.
     *
     * @param category {String}   The category switched to
     * @returns undefined
     */
    this.changeCategory = function (category) {
        trackEvent({
            'category': 'category',
            'action': 'select',
            'label': category
        });

        setCustomVar({
            'index': 1,
            'type': 'dimension',
            'value': category
        });

        App.vent.trigger('trackerChangeCategory', category, this);
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
        'click .tile': function () {
            var modelId = $(this).attr('id'),
                model = App.discovery.collection.get(modelId) ||
                        // {cXXX} models could be here instead, for some reason
                        App.discovery.collection._byId[modelId],
                trackingInfo = getTrackingInformation(model),
                tileId = model.get('tile-id') || 0,
                label = trackingInfo.label || "",
                hash;

            if (!label) {
                console.warn("Not tracking event with no label");
                return;
            }

            // for distinguishing product or (mostly content) tiles that
            // have different ids
            if (tileId) {
                label += " (Tile " + tileId + ")";

                // add click to our database
                App.vent.trigger('tracking:trackTileClick', tileId);

                // Be super explicit about what the hash is
                // rather than relying on the window
                //
                // adb: use '/' instead of '#' because it seems like google analytics will attribute
                // http://gap.secondfunnel.com/livedin#foo to http://gap.secondfunnel.com/livedin
                trackPageView('/' + tileId);
            } else {
                console.warn('No tile id present for for tile: ' + label);
            }

            trackEvent({
                'category': trackingInfo.category,
                'action': 'Preview',
                'label': label
            });

            try {
                Keen.addEvent('preview', getKeenInfo(model));
            } catch(err) {}
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
            model = App.previewArea.currentView.model;
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

    /**
     * Add an initializer to fetch Google Analytics
     * asynchronously.
     *
     */
    this.addInitializer(function () {
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
    });

    /**
     * Add an initializer to fetch Keen.io asynchronously
     * asynchronously.
     *
     */
    this.addInitializer(function() {
        var Keen = window.Keen = Keen || {
            configure: function (e) {
                this._cf = e
            }, addEvent: function (e, t, n, i) {
                this._eq = this._eq || [], this._eq.push([e, t, n, i])
            }, setGlobalProperties: function (e) {
                this._gp = e
            }, onChartsReady: function (e) {
                this._ocrq = this._ocrq || [], this._ocrq.push(e)
            }};
        (function () {
            var e = document.createElement("script");
            e.type = "text/javascript", e.async = !0, e.src = ("https:" == document.location.protocol ? "https://" : "http://") + "dc8na2hxrj29i.cloudfront.net/code/keen-2.1.0-min.js";
            var t = document.getElementsByTagName("script")[0];
            t.parentNode.insertBefore(e, t)
        })();

        // Configure the Keen object with your Project ID and (optional) access keys.
        var options = App.option('keen');

        if (!options.projectId || !options.writeKey) {
            return;
        }

        Keen.configure({
            projectId: options.projectId,
            writeKey: options.writeKey
        });
    });


    /**
     * Starts the module.
     * Sets up default tracking events.
     *
     */
    this.initialize = function () {
        addItem('create', App.option('gaAccountNumber'), 'auto');

        // Register custom dimensions in-case they weren't already
        // registered.
        _.each(App.optimizer.dimensions(),
            function (obj) {
                setCustomVar(obj);
            }
        );

        // Track a pageview, eg like https://developers.google.com/analytics/devguides/collection/analyticsjs/
        addItem('send', 'pageview');

        // TODO: If these are already set on page load, do we need to set them
        // again here? Should they be set here instead?
        setCustomVar({
            'index': 2,
            'type': 'dimension',
            'value': App.option('store:id')
        });

        setCustomVar({
            'index': 3,
            'type': 'dimension',
            'value': App.option('store:id')
        });

        setCustomVar({
            'index': 4,
            'type': 'dimension',
            'value': App.option('campaign')
        });

        setCustomVar({
            'index': 5,
            'type': 'dimension',
            'value': App.option('page:id')
        });

        // register event maps
        var defaults = new this.EventManager(this.defaultEventMap),
            customs = new this.EventManager(App.option('events'));

        App.vent.trigger('trackerInitialized', this);
        // setTrackingDomHooks() on $.ready
    };

    // add mediator triggers if the module exists.
    App.vent.on({
        'tracking:trackEvent': trackEvent,
        'tracking:trackTileView': trackTileView,
        'tracking:trackTileClick': trackTileClick,
        'tracking:trackPageView': $.noop, //trackPageView,
        'tracking:registerTwitterListeners': this.registerTwitterListeners,
        'tracking:registerFacebookListeners': this.registerFacebookListeners,
        'tracking:videoStateChange': this.videoStateChange,
        'tracking:changeCampaign': this.changeCampaign
    });
});
