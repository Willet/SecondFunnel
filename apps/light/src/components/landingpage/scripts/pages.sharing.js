/*global App, console*/
'use strict';

/**
 * This module has no initialization options.
 *
 * @module sharing
 */
module.exports = function (sharing, App, Backhone, Marionette, $, _) {

    var getButton = function (type) {
            // returns 'best' button class based on requested type.
            type = _.capitalize(type);  // e.g. Facebook

            // if we define a custom button class, return that.
            if (sharing[type + 'SocialButton']) {
                return sharing[type + 'SocialButton'];
            }
            // otherwise, return the default.
            return sharing.SocialButton;
        },
        /**
         * A mapping of the different sharing options and the related
         * share url.
         * add more via PAGES_INFO.shareSources.
         *
         * @type {String}
         */
        sources = _.extend({}, {
            // Main ones (e.g. Facebook, Twitter, Tumblr, etc.)
            'facebook': '//facebook.com/sharer/sharer.php?u=<%= url %>',
            'twitter': '//twitter.com/share?url=<%= url %>',
            'tumblr': '//tumblr.com/share/photo?source=<%= url %>&caption=<%= caption %>&click_thru=<%= landing %>',
            'pinterest': '//pinterest.com/pin/create/button/?url=<%= url %>'
        }, App.option('shareSources'));

    /**
     * Container for the social buttons; allows us to create arbitrary
     * social buttons.
     *
     * override the template by passing it in:
     *   `new sharing.SocialButtons({ template: ... })`.
     *
     * Template can be a selector or a function(json) ->  <_.template>
     *
     * @constructor
     * @alias sharing.SocialButtons
     * @type {*}
     */
    this.SocialButtons = Marionette.View.extend({
        'tagName': 'span',
        'showCount': App.option('showCount', true),
        'buttonTypes': App.option('socialButtons',
            ['facebook', 'twitter', 'pinterest']), // @override via constructor

        'loadSocial': _.once(function (callback) {
            $.getScripts([
                '//www.youtube.com/iframe_api',
                '//assets.pinterest.com/js/pinit.js',
                '//platform.twitter.com/widgets.js'
            ], callback);
        }),
        'initSocial': function () {
            // Only initialize the social aspects once; this load the FB script
            // and twitter handlers.
            if (window.FB && _.contains(this.buttonTypes, 'facebook')) {
                window.FB.init({
                    'cookie': true,
                    'status': false, // No AppID
                    'xfbml': true
                });
                App.vent.trigger('tracking:registerFacebookListeners');
            }

            if (window.twttr && window.twttr.widgets &&
                _.contains(this.buttonTypes, 'twitter')) {
                App.vent.trigger('tracking:registerTwitterListeners');
                window.twttr.widgets.load();
            }

            // pinterest does its own stuff - just include pinit.js.
            return this;
        },

        'initialize': function (options) {
            // Initializes the SocialButton View by determining what
            // social buttons to show and loading the initial config if necessary.
            // automatically called when its parent Layout is rendered.
            var self = this;
            // Only load the social once
            this.loadSocial(_.bind(this.initSocial, this));
            this.views = [];  // list of button views (used by marionette)

            self.buttonTypes = options.buttonTypes || self.buttonTypes;

            _.each(_.compact(self.buttonTypes), function (type) {
                var count = options.showCount || true,
                    ButtonClass,
                    template = '#' + type.toLowerCase() + '_social_button_template';
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

    /**
     * Base object for Social buttons.
     * When adding a new Social button, extend from this class and modify
     * as necessary.
     *
     * @constructor
     * @alias sharing.SocialButton
     * @type {ItemView}
     */
    this.SocialButton = Marionette.ItemView.extend({
        'initialize': function (options) {
            // Assign attributes to the object
            _.extend(this, options);
        },

        'load': function () {
            // @override: subclasses should override this method
            return this;
        },

        'templateHelpers': function () {  // or {k: v}
            //github.com/marionettejs/Marionette/blob/master/docs/marionette.view.md#viewtemplatehelpers

            // Template Helpers; add additional data to the data we're serializing to
            // render our template.
            var helpers = {},
                data = this.model.attributes,
                page = App.option('page', {}),
                product = data || page.product || {},
                related = data['tagged-products'] && data['tagged-products'].length ? data['tagged-products'][App.option('galleryIndex', 0)] : {},
                image;

            data.image = data.image ? data.image : {};
            image = page['stl-image'] || page['featured-image'] || data.thumbnail || data.image.url || data.url;

            if (data.source === 'youtube') {
                helpers.url = encodeURIComponent(data['original-url'] || product.url || image);
            } else {
                helpers.url = encodeURIComponent(related.url || product.url || data.url || image);
            }

            helpers.product = {
                'url': related.url, // product.url is the image url, whereas related.url is the product? (jackie)
                'image': image
            };
            helpers.showCount = this.showCount;
            helpers.image = encodeURIComponent(image);

            // Call the after template handler to allow subclasses to modify this
            // data
            return this.onTemplateHelpers ?
                   this.onTemplateHelpers(helpers) :
                   helpers;
        },

        // 'triggers': { 'click .facebook': 'event1 event2' },
        // 'onBeforeRender': $.noop,
        'onRender': function () {
            // Hide this element when it's rendered.
            this.$el = this.$el.children();
            this.setElement(this.$el);
            this.$el.parent().hide();
        },
        'commas': false
    });

    /**
     * Subclass of the SocialButton for FaceBook Social Buttons.
     *
     * @constructor
     * @alias sharing.FacebookSocialButton
     * @type {SocialButton}
     */
    this.FacebookSocialButton = sharing.SocialButton.extend({
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
        },

        'onTemplateHelpers': function (helpers) {
            // Additional attributes to add to our template data.
            var url = (helpers.product.url || helpers.product.image);
            if (url && url.indexOf('facebook') > -1) { // fast lookup
                // regex match it
                var matches = /(?:fbid=|http:\/\/www.facebook.com\/)(\d+)/.exec(url);
                if (matches) { // verify we have a match
                    url = 'http://www.facebook.com/' + matches[1];
                }
            }
            helpers.url = url;
            return helpers;
        }
    });

    /**
     * Subclass of the SocialButton for Twitter Social Buttons.
     *
     * @constructor
     * @alias sharing.TwitterSocialButton
     * @type {SocialButton}
     */
    this.TwitterSocialButton = sharing.SocialButton.extend({
        'load': function () {
            // Load the widget when called.
            try {
                // mainly lets you show tweet count.
                window.twttr.widgets.load();
            } catch (err) {
                console.warn('Could not load twitter');
            }
            return this;
        }
    });

    /**
     * Get source config of a social network type.
     *
     * @param {String} type     the button name.
     * @returns {String}        the url for that button.
     */
    this.get = function (type) {
        if (typeof type !== 'string') {
            return {};
        }
        type = type.toLowerCase();
        return sources[type];
    };
};
