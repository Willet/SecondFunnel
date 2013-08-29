/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _, Willet */
// JSLint/Emacs js2-mode directive to stop global 'undefined' warnings.
if (!window.console) {  // shut up JSLint / good practice
    var console = window.console = {
        log: $.noop,
        error: $.noop
    };
}

var broadcast, SecondFunnel, debugOp;

$.getScripts = function (urls, callback, options) {
    // batch getScript with caching
    // callback receives as many ajax xhr objects as the number of urls.

    // like getScript, this function is incompatible with scripts relying on
    // its own tag existing on the page (e.g. firebug, facebook jssdk)
    var calls = _.map(urls, function (url) {
        options = $.extend(options || {}, {
            'dataType': 'script',
            'crossDomain': true,
            'cache': true,
            'url': url
        });
        return $.ajax(options);
    });
    $.when.apply($, calls).done(callback, function () {
        broadcast('deferredScriptsLoaded', urls);
    });
};

broadcast = function () {
    // alias for vent.trigger with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    if (SecondFunnel.option('debug') > 2) {
        console.log('Broadcasting "' + arguments[0] + '" with args=%O', pArgs);
    }
    SecondFunnel.vent.trigger.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.fire(arguments[0], pArgs);
    }
};


debugOp = function () {
    console.log('%O, %O', this, arguments);
};


// Declaration of the SecondFunnel JS application
SecondFunnel = (function (SecondFunnel, $window, $document) {
    "use strict";

    var Tile, TileCollection, FeaturedAreaView, TileView,
        VideoTileView, Discovery, Category, CategoryView,
        CategorySelector, PreviewContent, PreviewWindow,
        TapIndicator, EventManager, ShadowTile;

    // keep reference to options. this needs to be done before classes are declared.
    SecondFunnel.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};
    SecondFunnel.classRegistry = {};
    SecondFunnel.option = function (name, defaultValue) {
        // convenience method for accessing PAGES_INFO or TEST_*
        var opt = Backbone.Marionette.getOption(SecondFunnel, name),
            keyNest = _.compact(name.split(/[:.]/)),
            keyName,
            cursor = SecondFunnel.options,
            i,
            depth;

        if (opt !== undefined && (keyNest.length === 1 && !_.isEmpty(opt))) {
            // getOption() returns a blank object when it thinks it is accessing
            // a nested option so we have to patch that up
            return opt;
        }
        // marionette sucks, so we'll do extra traversing to get stuff out of
        // our nested objects ourselves
        try {
            for (i = 0, depth = keyNest.length; i < depth; i++) {
                keyName = keyNest[i];
                cursor = cursor[keyName];
            }
            if (cursor !== undefined) {
                return cursor;
            }
        } catch (KeyError) {
            // requested traversal path does not exist. do the next line
            console.error('no such path');
        }
        return defaultValue;  // ...and defaultValue defaults to undefined
    };
    try {
        SecondFunnel.options.debug = 0;

        if (window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1') {
            SecondFunnel.options.debug = 1;
        }

        (function (hash) {
            var hashIdx = hash.indexOf('debug=');
            if (hashIdx > -1) {
                SecondFunnel.options.debug = hash[hashIdx + 6];
            }
        }(window.location.hash + window.location.search));
    } catch (e) {
        // this is an optional operation. never let this stop the script.
    }

    Backbone.Marionette.TemplateCache._exists = function (templateId) {
        // Marionette TemplateCache extension to allow checking cache for template
        // Checks if the Template exists in the cache, if not found
        // updates the cache with the template (if it exists), otherwise fail
        // returns true if exists otherwise false.
        var cached = this.templateCaches[templateId],
            cachedTemplate;

        if (cached) {
            return true;
        }

        // template exists but was not cached
        cachedTemplate = new Backbone.Marionette.TemplateCache(templateId);
        try {
            cachedTemplate.load();
            // Only cache on success
            this.templateCaches[templateId] = cachedTemplate;
        } catch (err) {
            if (!(err.name && err.name === "NoTemplateError")) {
                throw err;
            }
        }
        return !!this.templateCaches[templateId];
    };

    Backbone.Marionette.View.prototype.getTemplate = function () {
        // Accept an arbitrary number of template selectors instead of just one.
        // function will return in a short-circuit manner once a template is found.
        var i, templateIDs = Backbone.Marionette.getOption(this, "templates"),
            template = Backbone.Marionette.getOption(this, "template"),
            temp, templateExists, data;

        if (templateIDs) {
            if (typeof templateIDs === 'function') {
                // if given as a function, call it, and expect [<string> selectors]
                templateIDs = templateIDs(this);
            }

            for (i = 0; i < templateIDs.length; i++) {
                data = $.extend({},
                    Backbone.Marionette.getOption(this, "model").attributes);
                data.template = SecondFunnel.getModifiedTemplateName(data.template);

                temp = _.template(templateIDs[i], {
                    'options': SecondFunnel.options,
                    'data': data
                });
                templateExists = Backbone.Marionette.TemplateCache._exists(temp);

                if (templateExists) {
                    // replace this thing's desired template ID to the
                    // highest-order template found
                    template = temp;
                    break;
                }
            }
        }
        return template;
    };

    Backbone.Marionette.ItemView.prototype.render =  function () {
        this.isClosed = false;

        this.triggerMethod("before:render", this);
        this.triggerMethod("item:before:render", this);

        var data = this.serializeData(),
            html;
        data = this.mixinTemplateHelpers(data);
        try {
            var template = this.getTemplate();
            html = Marionette.Renderer.render(template, data);
        } catch (err) {
            // If template not found, signal error if debug is enabled, otherwise
            // just delete the model.
            if (err.name && err.name === "NoTemplateError") {
                SecondFunnel.vent.trigger('log', "Could not found template " +
                    template + ".  View did not render.");
                // Trigger method to signal an error
                this.isClosed = true;
                this.triggerMethod("missing:template", this);
                return this;
            } else {
                throw err;
            }
        }

        this.$el.html(html);
        this.bindUIElements();

        this.triggerMethod("render", this);
        this.triggerMethod("item:rendered", this);

        return this;
    };

    Backbone.Marionette.ItemView.prototype.onMissingTemplate = function () {
        // Default on missing template event
        this.remove();
    };

    SecondFunnel.module("observable", function (observable) {
        // make new module full of transient utilities

        var testUA = function (regex) {
            return regex.test(window.navigator.userAgent);
        };

        observable.mobile = function () {
            return ($window.width() < 768);  // 768 is set in stone now
        };
        observable.touch = function () {
            return ('ontouchstart' in document.documentElement);
        };

        observable.isAniPad = function () {
            // use of this function is highly discouraged, but you know it
            // will be used anyway
            return testUA(/ipad/i);
        };

        observable.onErrorResumeNext = function (func, context) {
            // ms.system.reactive.linq.observable.onerrorresumenext(v=vs.103)
            // the absolutely-no-errors-must-leave-this-function 'decorator'.
            // context should be the caller's 'this'.
            // arguments after context will be passed to func.
            try {
                var pArgs = Array.prototype.slice.call(arguments, 2);
                return func.apply(context || window, pArgs);
            } catch (err) {
                console.error('Exception in %O: %O', func, err);
            }
            return null;  // have a return, just to shut up jslint
        };
    });

    SecondFunnel.module("utils", function (utils) {
        utils.safeString = function (str, opts) {
            // trims the string and checks if it's just 'None'.
            // more checks to come later.
            return $.trim(str).replace(/^(None|undefined|false|0)$/, '');
        };

        utils.makeView = function (classType, params) {
            // view factory to allow views that bind to arbitrary regions
            // and use any template decided at runtime, e.g.
            //   someTemplate = '#derp1'
            //   a = makeView('Layout', {template: someTemplate})
            //   a.render()
            classType = classType || 'ItemView';
            return Backbone.Marionette[classType].extend(params);
        };

        utils.addWidget = function (name, selector, functionality) {
            // add a predefined UI component implemented as a region.
            // name must be unique. if addWidget is called with an existing
            // widget, the old one is overwritten.
            SecondFunnel.options.regions = SecondFunnel.options.regions || {};
            SecondFunnel.options.regionWidgets = SecondFunnel.options.regionWidgets || {};
            SecondFunnel.options.regions[name] = selector;
            SecondFunnel.options.regionWidgets[name] = functionality;
            broadcast('widgetAdded', name, selector, functionality);
        };

        utils.runWidgets = function (viewObject) {
            // process widget regions.
            // each widget function receives args (the view, the $element, option alias).
            var self = viewObject;

            // process itself (if it is a view)
            _.each(SecondFunnel.options.regions, function (selector, name, list) {
                var widgetFunc = SecondFunnel.options.regionWidgets[name];
                self.$(selector).each(function (idx, el) {
                    return widgetFunc(self, $(el), SecondFunnel.option);
                });
            });

            // process children regions (if it is a layout)
            _.each(self.regions, function (selector, name, list) {
                var isWidget = _.contains(SecondFunnel.options.regions, name),
                    widgetFunc = (SecondFunnel.options.regionWidgets || {})[name];
                if (isWidget && widgetFunc) {
                    self.$(selector).each(function (idx, el) {
                        return widgetFunc(self, $(el), SecondFunnel.option);
                    });
                }
            });
        };

        utils.pickImageSize = function (url, minWidth, scalePolicy) {
            // returns a url that is either
            //   - the url, if it is not an image service url, or
            //   - an image url pointing to one that is at least as wide as
            //     minWidth, or
            //   - an image url pointing to one that is at most as wide as
            //     the window width, or
            //   - if minWidth is ridiculously large, master.jpg.
            // if scalePolicy is "max", then the image served is always smaller
            //   than requested.
            var i,
                prevKey = 'pico',
                maxLogicalSize = Math.min($window.width(), $window.height()),
                sizable = /images\.secondfunnel\.com.+\.(jpe?g|png)/.test(url),
                nameRegex = /([^/]+)\.(jpe?g|png)/,
                imageSizes = SecondFunnel.option('imageSizes', {
                    // see Scraper: ImageServiceIntegrationTest.java#L52
                    "pico": 16,
                    "icon": 32,
                    "thumb": 50,
                    "small": 100,
                    "compact": 160,
                    "medium": 240,
                    "large": 480,
                    "grande": 600,
                    "1024x1024": 1024,
                    "master": 2048
                });

            if (!sizable) {
                return url;
            }

            for (i in imageSizes) {
                if (imageSizes.hasOwnProperty(i)) {
                    if (!scalePolicy || scalePolicy === 'min') {
                        if (imageSizes[i] >= minWidth) {
                            return url.replace(nameRegex, i + '.$2');
                        }
                    } else if (scalePolicy === 'max') {
                        if (imageSizes[i] >= minWidth) {
                            return url.replace(nameRegex, prevKey + '.$2');
                        }
                    }
                    if (imageSizes[i] >= maxLogicalSize) {
                        return url.replace(nameRegex, prevKey + '.$2');
                    }
                }
                prevKey = i;
            }
            return url;
        };
    });

    SecondFunnel.module("sharing", function (sharing) {
        sharing.SocialButtons = Backbone.Marionette.View.extend({
            // Acts as a manager for the social buttons; allows us to create arbitrary
            // social buttons.

            // override the template by passing it in: new SocialButtons({ template: ... })
            // template can be a selector or a function(json) ->  <_.template>
            'tagName': 'span',
            'showCount': SecondFunnel.option('showCount', true),
            'buttonTypes': SecondFunnel.option('socialButtons',
                ['facebook', 'twitter', 'pinterest']), // @override via constructor

            'loadSocial': _.once(function (callback) {
                $.getScripts([  // well, load once, right?
                    "//www.youtube.com/iframe_api",
                    "//assets.pinterest.com/js/pinit.js",
                    // "//connect.facebook.net/en_US/all.js",
                    "//platform.twitter.com/widgets.js",
                    "//google-analytics.com/ga.js"
                ], callback);
            }),
            'initSocial': function () {
                // Only initialize the social aspects once; this load the FB script
                // and twitter handlers.
                if (window.FB && _.contains(this.buttonTypes, "facebook")) {
                    window.FB.init({
                        cookie: true,
                        status: false, // No AppID
                        xfbml: true
                    });
                }

                if (window.twttr && window.twttr.widgets &&
                    _.contains(this.buttonTypes, "twitter")) {
                    window.twttr.widgets.load();
                    window.twttr.ready(function (twttr) {
                        twttr.events.bind('tweet', function (event) {
                            SecondFunnel.tracker.registerEvent({
                                "network": "Twitter",
                                "type": "share",
                                "subtype": "shared"
                            });
                        });

                        twttr.events.bind('click', function (event) {
                            var sType;
                            if (event.region === "tweet") {
                                sType = "clicked";
                            } else if (event.region === "tweetcount") {
                                sType = "leftFor";
                            } else {
                                sType = event.region;
                            }

                            SecondFunnel.tracker.registerEvent({
                                "network": "Twitter",
                                "type": "share",
                                "subtype": sType
                            });
                        });
                    });
                }

                // pinterest does its own stuff - just include pinit.js.
                // however, if it is to be disabled, the div needs to go.
                // see 'render' of SocialButtons.
                return this;
            },

            'initialize': function (options) {
                // Initializes the SocialButton CompositeView by determining what
                // social buttons to show and loading the initial config if necessary.
                var self = this;
                // Only load the social once
                this.loadSocial(_.bind(this.initSocial, this));
                this.views = [];

                _.each(self.buttonTypes, function (type) {
                    var count = options.showCount,
                        button = null,
                        template = "#" + type.toLowerCase() + "_social_button_template";
                    type = _.capitalize(type);
                    button = SecondFunnel.sharing.getButton(type);
                    self.views.push(new button({
                        'model': options.model,
                        'template': template,
                        'showCount': self.showCount
                    }));
                });
            },

            'showCondition': function () {
                // @override to false under any condition you don't want buttons to show
                return true;
            },

            'load': function () {
                // Initialize each Social Button; lazy loading to improve
                // page load times.
                _.each(this.views, function (view) {
                    view.load();
                });
                return this;
            },

            'render': function () {
                // Render each child view and append to master.
                var self = this;
                _.each(self.views, function (view) {
                    view.render();
                    if (!view.isClosed) {
                        self.$el.append(view.$el);
                    }
                });
                return this;
            }
        });

        sharing.SocialButtonView = Backbone.Marionette.ItemView.extend({
            // Base object for Social buttons, when adding a new Social button, extend
            // from this class and modify as necessary.
            'events': {
                'click': function (ev) {
                    SecondFunnel.vent.trigger('tracker:registerEvent', {
                        "network": "oneOfThem",
                        "type": "share",
                        "subtype": "clicked"
                    });
                    ev.stopPropagation(); // you did not click below the button
                }
            },

            'initialize': function (options) {
                // Assign attributes to the object
                _.extend(this, options);
            },

            'load': function () {
                // @override: subclasses should override this method
                return this;
            },

            'templateHelpers': function () {  // or {k: v}
                //github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.view.md#viewtemplatehelpers

                // Template Helpers; add additional data to the data we're serializing to
                // render our template.
                var helpers = {},
                    data = this.model.attributes,
                    page = SecondFunnel.option('page', {}),
                    product = data || page.product || {},
                    image = page['stl-image'] || page['featured-image'] || data.image || data.url;

                helpers.url = encodeURIComponent(product.url || image);
                helpers.product = {
                    'url': product.url
                };
                helpers.showCount = this.showCount;
                helpers.image = image;

                // Call the after template handler to allow subclasses to modify this
                // data
                return this.onTemplateHelpers ?
                    this.onTemplateHelpers(helpers) :
                    helpers;
            },

            // 'triggers': { "click .facebook": "event1 event2" },
            // 'onBeforeRender': $.noop,
            'onRender': function () {
                // Hide this element when it's rendered.
                this.$el = this.$el.children();
                this.setElement(this.$el);
                this.$el.parent().hide();

                // process widgets
                SecondFunnel.utils.runWidgets(this);
            },
            // 'onDomRefresh': $.noop,
            // 'onBeforeClose': function () { return true; },
            // 'onClose': $.noop,
            'commas': false
        });

        sharing.FacebookSocialButton = sharing.SocialButtonView.extend({
            // Subclass of the SocialButtonView for FaceBook Social Buttons.
            'load': function () {
                // Onload, render the button and remove the placeholder
                var facebookButton = this.$el;
                if (window.FB && window.FB.XFBML && facebookButton &&
                    facebookButton.length >= 1) {
                    if (!facebookButton.attr('id')) {
                        // generate a unique id for this facebook button
                        // so fb can parse it.
                        var fbId = this.cid + '-fb';
                        facebookButton.attr('id', fbId);

                        // this makes 1 iframe request to fb per button regardless
                        // so stretch out its loading by a second and make the
                        // the page look less owned by the lag
                        window.FB.XFBML.parse(facebookButton[0], function () {
                            facebookButton.find('.placeholder').remove();
                        });
                    }
                }
                return this;
            },

            'onRender': function () {
                // On load we want to add the class 'no-count' if
                // showCount is false.
                this.$el = this.$el.children();
                this.setElement(this.$el);
                if (!this.showCount) {
                    this.$el.addClass('no-count');
                }

                // process widgets
                SecondFunnel.utils.runWidgets(this);
            },

            'onTemplateHelpers': function (helpers) {
                // Additional attributes to add to our template data.
                var url = (helpers.product.url || helpers.image);
                if (url && url.indexOf("facebook") > -1) {
                    url = "http://www.facebook.com/" + /(?:fbid=|http:\/\/www.facebook.com\/)(\d+)/.exec(url)[1];
                }
                helpers.url = url;
                return helpers;
            }
        });

        sharing.TwitterSocialButton = sharing.SocialButtonView.extend({
            // Subclass of the SocialButtonView for Twitter Social Buttons.
            'load': function () {
                // Load the widget when called.
                try {
                    window.twttr.widgets.load();
                } catch (err) {
                    // do other things
                }
                return this;
            }
        });

        sharing.ShareSocialButton = sharing.SocialButtonView.extend({
            // Subclass of SocialButtonView for triggering a Share popup
            'events': {
                'click': function (ev) {
                    // Creates a new popup instead of the default action
                    ev.stopPropagation();
                    ev.preventDefault();
                    var popup = new sharing.SharePopup({
                        'url': this.options.url,
                        'model': this.options.model,
                        'showCount': this.options.showCount
                    });
                    popup.render();
                }
            },

            'onTemplateHelpers': function (helpers) {
                // Catch url for reference on click
                this.options.url = helpers.url;
                return helpers;
            }
        });

        sharing.SharePopup = Backbone.Marionette.ItemView.extend({
            // Displays a popup that provides the viewer with a plethora of other
            // social share options as defined by the designer/developer.
            'tagName': "div",
            'className': "shareContainer previewContainer",
            'template': "#share_popup_template",
            'buttons': SecondFunnel.option('shareSocialButtons', []),

            'events': {
                'click .close, .mask': function (ev) {
                    this.$el.fadeOut(100).remove();
                    this.unbind();
                    this.views = [];
                }
            },

            'onRender': function () {
                var self = this;

                this.$el.css({'display': "table"});
                $('body').append(this.$el.fadeIn(100));

                _.each(this.buttons, function (button) {
                    var share = new sharing.ShareOption(_.extend({
                        'type': button
                    }, self.options));
                    share.render();

                    if (!share.isClosed) {
                        self.$('.share').append(share.$el);
                    }
                });

                // process widgets
                SecondFunnel.utils.runWidgets(this);
            }
        });

        sharing.ShareOption = Backbone.Marionette.ItemView.extend({
            'tagName': "div",
            'className': "shareOption",
            'templates': [
                '#<%= data.type %>_share_popup_option_template'
            ],
            'template': "#share_popup_option_template",

            'templateHelpers': function () {
                var helpers = SecondFunnel.sharing.get(this.options.type);
                if (helpers.url) {
                    helpers.url = _.template(helpers.url,
                        _.extend({
                            'landing': encodeURIComponent(window.location),
                            'title': document.title
                    }, this.options, this.model.attributes));
                }
                this.options.image = helpers.image || "";
                helpers.text = "Share this on " + _.capitalize(this.options.type) + "!";
                return helpers;
            },

            'onRender': function () {
                this.$el.addClass(this.options.type + "_share");
                var $img = this.$('img');
                if ($img.css('background-image') === "none" ||
                    !$img.css('background-image')) {
                    this.$('img').css({'background-image': "url(" + this.options.image + ")" });
                }
                return this;
            }
        });

        sharing.sources = {
            // A mapping of the different sharing options and the related
            // share url.
            // TODO: Can we do better than this ?

            // Main ones (e.g. Facebook, Twitter, Tumblr, etc.)
            'facebook': {
                'url': "//facebook.com/sharer/sharer.php?u=<%= url %>",
                'image': ""
            },
            'twitter': {
                'url': "//twitter.com/share?url=<%= url %>",
                'image': "//abs.twimg.com/a/1377684308/images/resources/twitter-bird-white-on-blue.png"
            },
            'reddit': {
                'url': "//reddit.com/submit?url=<%= url %>",
                'image': ""
            },
            'tumblr': {
                'url': "//tumblr.com/share/photo?source=<%= url %>&caption=<%= caption %>&click_thru=<%= landing %>",
                'image': ""
            },
            'pinterest': {
                'url': "//pinterest.com/pin/create/button/?url=<%= url %>",
                'image': ""
            },

            // Auxiliary ones
            'email': {
                'url': "mailto:user@example.com?subject=<%= subject %>&body=<%= caption %>&#10;<%= url %>",
                'image': ""
            },
            'google+': {
                'url': "//plus.google.com/share?url=<%= url %>",
                'image': ""
            },
            'digg': {
                'url': "//digg.com/submit?url=<%= url %>",
                'image': ""
            },
            'blogger': {
                'url': "//blogger.com/blog-this.g?t=<%= caption %>&u=<%= url %>&n=<%= title %>",
                'image': ""
            },
            'stumbleupon': {
                'url': "//stumbleupon.com/submit?url=<%= url %>",
                'image': ""
            }
        };

        sharing.get = function (type) {
            if (!typeof type === 'string') {
                return {};
            }
            type = type.toLowerCase();
            type = this.sources[type] || {};

            // TODO: Default image + images
            if (!_.isEmpty(type)) {
                type.image = type.image.length ?
                    type.image :
                    this.sources['twitter'].image;
            }
            return type;
        };

        sharing.getButton = function (type) {
            var button;
            switch (type) {
            case "Facebook":
                button = sharing.FacebookSocialButton;
                break;
            case "Twitter":
                button = sharing.TwitterSocialButton;
                break;
            case "Share":
                button = sharing.ShareSocialButton;
                break;
            default:
                button = sharing.SocialButtonView;
                break;
            }
            return button;
        };
    });

    SecondFunnel.module("intentRank",
        function (intentRank) {
            intentRank.base = "http://intentrank-test.elasticbeanstalk.com/intentrank";
            intentRank.templates = {
                'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
                'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
            };

            intentRank.initialize = function (options) {
                // Any additional init declarations go here
                var page = options.page || {},
                    online = !page.offline;

                _.extend(intentRank, {
                    'base': options.IRSource || this.base,
                    'store': options.store,
                    'campaign': options.campaign,
                    // @deprecated: options.categories will be page.categories
                    'categories': page.categories || options.categories || {},
                    'backupResults': options.backupResults || [],
                    'IRResultsCount': options.IRResultsCount || 10,
                    'IRTimeout': options.IRTimeout || 5000,
                    'content': options.content || [],
                    'getResults': online ?
                                  intentRank.getResultsOnline :
                                  intentRank.getResultsOffline
                });

                broadcast('intentRankIntialized', intentRank);
            };

            intentRank.getResultsOffline = function (options, callback) {
                broadcast('beforeintentRankgetResultsOffline', options,
                    callback, intentRank);
                var args = _.toArray(arguments).slice(2);
                args.unshift(intentRank.content);

                broadcast('intentRankgetResultsOffline', options, callback,
                    intentRank);
                return callback.apply(callback, args);
            };

            intentRank.getResultsOnline = function (options, callback) {
                broadcast('beforeintentRankgetResultsOnline', options,
                    callback, intentRank);

                var uri = _.template(intentRank.templates[options.type],
                        _.extend({}, options, intentRank, {
                            'url': intentRank.base
                        })),
                    args = _.toArray(arguments).slice(2);

                $.ajax({
                    'url': uri,
                    'data': {
                        'results': intentRank.IRResultsCount
                    },
                    'contentType': "json",
                    'dataType': 'jsonp',
                    'timeout': intentRank.IRTimeout,
                    'success': function (results) {
                        // Check for non-empty results.
                        results = results.length ?
                                  results :
                            // If no results, fetch from backup
                                  _.shuffle(intentRank.backupResults);
                        results = _.first(results, intentRank.IRResultsCount);
                        args.unshift(results);
                        return callback.apply(callback, args);
                    },
                    'error': function () {
                        SecondFunnel.vent.trigger('log', arguments[1]);
                        // On error, fall back to backup results
                        var results = _.shuffle(intentRank.backupResults);
                        results = _.first(results, intentRank.IRResultsCount);
                        args.unshift(results);
                        return callback.apply(callback, args);
                    }
                });

                broadcast('intentRankgetResultsOffline', options, callback,
                    intentRank);
            };

            intentRank.changeCategory = function (category) {
                // Change the category; category has been validated
                // by the CategoryView, so a check isn't necessary
                broadcast('intentRankChangeCategory', category, intentRank);

                intentRank.campaign = category;
                return intentRank;
            };
        });


    SecondFunnel.module("tracker",
        function (tracker) {
            // TODO: when done, split into its own file
            var isBounce = true,  // this flag set to false once user scrolls down
                videosPlayed = [],
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
                    var category = "appname=pinpoint|" +
                        "storeid=" + SecondFunnel.option('store:id') + "|" +
                        "campaignid=" + SecondFunnel.option('page:id') + "|" +
                        "referrer=" + referrerName() + "|" +
                        "domain=" + parseUri(window.location.href).host;

                    if (SecondFunnel.option('enableTracking', true)) {
                        if (window._gaq) {
                            window._gaq.push(['_trackEvent', category, o.action, o.label, o.value || undefined]);
                        }
                        broadcast('eventTracked', o, category);
                    }
                },

                setCustomVar = function (o) {
                    var slotId = o.slotId,
                        name = o.name,
                        value = o.value,
                        scope = o.scope || 3; // 3 = page-level

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

                tracker.notABounce(o.type);

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

            tracker.registerTwitterListeners = function () {
                if (!window.twttr) {
                    return;
                }
                window.twttr.ready(function (twttr) {
                    twttr.events.bind('tweet', function (event) {
                        tracker.registerEvent({
                            "network": "Twitter",
                            "type": "share",
                            "subtype": "shared"
                        });
                    });

                    twttr.events.bind('click', function (event) {
                        var sType;
                        if (event.region === "tweet") {
                            sType = "clicked";
                        } else if (event.region === "tweetcount") {
                            sType = "leftFor";
                        } else {
                            sType = event.region;
                        }
                        tracker.registerEvent({
                            "network": "Twitter",
                            "type": "share",
                            "subtype": sType
                        });
                    });
                });
            };

            tracker.notABounce = _.once(function (how) {
                // visitor already marked as "non-bounce"
                // this function becomes nothing after it's first run, even
                // after re-initialisation, or if the function throws an exception.
                broadcast('notABounce', how, tracker);

                tracker.registerEvent({
                    "type": "visit",
                    "subtype": "noBounce",
                    "label": how
                });
            });

            tracker.videoStateChange = function (videoId, event) {
                broadcast('videoStateChange', videoId, event, tracker);

                if (videosPlayed.indexOf(videoId) !== -1) {
                    // not that video
                    return;
                }

                if (event.data === window.YT.PlayerState.PLAYING) {
                    videosPlayed.push(videoId);

                    tracker.registerEvent({
                        "type": "content",
                        "subtype": "video",
                        "label": videoId
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

                broadcast('trackerInitialized', tracker);
                // setTrackingDomHooks() on $.ready
            };

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
                    tracker.registerEvent({
                        "type": "???",  // no known values for this new event
                        "subtype": "???",
                        "label": "???"
                    });
                },

                "click .header a": function (ev) {
                    broadcast('headerHover', ev.currentTarget);
                    tracker.registerEvent({
                        "type": "clickthrough",
                        "subtype": "header",
                        "label": $(this).attr("href")
                    });
                },

                "click .previewContainer .close": function () {
                    broadcast('popupClosed');
                    tracker.registerEvent({
                        "type": "???",  // no known values for this new event
                        "subtype": "???",
                        "label": "???"
                    });
                },

                // buy now event
                "click a.buy": function () {
                    broadcast('buyClick');
                    tracker.registerEvent({
                        "type": "clickthrough",
                        "subtype": "buy",
                        "label": $(this).attr("href")
                    });
                },

                // popup open event: product click
                "click .tile.product, .tile.combobox .product": function (e) {
                    // TODO: data('label') === ?
                    broadcast('tileClick');
                    tracker.registerEvent({
                        "type": "inpage",
                        "subtype": "openpopup",
                        "label": $(this).data("label")
                    });
                },

                // lifestyle image click
                "click .tile.combobox .lifestyle, .tile.image, .tile>img": function (e) {
                    broadcast('lifestyleTileClick');
                    tracker.registerEvent({
                        "type": "content",
                        "subtype": "openpopup",
                        "label": $(this).data("label")
                    });
                },

                // can't do click with delegation: stopPropagation in effect
                "hover .social-buttons .button": function (e) {
                    var $button = $(e.currentTarget);
                    broadcast('socialButtonHover', $button);
                    tracker.registerEvent({
                        "type": "inpage",
                        "subtype": "hoverSocialButton",
                        "label": $button.getClasses().join(':')
                    });
                },

                // core metrics: 'Shop Now', 'Find in Store' or similar
                "click .find-store, .in-store": function (e) {
                    var $button = $(e.currentTarget),
                        isFindStore = $button.hasClass('find-store'),
                        isInStore = $button.hasClass('in-store');
                    if (isFindStore) {
                        broadcast('findStoreClick', $button);
                        tracker.registerEvent({
                            "type": "inpage",
                            "subtype": "clickFindStore",
                            "label": "???"  // TODO: decide on a label
                        });
                    }
                    if (isInStore) {
                        broadcast('inStoreClick', $button);
                        tracker.registerEvent({
                            "type": "inpage",
                            "subtype": "clickInStore",
                            "label": "???"  // TODO: decide on a label
                        });
                    }
                },

                "click .pinterest": function () {
                    // social hover and popup pinterest click events
                    tracker.registerEvent({
                        "network": "Pinterest",
                        "type": "share",
                        "subtype": "clicked"
                    });
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
                'tracking:notABounce': tracker.notABounce,
                'tracking:videoStateChange': tracker.videoStateChange,
                'tracking:changeCampaign': tracker.changeCampaign
            });

            // the app initializer init()s it
        });

    SecondFunnel.module("layoutEngine",
        function (layoutEngine) {
            layoutEngine.options = {
                'isInitLayout': true,
                'isResizeBound': true,
                'visibleStyle': {
                    'opacity': 1,
                    'transform': 'none',
                    '-webkit-transform': 'none',
                    '-moz-transform': 'none'
                },
                'hiddenStyle': {
                    'opacity': 0,
                    'transform': 'scale(1)',
                    '-webkit-transform': 'scale(1)',
                    '-moz-transform': 'none'
                }
            };

            layoutEngine.initialize = function ($elem, options) {
                var mobile = SecondFunnel.observable.mobile();

                layoutEngine.selector = options.discoveryItemSelector;
                _.extend(layoutEngine.options, {
                    'itemSelector': options.discoveryItemSelector,
                    'columnWidth': options.columnWidth(),
                    'isAnimated': !mobile,
                    'transitionDuration': (mobile ?
                                           options.masonryMobileAnimationDuration :
                                           options.masonryAnimationDuration) + 's'
                }, options.masonry);

                $elem.masonry(layoutEngine.options).masonry('bindResize');
                layoutEngine.$el = $elem;
                broadcast('layoutEngineIntialized', layoutEngine);
                // @temporary
                layoutEngine.imagesLoaded = layoutEngine.imagesLoadedTransitional;
            };

            layoutEngine.call = function (callback, $fragment) {
                if (typeof callback !== 'string') {
                    SecondFunnel.vent.trigger('log', "Unsupported type " +
                        (typeof callback) + " passed to LayoutEngine.");
                    return layoutEngine;
                }
                if (!layoutEngine[callback]) {
                    SecondFunnel.vent.trigger('log',
                        "LayoutEngine has no property " +
                            callback + ".");
                    return layoutEngine;
                }

                // turn name of function into function itself
                var args = _.toArray(arguments);
                args[0] = layoutEngine[callback];  // [callback, fragment, ...]

                return layoutEngine.imagesLoaded.apply(layoutEngine, args);
            };

            layoutEngine.append = function ($fragment, callback) {
                broadcast('fragmentAppended', $fragment);
                if ($fragment.length) {
                    layoutEngine.$el.append($fragment).masonry('appended', $fragment);
                }
                return callback ? callback($fragment) : layoutEngine;
            };

            layoutEngine.stamp = function (element) {
                broadcast('elementStamped', element);
                layoutEngine.$el.masonry('stamp', element);
                return layoutEngine;
            };

            layoutEngine.unstamp = function (element) {
                broadcast('elementUnstamped', element);
                layoutEngine.$el.masonry('unstamp', element);
                return layoutEngine;
            };

            layoutEngine.layout = function () {
                layoutEngine.$el.masonry('layout');
                return layoutEngine;
            };

            layoutEngine.reload = function ($fragment) {
                layoutEngine.$el.masonry('reloadItems');
                layoutEngine.$el.masonry();
                return layoutEngine;
            };

            layoutEngine.insert = function ($fragment, $target, callback) {
                var initialBottom = $target.position().top + $target.height();
                if ($fragment.length) {
                    // Find a target that is low enough on the screen to insert after
                    while ($target.position().top <= initialBottom &&
                           $target.next().length > 0) {
                        $target = $target.next();
                    }
                    $fragment.insertAfter($target);
                    layoutEngine.reload();
                }
                return callback ? callback($fragment) : layoutEngine;
            };

            layoutEngine.clear = function () {
                // Resets the LayoutEngine's instance so that it is empty
                layoutEngine.$el
                    .masonry('destroy')
                    .html("")
                    .css('position', 'relative')
                    .masonry(layoutEngine.options);
            };

            layoutEngine.imagesLoaded = function (callback, $fragment) {
                // This function is based on the understanding that the ImageService will
                // return dimensions and/or a dominant colour; elements in the $fragment have
                // assigned widths and heights; (e.g. .css('width', '100px'))
                var args = _.toArray(arguments).slice(1),
                    toLoad = $fragment.children('img').length,
                    $badImages = $();
                // We set the background image of the tile image as the dominant colour/loading;
                // when the image is loaded, we replace the src.
                $fragment.children('img').each(function () {
                    // Create a dummy image to load the image
                    var img = new Image(),
                        self = this;
                    img.src = $(this).attr('src');
                    // Clear the src attribute so it doesn't load there
                    $(this).attr('src', '');

                    // Now apply handlers
                    var onImage = function () {
                        // Function to check on each image load/error
                        --toLoad;
                        if ($badImages.length !== 0 && toLoad == 0) {
                            // If broken images exist, remove them and
                            // reload the layout.
                            $badImages.remove();
                            layoutEngine.reload();
                        }
                    };
                    img.onload = function () {
                        self.src = img.src;
                        onImage();
                    };

                    img.onerror = function () {
                        broadcast('tileRemoved', self);
                        $badImages = $badImages.add($(self).parents(layoutEngine.selector));
                        onImage();
                    };
                });
                return callback.apply(layoutEngine, args);
            };

            layoutEngine.imagesLoadedTransitional = function (callback, $fragment) {
                // @deprecated: Use until ImageService is reading/returns dominant colour
                // Calls the broken handler to remove broken images as they appear;
                // when all images are loaded, calls the appropriate layout function
                var args = _.toArray(arguments).slice(2),
                    $badImages = $(),
                    imgLoad = imagesLoaded($fragment.children('img'));
                imgLoad.on('always', function (imgLoad) {
                    // When all images are loaded and/or error'd remove the broken ones, and load
                    // the good ones.
                    if (imgLoad.hasAnyBroken) {
                        // Iterate through the images and collect the bad images.
                        var $badImages = $();
                        _.each(imgLoad.images, function (image) {
                            if (!image.isLoaded) {
                                var $img = $(image.img),
                                    $elem = $img.parents(layoutEngine.selector);
                                $fragment = $fragment.filter(function () {
                                    return !$(this).is($elem);
                                });
                                $badImages = $badImages.add($elem);
                            }
                        });
                        // Batch removal of bad elements
                        $badImages.remove();
                    }
                    // Trigger tracking event and call the callback
                    SecondFunnel.vent.trigger('tracking:trackEvent', {
                        'action': "network=|actionType=impression|actionSubtype=productImpression|actionScope=???",
                        'label': 'productViewed',
                        'value': ''
                    });
                    args.unshift($fragment);
                    callback.apply(layoutEngine, args);
                });
                return layoutEngine;
            };
        });


    Tile = Backbone.Model.extend({
        'defaults': {
            // Default product tile settings, some tiles don't
            // come specifying a type or caption
            'caption': "Shop product",
            'tile-id': null,
            'content-type': "product",
            'related-products': [],
            // Awaiting ImageService for a name
            // TODO: What's the real name?
            'dominant-color': "pink"
        },

        'initialize': function (attributes, options) {
            var videoTypes = ["youtube", "video"],
                type = this.get('content-type').toLowerCase();

            this.type = 'image';  // TODO: what is this
            this.set({
                "type": "image",
                "caption": SecondFunnel.utils.safeString(this.get("caption"))
            });
            if (_.contains(videoTypes, type)) {
                this.type = 'video';
            }
            broadcast('tileModelIntialized', this);
        },

        'sync': function () {
            return false;
        },

        'is': function (type) {
            // check if a tile is of (type). the type is _not_ the tile's template.
            return this.get('content-type').toLowerCase() === type.toLowerCase();
        },

        'createView': function () {
            var targetClassName, TargetClass, view;

            switch (this.type) {
            case "video":
                TargetClass = VideoTileView;
                break;
            default:
                targetClassName = _.capitalize(this.type) + 'TileView';
                if (window[targetClassName] !== undefined) {
                    TargetClass = window[targetClassName];
                    break;
                }
                if (SecondFunnel.classRegistry &&
                    SecondFunnel.classRegistry[targetClassName] !== undefined) {
                    // if designers want to define a new tile view, they must
                    // let SecondFunnel know about its existence.
                    TargetClass = SecondFunnel.classRegistry[targetClassName];
                    break;
                }
                TargetClass = TileView;
            }
            // undeclared / class not found in scope
            view = new TargetClass({model: this});
            broadcast('tileViewIntialized', view, this);
            return view.render();
        }
    });

    TileCollection = Backbone.Collection.extend({
        // Our TileCollection manages ALL the tiles on the page.
        'model': function (attrs) {
            var SubClass = 'Tile';
            if (window[SubClass]) {
                return new window[SubClass](attrs);
            }
            return new Tile(attrs);  // base class
        },
        'loading': false,
        'totalItems': null,

        'initialize': function (arrayOfData) {
            // Our TileCollection starts by rendering several Tiles using the
            // data it is passed.
            var data;
            for (data in arrayOfData) {  // Generate Tile
                if (arrayOfData.hasOwnProperty(data)) {
                    this.add(new Tile(data));
                }
            }
            broadcast('tileCollectionIntialized', this);
        }
    });

    FeaturedAreaView = Backbone.Marionette.ItemView.extend({
        // $(...).html() defaults to the first item successfully selected
        // so featured will be used only if stl is not found.
        'model': new Tile(SecondFunnel.option('featured')),
        'template': "#stl_template, #featured_template, #hero_template",
        'onRender': function () {
            if (this.$el.length) {  // if something rendered, it was successful
                $('#hero-area').html(this.$el.html());
            }

            // process widgets
            SecondFunnel.utils.runWidgets(this);
        }
    });

    TileView = Backbone.Marionette.Layout.extend({
        // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
        'tagName': SecondFunnel.option('tileElement', "div"),
        'templates': function (currentView) {
            return [
                "#<%= data.template %>_<%= data['content-type'] %>_tile_template",
                "#<%= data['content-type'] %>_<%= data.template %>_tile_template",
                "#<%= data.template %>_tile_template",
                "#product_tile_template" // default
            ];
        },
        'template': "#product_tile_template",
        'className': SecondFunnel.option('discoveryItemSelector',
            '').substring(1),

        'events': {
            'click': "onClick",
            'mouseenter': "onHover",
            "mouseleave": "onHover"
        },

        'regions': _.extend({}, {
            'socialButtons': '.social-buttons',
            'tapIndicator': '.tap-indicator-target'
        }, SecondFunnel.options.regions || {}),

        'initialize': function (options) {
            // Creates the TileView using the options.  Subclasses should not override this
            // method, rather provide an 'onInitialize' function
            var data = options.model.attributes,
                self = this;

            _.each(data['content-type'].toLowerCase().split(),
                function (cName) {
                    self.className += " " + cName;
                });
            this.$el.attr({
                'class': this.className,
                'id': this.cid
            });

            // do some kind of magic such that these methods are always called
            // with its context being this object.
            _.bindAll(this, 'close', 'modelChanged');

            // If the tile model is changed, re-render the tile
            this.listenTo(this.model, 'changed', this.modelChanged);

            // If the tile model is removed, remove the DOM element
            this.listenTo(this.model, 'destroy', this.close);
            // Call onInitialize if it exists
            if (this.onInitialize) {
                this.onInitialize(options);
            }
        },

        'modelChanged': function (model, value) {
            this.render();
        },

        'onHover': function (ev) {
            // Trigger tile hover event with event and tile
            SecondFunnel.vent.trigger("tileHover", ev, this);
            if (!SecondFunnel.observable.mobile() &&
                !SecondFunnel.observable.touch() &&
                this.socialButtons && this.socialButtons.$el &&
                this.socialButtons.$el.children().length) {
                var inOrOut = (ev.type === 'mouseenter') ? 'fadeIn'
                    : 'fadeOut';
                this.socialButtons.$el[inOrOut](200);
                this.socialButtons.currentView.load();
            }
        },

        'onClick': function (ev) {
            var tile = this.model,
                preview = new PreviewWindow({
                    'model': tile,
                    'caller': ev.currentTarget
                });
            SecondFunnel.vent.trigger("tileClicked", ev, this);
        },

        'onBeforeRender': function () {
            var maxImageSize,
                self = this;
            try {
                maxImageSize = _.findWhere(this.model.images[0].sizes,
                    {'name': 'master'})[0];
                this.model.set('size', maxImageSize);

                if (Math.random() > 0.333 && maxImageSize.width >= 512) {
                    this.$el.addClass('wide');
                }  // else: leave it as 1-col
            } catch (imageServiceNotReady) {
                if (Math.random() < 0.333) {
                    this.$el.addClass('wide');
                }
            }
            // Listen for the image being removed from the DOM, if it is, remove
            // the View/Model to free memory
            this.$el.on('remove', function (ev) {
                if (ev.target === self.el) {
                    self.model.destroy();
                }
            });
        },

        'onMissingTemplate': function () {
            // If a tile fails to load, destroy the model
            // and subsequently this tile.
            this.model.destroy();
            this.close();
        },

        'onRender': function () {
            if (this.model.get('size')) {
                // Check if ImageService is ready
                this.$("img").css({
                    'background-color': this.model.get('dominant-color'),
                    'width': this.model.get('size').width,
                    'height': this.model.get('size').height
                });
            }

            // semi-stupid view-based resizer
            var tileImg = this.$('img.focus'),
                columns = (this.$el.hasClass('wide') && $window.width() > 480) ? 2 : 1,
                columnWidth = SecondFunnel.option('columnWidth', $.noop)() || 256;
            if (tileImg.length) {
                tileImg.attr('src', SecondFunnel.utils.pickImageSize(tileImg.attr('src'),
                                    columnWidth * columns));
            }

            if (this.tapIndicator && this.socialButtons) {
                // Need to do this check in case layout is closing due
                // to broken images.
                if (SecondFunnel.sharing.SocialButtons.prototype.buttonTypes.length && 
                    !(SecondFunnel.observable.touch() || SecondFunnel.observable.mobile())) {
                    this.socialButtons.show(new SecondFunnel.sharing.SocialButtons({model: this.model}));
                }
                this.tapIndicator.show(new TapIndicator());
            }

            this.$el.scaleImages();

            // process widgets
            SecondFunnel.utils.runWidgets(this);
        }
    });

    // TODO: Seperate this into modules/seperate files
    VideoTileView = TileView.extend({
        // VideoTile extends from TileView, allows playing of Video files; for
        // now, we only support YT
        'onInitialize': function (options) {
            // Add here additional things to do when loading a VideoTile
            this.$el.addClass('wide');

            if (this.model.is('youtube')) {
                this.model.set("thumbnail", 'http://i.ytimg.com/vi/' +
                                            this.model.get('original-id') +
                                            '/hqdefault.jpg');
            }

            // Determine which click handler to use; determined by the
            // content type.
            var handler = _.capitalize(this.model.get('content-type'));
            this.onClick = this['on' + handler] || this.onVideo;
        },

        'onYoutube': function (ev) {
            // Renders a YouTube video in the tile
            var thumbId = 'thumb-' + this.cid,
                $thumb = this.$('div.thumbnail'),
                self = this;

            if (typeof window.YT === 'undefined') {
                window.open(this.model.get('original-url'));
                return;
            }

            $thumb.attr('id', thumbId).wrap('<div class="video-container" />');
            var player = new window.YT.Player(thumbId, {
                'width': $thumb.width(),
                'height': $thumb.height(),
                'videoId': this.model.attributes['original-id'] || this.model.id,
                'playerVars': {
                    'wmode': 'opaque',
                    'autoplay': 1,
                    'controls': SecondFunnel.observable.mobile()
                },
                'events': {
                    'onReady': $.noop,
                    'onStateChange': function (newState) {
                        SecondFunnel.tracker.videoStateChange(
                            self.model.attributes['original-id'] || self.model.id,
                            newState
                        );
                        switch (newState) {
                        case window.YT.PlayerState.ENDED:
                            self.onPlaybackEnd();
                            break;
                        default:
                            break;
                        }
                    },
                    'onError': $.noop
                }
            });
        },

        'onVideo': function () {
            // TODO: play videos more appropriately
            window.open(this.model.get('original-url') || this.model.get('url'));
        },

        'onPlaybackEnd': function (ev) {
            SecondFunnel.vent.trigger("videoEnded", ev, this);
        }
    });

    ShadowTile = Tile.extend({
        // based on a View, this object contains a get() and a set()
        // that does NOT alter its original model.
        'propBag': {},
        'get': function (key) {
            return this.propBag[key] || Backbone.Model.prototype.get.apply(this, arguments);
        },
        'set': function (key, val, options) {
            this.propBag[key] = val;
            return this;
        }
    });

    Discovery = Backbone.Marionette.CompositeView.extend({
        // Manages the HTML/View of ALL the tiles on the page (our discovery area)
        // tagName: "div"
        'el': $(SecondFunnel.option('discoveryTarget')),
        'itemView': TileView,
        'collection': null,
        'loading': false,
        'lastScrollTop': 0,

        // prevent default appendHtml behaviour (append in batch)
        'appendHtml': $.noop,

        'initialize': function (options) {
            var self = this;
            // Initialize IntentRank; use as a seperate module to make changes easier.
            SecondFunnel.intentRank.initialize(options);
            // Black box Masonry (this will make migrating easier in the future)
            SecondFunnel.layoutEngine.initialize(this.$el,
                options);
            this.collection = new TileCollection();
            this.categories = new CategorySelector(options.categories || []);
            this.attachListeners();

            // If the collection has initial values, lay them out
            if (options.initialResults && options.initialResults.length > 0) {
                this.layoutResults(options.initialResults, undefined,
                    function () {
                        self.getTiles();
                    });
            } else {
                // Load additional results and add them to our collection
                this.getTiles();
            }
        },

        'attachListeners': function () {
            // TODO: Find a better way than this...
            _.bindAll(this, 'pageScroll', 'toggleLoading',
                'layoutResults');
            $window
                .scroll(_.throttle(this.pageScroll, 500))
                .resize(_.throttle(function () {
                    // did you know any DOM element without resize events
                    // can still react to potential resizes by having its
                    // own .bind('resize', function () {})?
                    $('.resizable', document).resize();
                }, 500));

            // Vent Listeners
            SecondFunnel.vent.on("tileClicked", this.updateContentStream,
                this);
            SecondFunnel.vent.on('changeCampaign', this.categoryChanged, this);
            return this;
        },

        'getTiles': function (options, $tile) {
            if (!this.loading) {
                this.toggleLoading();
                options = options || {};
                options.type = options.type || 'campaign';
                SecondFunnel.intentRank.getResults(options,
                    this.layoutResults, $tile);
            }
            return this;
        },

        'layoutResults': function (data, tile, callback) {
            var self = this,
                $fragment = $();
            callback = callback || this.toggleLoading;

            // Check if we don't have anything
            if (data.length === 0) {
                return this.toggleLoading();
            }

            // If we have data to use.
            data = this.filter(data);
            _.each(data, function (tileData) {
                // Create the new tiles using the data
                var tile = new Tile(tileData),
                    img = tile.get('image'),
                    view = tile.createView();

                if (!view.isClosed) {
                    // Ensure we were given something
                    self.collection.add(tile);
                    $fragment = $fragment.add(view.$el);
                }
            });

            if (tile) {
                SecondFunnel.layoutEngine.call('insert', $fragment, tile.$el,
                    callback);
            } else {
                SecondFunnel.layoutEngine.call('append', $fragment,
                    callback);
            }
            return this;
        },

        'filter': function (content, selector) {
            // Filter the content in the LayoutEngine based on the selector
            // passed and the criteria/filters defined in the SecondFunnel options.
            var filters = this.options.filters || [];
            filters.push(selector);
            filters = _.flatten(filters);

            for (var i = 0; i < filters.length; ++i) {
                var filter = filters[i];
                if (content.length === 0) {
                    break;
                }
                switch (typeof filter) {
                case 'function':
                    content = _.filter(content, filter);
                    break;
                case 'object':
                    content = _.where(content, filter);
                    break;
                }
            }
            return content;
        },

        'updateContentStream': function (ev, tile) {
            // Loads in related content below the specified tile
            var id = tile.model.get('tile-id');
            return id === null ? this :
                   this.getTiles({
                       'type': "content",
                       'id': id
                   }, tile);
        },

        'categoryChanged': function (ev, category) {
            // Changes the category (campaign) by refreshign IntentRank, clearing
            // the Layout Engine and collecting new tiles.
            var self = this;
            if (this.loading) {
                setTimeout(function () {
                    self.categoryChanged(ev, category);
                }, 100);
            } else {
                SecondFunnel.intentRank.changeCategory(category.model.get('id'));
                SecondFunnel.layoutEngine.clear();
                return this.getTiles();
            }
            return this;
        },

        'toggleLoading': function (bool) {
            if (typeof bool === 'boolean') {
                this.loading = bool;
            } else {
                this.loading = !this.loading;
            }
            return this;
        },

        'pageScroll': function () {
            var pageBottomPos = $window.innerHeight() + $window.scrollTop(),
                documentBottomPos = $document.height(),
                viewportHeights = $window.innerHeight() * (SecondFunnel.option('prefetchHeight',
                    1));

            if (pageBottomPos >= documentBottomPos - viewportHeights && !this.loading) {
                this.getTiles();
            }

            // detect scrolling detection. not used for anything yet.
            var st = $window.scrollTop();
            if (st > this.lastScrollTop) {
                broadcast('scrollDown', this);
            } else {
                broadcast('scrollUp', this);
            }
            this.lastScrollTop = st;
        }
    });

    Category = Backbone.Model.extend({
        // Base empty category, no functionality needed here
    });

    CategoryView = Backbone.Marionette.ItemView.extend({
        'events': {
            'click': function (ev) {
                ev.preventDefault();
                SecondFunnel.vent.trigger('changeCampaign', ev, this);
            }
        },

        'initialize': function (options) {
            // Initializes the category view, expects some el to use
            this.el = options.el;
            this.$el = $(this.el);
            delete options.$el;
            this.model = new Category(options);
        }
    });

    CategorySelector = Backbone.Marionette.CompositeView.extend({
        // This ItemView does not create an element, rather is passed
        // the element that it will use for category selection
        itemView: CategoryView,

        'initialize': function (categories) {
            // Initialize a category view for each object with a
            // data-category option.
            var views = [];
            $('[data-category]').each(function () {
                var id = $(this).attr('data-category');
                if (_.findWhere(categories, {'id': Number(id)})) {
                    // Make sure category is a valid one.
                    views.push(new CategoryView({
                        'id': id,
                        'el': this
                    }));
                }
            });
            this.views = views;
        }
    });

    PreviewContent = Backbone.Marionette.ItemView.extend({
        'template': '#tile_preview_template',
        'templates': function (currentView) {
            var defaultTemplateRules = [
                // supported contexts: options, data
                '#<%= options.store.name %>_<%= data.template %>_mobile_preview_template',
                '#<%= options.store.name %>_<%= data.template %>_preview_template',
                '#<%= data.template %>_mobile_preview_template',
                '#<%= data.template %>_preview_template',
                '#tile_mobile_preview_template', // fallback
                '#tile_preview_template' // fallback
            ];

            if (!SecondFunnel.observable.mobile()) {
                // remove mobile templates if it isn't mobile, since they take
                // higher precedence by default
                defaultTemplateRules = _.reject(defaultTemplateRules,
                    function (t) {
                        return t.indexOf('mobile') >= 0;
                    });
            }
            return defaultTemplateRules;
        },
        'onRender': function () {
            // ItemViews don't have regions - have to do it manually
            var buttons, width;
            if (!(SecondFunnel.observable.touch() || SecondFunnel.observable.mobile())) {
                buttons = new SecondFunnel.sharing.SocialButtons({model: this.model}).render().load().$el;
                this.$('.social-buttons').append(buttons);
            }
            width = Backbone.Marionette.getOption(this, 'width');
            if (width) {
                this.$('.content').css('width', width + 'px');
            }

            this.$el.scaleImages();

            // process widgets
            SecondFunnel.utils.runWidgets(this);

            // out of scope
            $('.scrollable', '.previewContainer').scrollable(true);
            broadcast('previewRendered', this);
        }
    });


    PreviewWindow = Backbone.Marionette.Layout.extend({
        'tagName': "div",
        'className': "previewContainer",
        'template': "#preview_container_template",
        'events': {
            'click .close, .mask': function () {
                this.$el.scrollable(false);
                this.$el.fadeOut(SecondFunnel.option('previewAnimationDuration'));
                this.close();
            }
        },

        'regions': {
            'content': '.template.target',
            'socialButtons': '.social-buttons'
        },


        'initialize': function (options) {
            // Initialize the PreviewWindow by rendering the content to
            // display in it as well.
            this.render();
            if (!this.isClosed) {
                this.content.show(new PreviewContent({
                    'model': options.model,
                    'caller': options.caller
                }));
                if (this.content.currentView.isClosed) {
                    this.close();
                }
            }
        },

        'onMissingTemplate': function () {
            this.close();
        },

        'onBeforeRender': function () {

        },

        'templateHelpers': function () {
            // return {data: $.extend({}, this.options, {template: this.template})};
        },

        'onRender': function () {
            this.$el.css({display: "table"});
            this.$el.scaleImages();

            // process widgets
            SecondFunnel.utils.runWidgets(this);

            $('body').append(this.$el.fadeIn(SecondFunnel.option('previewAnimationDuration')));
        }
    });

    TapIndicator = Backbone.Marionette.ItemView.extend({
        'template': "#tap_indicator_template",
        'className': 'tap_indicator animated fadeIn',
        'onBeforeRender': function () {
            // http://jsperf.com/hasclass-vs-toggleclass
            // toggleClass with a boolean is 55% slower than manual checks
            if (SecondFunnel.observable.touch()) {
                $('html').addClass('touch-enabled');
            } else {
                $('html').removeClass('touch-enabled');
            }
        }
    });

    EventManager = Backbone.View.extend({
        // Top-level event binding wrapper. all events bubble up to this level.
        // the theme can declare as many event handlers as they like by creating
        // their own new EventManager({ event: handler, event: ... })s.
        'el': $window.add($document),
        'initialize': function (bindings) {
            var self = this;
            _.each(bindings, function (func, key, l) {
                var event = key.substr(0, key.indexOf(' ')),
                    selectors = key.substr(key.indexOf(' ') + 1);
                self.$el.on(event, selectors, func);
                if (SecondFunnel.option('debug', 0) > 0) {
                    console.log('regEvent ' + key);
                }
            });
        }
    });

    // expose some classes (only if required)
    SecondFunnel.classRegistry = {
        Discovery: Discovery,
        EventManager: EventManager,
        FeaturedAreaView: FeaturedAreaView,
        ShadowTile: ShadowTile
    };

    return SecondFunnel;
}(new Backbone.Marionette.Application(), $(window), $(document)));


SecondFunnel.addInitializer(function (options) {
    // JQuery Special event to listen to delete
    // stackoverflow.com/questions/2200494
    // does not work with jQuery UI
    // does not work when affected by html(), replace(), replaceWith(), ...
    var ev = new $.Event('remove'),
        orig = $.fn.remove;
    $.fn.remove = function () {
        $(this).trigger(ev);
        return orig.apply(this, arguments);
    };

    $.fn.scrollable = $.fn.scrollable || function (yesOrNo) {
        // make an element scrollable on mobile.
        if (SecondFunnel.observable.touch()) { //if touch events exist...
            var $el = $(this),  // warning: multiple selectors
                $html = $('html'),
                $body = $('body'),
                scrollPosition;

            if (yesOrNo) {  // lock
                scrollPosition = [
                    self.pageXOffset || document.documentElement.scrollLeft || document.body.scrollLeft,
                    self.pageYOffset || document.documentElement.scrollTop  || document.body.scrollTop
                ];

                $html.data({
                    'scroll-position': scrollPosition,
                    'previous-overflow': $html.css('overflow')
                });

                $html.css({
                    'overflow': 'hidden',
                    'height': '100%'
                });

                $body.data('previous-overflow', $body.css('overflow'));
                $body.css({
                    'overflow': 'hidden',
                    'height': '100%'
                });

                $el
                    .height(1.5 * $(window).height())
                    .css('max-height', '100%');

            } else {
                scrollPosition = $html.data('scroll-position');

                $html.css({
                    'overflow': $html.data('previous-overflow'),
                    'height': 'auto'
                });
                $body.css({
                    'overflow': $body.data('previous-overflow'),
                    'height': 'auto'
                });
            }
            window.scrollTo(scrollPosition[0], scrollPosition[1]);
        }
    };

    $.fn.getClasses = $.fn.getClasses || function () {
        // random helper. get an element's list of classes.
        // example output: ['facebook', 'button']
        return _.compact($(this).attr('class').split(' ').map($.trim));
    };

    $.fn.scaleImages = $.fn.scaleImages || function () {
        // looks for .auto-scale elements and replace them with an image.
        $(this).find('img.auto-scale').each(function () {
            var $el = $(this),
                data = $el.data();
            if (data.src && data.size) {
                $el.attr('src', SecondFunnel.utils.pickImageSize(data.src, data.size));
            }
        });
    };

    // underscore's fancy pants capitalize()
    _.mixin({
        'capitalize': function (string) {
            return string.charAt(0).toUpperCase() + string.substring(1).toLowerCase();
        }
    });
});

// Add SecondFunnel component(s)
SecondFunnel.addInitializer(function (options) {
    window.SecondFunnel = SecondFunnel;

    SecondFunnel.getModifiedTemplateName = function (name) {
        return name.replace(/(styld[\.\-]by|tumblr|pinterest|facebook|instagram)/i,
            'image');
    };
});

SecondFunnel.addInitializer(function (options) {
    // delegated analytics bindings
    var defaults = new SecondFunnel.classRegistry.EventManager(SecondFunnel.tracker.defaultEventMap),
        customs = new SecondFunnel.classRegistry.EventManager(options.events);
});

SecondFunnel.addInitializer(function (options) {
    if (SecondFunnel.option('debug', false) > 5) {
        $(document).ready(function () {
            // don't use getScript, firebug needs to know its src path
            // and getScript removes the tag so firebug doesn't know what to do
            var tag = document.createElement('script'),
                firstScriptTag;
            tag.src = "https://getfirebug.com/firebug-lite.js";

            firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            broadcast('firebugLoaded');
        });
    }
});

SecondFunnel.addInitializer(function (options) {
    try {
        var fa = new SecondFunnel.classRegistry.FeaturedAreaView();
        fa.render();
        broadcast('featureAreaRendered', fa);
    } catch (err) {
        // marionette throws an error if no hero templates are found or needed.
        // it is safe to ignore it.
        broadcast('featureAreaNotRendered');
    }
});

SecondFunnel.addInitializer(function (options) {
    // Add our initializer, this allows us to pass a series of tiles
    // to be displayed immediately (and first) on the landing page.
    broadcast('beforeInit', options, SecondFunnel);

    $('.brand-label').text(options.store.displayName ||
                           _.capitalize(options.store.name) ||
                           'Brand Name');

    SecondFunnel.discovery = new SecondFunnel.classRegistry.Discovery(options);
    SecondFunnel.tracker.init();
    broadcast('finished', options, SecondFunnel);
});
