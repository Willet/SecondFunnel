SecondFunnel.module("sharing", function (sharing, SecondFunnel) {
    "use strict";

    var $document = $(document),
        $window = $(window),
        getButton = function (type) {
            // returns 'best' button class based on requested type.
            type = _.capitalize(type);  // e.g. Facebook

            // if we define a custom button class, return that.
            if (sharing[type + 'SocialButton']) {
                return sharing[type + 'SocialButton'];
            }
            // otherwise, return the default.
            return sharing.SocialButton;
        },
        sources = _.extend({}, {
            // A mapping of the different sharing options and the related
            // share url.

            // add more via PAGES_INFO.shareSources.

            // Main ones (e.g. Facebook, Twitter, Tumblr, etc.)
            'facebook': "//facebook.com/sharer/sharer.php?u=<%= url %>",
            'twitter': "//twitter.com/share?url=<%= url %>",
            'tumblr': "//tumblr.com/share/photo?source=<%= url %>&caption=<%= caption %>&click_thru=<%= landing %>",
            'pinterest': "//pinterest.com/pin/create/button/?url=<%= url %>",

            // Auxiliary ones
            'google+': "//plus.google.com/share?url=<%= url %>",
            'reddit': "//reddit.com/submit?url=<%= url %>",
            'email': "mailto: ?subject=<%= title %>&body=<%= caption %>%20<%= url %>",
            'digg': "//digg.com/submit?url=<%= url %>",
            'blogger': "//blogger.com/blog-this.g?t=<%= caption %>&u=<%= url %>&n=<%= title %>",
            'stumbleupon': "//stumbleupon.com/submit?url=<%= url %>"
        }, SecondFunnel.option('shareSources'));

    sharing.SocialButtons = Backbone.Marionette.View.extend({
        // Container for the social buttons; allows us to create arbitrary
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
                    'cookie': true,
                    'status': false, // No AppID
                    'xfbml': true
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
            // Initializes the SocialButton View by determining what
            // social buttons to show and loading the initial config if necessary.
            var self = this;
            // Only load the social once
            this.loadSocial(_.bind(this.initSocial, this));
            this.views = [];  // list of button views (used by marionette)

            _.each(_.compact(self.buttonTypes), function (type) {
                var count = options.showCount || false,
                    ButtonClass,
                    template = "#" + type.toLowerCase() + "_social_button_template";
                ButtonClass = getButton(type);
                self.views.push(new ButtonClass({
                    'model': options.model,
                    'template': template,
                    'showCount': self.showCount
                }));
            });
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

    sharing.SocialButton = Backbone.Marionette.ItemView.extend({
        // Base object for Social buttons, when adding a new Social button, extend
        // from this class and modify as necessary.
        'events': {
            'click': function (ev) {
                SecondFunnel.vent.trigger('tracker:registerEvent', {
                    "network": "oneOfThem",
                    "type": "share",
                    "subtype": "clicked"
                });
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

        'showCondition': function () {
            // @override to false under any condition you don't want buttons to show
            return SecondFunnel.option('socialButtonsEnableCondition')(this);
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

        'onBeforeRender': function () {
            if (!this.showCondition()) {
                this.unbind();
                this.close();
            }
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

    sharing.FacebookSocialButton = sharing.SocialButton.extend({
        // Subclass of the SocialButton for FaceBook Social Buttons.
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

                    // after the button is parsed, remove its dummy placeholder
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

    sharing.TwitterSocialButton = sharing.SocialButton.extend({
        // Subclass of the SocialButton for Twitter Social Buttons.
        'load': function () {
            // Load the widget when called.
            try {
                // mainly lets you show tweet count.
                window.twttr.widgets.load();
            } catch (err) {
                SecondFunnel.vent.trigger('warn', 'Could not load twitter');
            }
            return this;
        }
    });

    sharing.ShareSocialButton = sharing.SocialButton.extend({
        // The "share this" button that opens a "share this" popup
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
        'buttons': SecondFunnel.option('shareSocialButtons'),

        'events': {
            'click .close, .mask': function (ev) {
                this.$el.fadeOut(100).remove();
                this.unbind();  // Removes all callbacks on `this`.
                this.views = [];
            }
        },

        'onRender': function () {
            var self = this;

            this.$el.css({'display': "table"});
            $('body').append(this.$el.fadeIn(100));

            // this.buttons = ["facebook", "twitter", "tumblr", ...]
            if (!(this.buttons && this.buttons.length)) {
                this.buttons = _.map(sources, function (obj, key) {
                    return key;
                });
            }

            _.each(this.buttons, function (button) {
                var share = new sharing.ShareOption(_.extend({
                    'type': button
                }, self.options));
                share.render();

                if (!share.isClosed) {
                    self.$('.share').append(share.$el);
                }
            });

            // process widgets in this view
            SecondFunnel.utils.runWidgets(this);
        }
    });

    sharing.ShareOption = Backbone.Marionette.ItemView.extend({
        // a View for each option within the 'share this' dialogue.
        'tagName': "div",
        'className': "button",
        'templates': [
            '#<%= data.type %>_share_popup_option_template'
        ],
        'template': "#share_popup_option_template",

        'templateHelpers': function () {
            var uri = SecondFunnel.sharing.get(this.options.type),
                helpers = {};
            if (uri) {
                helpers.url = _.template(uri,
                    _.extend({
                        'landing': encodeURIComponent(window.location),
                        'title': document.title
                    }, this.options, this.model.attributes));
            } else {
                helpers.url = window.location;
            }
            helpers.text = _.capitalize(this.options.type);
            return helpers;
        },

        'onRender': function () {
            this.$el.addClass((this.options.type + "_share").replace(/[+\-]/g,
                ""));
            return this;
        }
    });

    sharing.get = function (type) {
        // get source config of a social network type.
        if (typeof type !== 'string') {
            return {};
        }
        type = type.toLowerCase();
        return sources[type];
    };
});