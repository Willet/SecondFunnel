'use strict';

/**
 * @module tracker
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

    var eventMap, eventManager,
        $document = $(document),
        $window = $(window),
        pagesScrolled = 0,
        videosPlayed = [],
        GA_CUSTOMVAR_SCOPE = {
            'PAGE': 3,
            'EVENT': 3,
            'SESSION': 2,
            'VISITOR': 1
        },
        VIDEO_BASE_URL = 'http://www.youtube.com/watch?v=',

        addItem = function () {
            // wrap ga to obey our tracking
            if (!window.ga) {
                if (console.warn) {
                    console.warn('Analytics library is not ready. %o', arguments);
                }
                return;
            }

            if (!App.option('enableTracking', true)) {
                console.warn('addItem was either disabled by the client ' +
                             'or prevented by the browser. %o', arguments);
                return;
            }
            window.ga.apply(window, arguments);
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

            analyticsPage.url = window.location.protocol +
                '//' +
                window.location.hostname +
                window.location.pathname;

            return {
                'store': App.options.store,
                'tile': analyticsTile,
                'product': analyticsProduct,
                'page': analyticsPage
            };
        },

        setCustomVar = function (o) {
            var index = o.index,
                type = o.type,
                value = o.value;

            if (!(index && value && type)) {
                console.warn('Missing one or more of: index, type, value');
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
            var category, label, name, sku;

            if (!model) {
                throw 'Lost reference to model (check if correct template is used)';
            }

            switch (model.get('template')) {
                case 'product':
                    category = 'Product';
                    sku = model.get('sku');
                    label = sku ? sku+' '+model.get('name') : model.get('name');
                    break;
                default:
                    category = 'Content';
                    label = model.get('id')
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

    module.trackEvent = function (o) {
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
    module.EventManager = Backbone.View.extend({
        'el': $window.add($document),
        'initialize': function (bindings) {
            var _this = this;
            _.each(bindings, function (func, key, l) {
                var event = key.substr(0, key.indexOf(' ')),
                    selectors = key.substr(key.indexOf(' ') + 1);
                _this.$el.on(event, selectors, func);
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
    module.registerFacebookListeners = function () {
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
                modelId = $previewContainer.attr('id') || '';
                modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            } else {
                modelId = $(this).parents('.tile').attr('id');
            }

            model = App.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model, isPreview);

            module.trackEvent({
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
    module.registerTwitterListeners = function () {
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
                    modelId = $previewContainer.attr('id') || '';
                    modelId = modelId.replace('preview-', ''); // Remove prefix, if present
                } else {
                    modelId = $(this).parents('.tile').attr('id');
                }

                model = App.discovery.collection.get(modelId);
                trackingInfo = getTrackingInformation(model, isPreview);

                module.trackEvent({
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
    module.videoPlay = function (videoId, event) {

        // TODO: Do we only want to measure one event per video?
        if (videosPlayed.indexOf(videoId) > -1) {
            // not that video
            return;
        }

        if (event.data === window.YT.PlayerState.PLAYING) {
            videosPlayed.push(videoId);

            module.trackEvent({
                'category': 'Content',
                'action': 'Video Play',
                'label': videoId
            });
        }
    };

    /**
     * Records the fact that the category has been changed.
     *
     * @param category {String}   The category switched to
     * @returns undefined
     */
    module.changeCategory = function (category) {
        module.trackEvent({
            'category': 'category',
            'action': 'select',
            'label': category
        });

        setCustomVar({
            'index': 1,
            'type': 'dimension',
            'value': category
        });
    };

    module.findStoreClick = function (model) {
        var trackingInfo = getTrackingInformation(model, true);

        module.trackEvent({
            'category': trackingInfo.category,
            'action': 'Product Find Store',
            'label': trackingInfo.label
        });
    };

    module.buyClick = function (model) {
        var trackingInfo = getTrackingInformation(model, true);

        module.trackEvent({
            'category': trackingInfo.category,
            'action': 'Product Purchase Click',
            'label': trackingInfo.label
        });
    };

    module.thumbnailClick = function (model) {
        var trackingInfo = getTrackingInformation(model, true),
            sku = model.get('sku'),
            label = sku ? sku+' '+model.get('name') : model.get('name');

        module.trackEvent({
            'category': trackingInfo.category,
            'action': 'Product Thumbnail Click',
            'label': label || trackingInfo.label
        });
    };

    module.imageView = function (model) {
        var trackingInfo = getTrackingInformation(model, true);

        module.trackEvent({
            'category': trackingInfo.category,
            'action': 'Product Image Click',
            'label': trackingInfo.label
        });
    };

    module.pageScroll = _.throttle(
        function () {
            var pageHeight = $(window).innerHeight(),
                windowTop = $(window).scrollTop(),
                page = Math.floor(windowTop / pageHeight);
            
            if (page > pagesScrolled) {
                module.trackEvent({
                    'category': 'Page',
                    'action': 'scroll',
                    'label': page
                });
            }
            pagesScrolled = page;
        }, 2000);

    // Generally, we have views handle event tracking on their own.
    // However, it can be expensive to bind events to every single view.
    // So, to avoid the performance penalty, we do most of our tracking via
    // delegated events.

    // Hook to add on tracking events for the page
    module.pageEventMap = {};

    // Backbone format: { '(event) (selectors)': function(ev), ...  }
    module.defaultEventMap = {
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
                label = trackingInfo.label || '',
                hash;

            if (!label) {
                console.warn('Not tracking event with no label');
                return;
            }

            // for distinguishing product or (mostly content) tiles that
            // have different ids
            if (tileId) {
                label += ' (Tile ' + tileId + ')';

                // add click to our database
                App.vent.trigger('tracking:tile:click', tileId);
            } else {
                console.warn('No tile id present for for tile: ' + label);
            }

            module.trackEvent({
                'category': trackingInfo.category,
                'action': $(this).hasClass('banner') ? 'Purchase' : 'Preview',
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
        'click .social-buttons .button': function (e) {
            var modelId, model, trackingInfo, network, classes, $previewContainer;

            // A bit fragile, but should do
            $previewContainer = $(this).parents('.template.target > div');
            if ($previewContainer) {
                modelId = $previewContainer.attr('id') || '';
                modelId = modelId.replace('preview-', ''); // Remove prefix, if present
            } else {
                modelId = $(this).parents('.tile').attr('id');
            }

            model = App.discovery.collection.get(modelId);
            trackingInfo = getTrackingInformation(model);

            classes = $(this).getClasses();
            network = _.first(_.without(classes, 'button'));

            module.trackEvent({
                'category': trackingInfo.category,
                'action': network,
                'label': trackingInfo.label
            });
        },

        // Content Play (Video)
        // Note:    Handled by `videoStateChange`

        // Content Impressions
        // Product Impressions

        // Exit
        'click header a': function (ev) {
            var link = $(this).attr('href');
            module.trackEvent({
                'category': 'Header',
                'action': 'Clickthrough', // Exit?
                'label': link
            });
        },

        'click #hero-area a': function (ev) {
            var link = $(this).attr('href');
            module.trackEvent({
                'category': 'Hero Area',
                'action': 'Clickthrough', // Exit?
                'label': link
            });
        },
    };

    /**
     * Add an initializer to fetch Google Analytics
     * asynchronously.
     *
     */
    module.addInitializer(function () {
        // this (verbatim) code creates window.ga
        /* jshint ignore:start */
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=0;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
        /* jshint ignore:end */
    });

    /**
     * Add an initializer to fetch Keen.io asynchronously
     * asynchronously.
     *
     */
    module.addInitializer(function() {
        var Keen = window.Keen = Keen || {
            configure: function (e) {
                this._cf = e;
            },
            addEvent: function (e, t, n, i) {
                this._eq = this._eq || [];
                this._eq.push([e, t, n, i]);
            },
            setGlobalProperties: function (e) {
                this._gp = e;
            },
            onChartsReady: function (e) {
                this._ocrq = this._ocrq || [];
                this._ocrq.push(e);
            }
        };
        (function () {
            var e = document.createElement('script');
            e.type = 'text/javascript';
            e.async = !0;
            e.src = ('https:' === document.location.protocol ? 'https://' : 'http://') + 'dc8na2hxrj29i.cloudfront.net/code/keen-2.1.0-min.js';
            var t = document.getElementsByTagName('script')[0];
            t.parentNode.insertBefore(e, t);
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
    module.initialize = function () {
        var gaAccountNumber = App.option('store:gaAccountNumber', false) || App.option('page:gaAccountNumber', 'UA-23764505-25');
        addItem('create', gaAccountNumber, 'auto');

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

        // more events can be declared by the theme without EventManager instances
        eventMap = $.extend(true, {}, module.defaultEventMap, module.pageEventMap);
        // register event maps
        eventManager = new module.EventManager(eventMap);

        App.vent.trigger('trackerInitialized', this);
        // setTrackingDomHooks() on $.ready
    };

    // add mediator triggers if the module exists.
    App.vent.on({
        'tracking:trackEvent': module.trackEvent,
        'tracking:registerTwitterListeners': module.registerTwitterListeners,
        'tracking:registerFacebookListeners': module.registerFacebookListeners,
        'tracking:videoPlay': module.videoPlay,
        'tracking:changeCampaign': module.changeCampaign,
        'tracking:changeCategory': module.changeCategory,
        'tracking:product:buyClick': module.buyClick,
        'tracking:product:findStoreClick': module.findStoreClick,
        'tracking:product:thumbnailClick': module.thumbnailClick,
        'tracking:product:imageView': module.imageView,
        'tracking:feed:scroll': module.pageScroll

    });
};
