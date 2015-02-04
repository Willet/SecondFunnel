/**
 *  GAP PAGE
 **/
"use strict";

var $ = require('jquery');
var _ = require('underscore');
var waypoints = require("jquery-waypoints") // register $.fn.waypoint

var Page = require('landingpage'),
    App = Page.App;

// Import client customizations
App.module('utils', require('./utils'));
App.module('core', require('./core.views'));

// Run Application
App.init.initialize();

App.start();

// GAP Google Analytics
(function initGapAnalytics () {
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
        // mobile
        App.options.urlParams.tid = "gpem000067";
        App.options.clickUrl = "http://ad.doubleclick.net/ddm/clk/288205600;115211941;r?"
    } else {
        // desktop
        App.options.urlParams.tid = "gpem000066";
        App.options.clickUrl = "http://ad.doubleclick.net/ddm/clk/288199394;115211941;n?"
    }

    // Shorthand for pushing data to Google Analytics
    var productName = null,
        recordEvent = function (event, eventCategory, eventAction, eventLabel) {
            dataLayer.push({
                'event': event,
                'eventCategory': eventCategory,
                'eventAction': eventAction,
                'eventLabel': eventLabel
            });

            // for our internal analytics: also track these events.
            // tracking page_scroll causes infinite loops.
            if (event !== 'page_scroll' &&
                window.App &&
                window.App.vent &&
                window.App.vent.trigger &&
                typeof window.App.vent.trigger === 'function') {
              App.vent.trigger('tracking:trackEvent', {
                  'category': eventCategory,
                  'action': eventAction,
                  'label': eventLabel,
                  'value': event
              });
            }
        };

    window._pq = window._pq || [];

    // Tracking Code for GAP's Google Analytics
    window.GAP_ANALYTICS = new App.tracker.EventManager({
        // 1 - Top Nav
        'click a.navbar-brand, .other-brands.dropdown a:not(.dropdown-toggle)': function () {
            var dataBrand = $(this).data('brand');
            var brand = "(Unknown)";
            if (dataBrand && $.trim(dataBrand).length > 0) {
                brand = dataBrand;
            } else {
                var textBrand = $.trim($(this).text().toLowerCase());
                if (textBrand.length > 0 ) {
                    brand = textBrand;
                }
            }

            recordEvent('gap_nav', 'nav', 'exit', 'nav - ' + brand);
        },
        // 2 - Header Logo
        'click header > a': function () {
            recordEvent('header_logo', 'header', 'exit', 'gap.com');
        },
        // 3 - Social Subscribe Links
        'click .nav.navbar-nav.navbar-right a, .stay-connected .dropdown-menu a': function () {
            var social_network = /(?:(\w+?)\.com)/.exec($(this).attr('href'))[1];
            recordEvent('social_follow', 'follow', social_network + ' follow', 'follow');
        },
        // 4 - Main Visual
        'click #hero-area .jumbotron': function () {
            recordEvent('main_visual', 'main visual', 'visual click', 'visual click');
        },
        // 5 - Feed Visuals
        'click .tile.product': function () {
            productName = App.discovery.collection.get($(this).attr('id')).get('name');
            recordEvent('product_feed', 'product_feed', 'pop-up open', productName);
        },
        // 6 - Product Social Links
        'click .content-wrapper .social-buttons .button': function () {
            var social_network = $(this).attr('class').replace(/\s*button\s*/, '');
            recordEvent('product_share', 'product pop-up', social_network + ' share', productName);
        },
        // 7 - Find Product in Store
        'click .content-wrapper a.button.find-store': function () {
            recordEvent('product_find in store', 'product pop-up', 'find in store', productName);

            try {
                _pq.push(['track', 'FindInStore']);
            } catch(err) {}

            try {
                __adroll.record_user({"adroll_segments": 'FindInStore'});
            } catch(err) {}

        },
        // 8 - Buy Product Online
        'click .content-wrapper a.button.in-store': function () {
            recordEvent('product_buy online', 'product pop-up', 'buy online', productName);

            try {
                _pq.push(['track', 'ShopOnGap']);
            } catch(err) {}

            try {
                __adroll.record_user({"adroll_segments": 'ShopOnGap'});
            } catch(err) {}

        },
        // 10 - Share deal
        'click #hero-area .buttons a': function () {
            var social_network = /(?:(\w+?)\.com)/.exec($(this).attr('href'))[1];
            recordEvent('deal_share', 'header', social_network + ' share', 'share page');
        },
        // 13 - Lifestyle Feed Visuals
        'click .tile.image': function () {
            var cid = $(this).attr('id'),
                obj = App.discovery.collection.get(cid),
                products = obj.get('tagged-products');
            if (products && products.length > 0) {
                productName = products[0].name;
                recordEvent('lifestyle_feed', 'lifestyle feed', 'pop-up open', productName);
            } else {
                productName = null;
            }
        },
        // 14 - Lifestyle Product Social Links
        'click .image-with-tagged-products .social-buttons .button, .image-without-tagged-products .social-buttons .button': function () {
            if (productName) {
                var social_network = $(this).attr('class').replace(/\s*button\s*/, '');
                recordEvent('lifestyle_share', 'lifestyle pop-up', social_network + ' share', productName);
            }
        },
        // 15 - Find Lifestyle Product in Store
        'click .image-with-tagged-products a.button.find-store, .image-without-tagged-products a.button.find-store': function () {
            if (productName) {
                recordEvent('lifestyle_find in store', 'lifestyle pop-up', 'find in store', productName);
            }
        },
        // 16 - Buy Lifestyle Product Online
        'click .image-with-tagged-products a.button.in-store, .image-without-tagged-products a.button.in-store \
            .image-with-tagged-products a.buy, .image-without-tagged-products a.buy': function () {
            if (productName) {
                recordEvent('lifestyle_buy online', 'lifestyle pop-up', 'buy online', productName);
            }
        },
        // 17 - Lifestyle Feed Video
        'click .tile.youtube.wide': function () {
            var cid = $(this).attr('id'),
                obj = App.discovery.collection.get(cid),
                products = obj.get('tagged-products');
            if (products && products.length > 0) {
                recordEvent('lifestyle_video', 'lifestyle_feed', 'video play', products[0].name);
            }
        },
        // 18 - Lifestyle Feed Video
        'click #hero-area .overlay .find a': function() {
            recordEvent('find_store', 'main visual', 'store locator', 'find a store');
        },
        // Perfect Audience
        'click .tile.image, .tile.product': function() {
            var cid = $(this).attr('id'),
                obj = App.discovery.collection.get(cid),
                product, pageId, storeSlug, feedId,
                segment, analyticsTile, analyticsProduct, related,
                analyticsPage, tileId;

            tileId = obj.get('tile-id');
            pageId = App.options.page.id;
            storeSlug = App.options.store.slug;

            // Needs to match the RSS
            feedId = storeSlug + 'P' + pageId + 'T' + tileId;

            if ($(this).hasClass('image')) {
                segment = 'ImagePopUp';
            } else if ($(this).hasClass('product')) {
                segment = 'ProductPopUp';
            }

            try {
                _pq.push(['track', segment]);
                _pq.push(['track', 'PopUp']);
                _pq.push(['trackProduct', feedId]);
            } catch(err) {}

            try {
                __adroll.record_user({"adroll_segments": segment});
                __adroll.record_user({"adroll_segments": 'PopUp'});
                __adroll.record_user({"product_id": feedId});
            } catch(err) {}
        }
    });

    // Scroll event has to be seperately tracked.
    // 12 - Scroll for more
    var pagesScrolled = 1;
    App.vent.on('tracking:trackEvent', function (o) {
        if (o.action === 'scroll') {
            recordEvent('page_scroll', 'scroll', 'page_scroll', 'scroll - ' + o.label);
        }
    });

    // Subscribe to FB event for GAP Analytic tracking
    App.vent.on('tracking:registerFacebookListeners', function () {
        FB.Event.subscribe('edge.create', function(href, widget) {
            var type = $('div.facebook').eq(0).parents('.image-with-tagged-products, .image-without-tagged-products');
            if (productName && type && type.length > 0) {
                recordEvent('lifestyle_share', 'lifestyle pop-up', 'facebook share', productName);
            } else if (productName) {
                recordEvent('product_share', 'product pop-up', 'facebook share', productName);
            }
        });
    });

    App.vent.on({
        // 19 - video play
        'tracking:videoPlay': function (videoId) {
            recordEvent('video_play', 'video', 'video play', videoId);
        },
        // 20 - video complete
        'tracking:videoFinish': function (videoId) {
            recordEvent('video_complete', 'video', 'video complete', videoId);
        },
        // 21 - choose a video
        'tracking:videoClick': function (videoId) {
            recordEvent('video_choose', 'video', 'choose a video', videoId);
        }
    });
}());
