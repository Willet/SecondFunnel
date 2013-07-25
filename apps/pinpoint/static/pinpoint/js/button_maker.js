var Willet = Willet || {};

Willet.buttonMaker = (function (me) {
    "use strict";
    if (!$) {
        Willet.mediator.fire('error', ['Cannot load buttonMaker']);
        return;
    }

    // pages.js makes this
    me.details = {};

    me.init = function (details) {
        me.details = details;
    };

    me.loadFB = function () {
        if (window.FB) {
            window.FB.init({
                cookie: true,
                status: true,
                xfbml: true
            });

            var $featuredFB = $('.featured .social-buttons .button.facebook');

            if ($featuredFB.length > 0) {
                window.FB.XFBML.parse($featuredFB[0]);
            }

            window.FB.Event.subscribe('xfbml.render', function (response) {
                $(".loaded").find(".loading-container").css('visibility', 'visible');
                $(".loaded").find(".loading-container").hide();
                $(".loaded").find(".loading-container").fadeIn('fast');
            });

            window.FB.Event.subscribe('edge.create',
                function (url) {
                    window.Willet.mediator.fire('tracking.registerEvent', [{
                        "network": "Facebook",
                        "type": "share",
                        "subtype": "liked",
                        "label": url
                    }]);
                });
        } else {
            Willet.mediator.fire('error', ['FB button is blocked.']);
        }
    };

    me.createSocialButtons = function (config) {
        var conf           = config || {},
            $socialButtons = $('<div/>', {'class': 'social-buttons'}),
            $fbButton        = $('<div/>', {'class': 'facebook button'}),
            $twitterButton   = $('<div/>', {'class': 'twitter button'}),
            $pinterestButton = $('<div/>', {'class': 'pinterest button'});

        $fbButton.append(me.createFBButton(conf));
        $twitterButton.append(me.createTwitterButton(conf));
        $pinterestButton.append(me.createPinterestButton(conf));

        $socialButtons.append($fbButton).append($twitterButton).append($pinterestButton);
        return $socialButtons;
    };

    me.createFBButton = function (config) {
        var conf = config || {},
            fbxml = "<fb:like " +
                "href='" + (conf.url || '') + "' " +
                "layout='" + (conf.button_count || 'button_count') + "' " +
                "width='" + (conf.width || 80) + "' " +
                "show_faces='" + (conf.show_faces || false) + "' " +
                "></fb:like>";

        return $(fbxml);
    };

    me.createTwitterButton = function (config) {
        var conf = config || {},
            $twitterHtml = $('<a/>', {
                'href'     : 'https://twitter.com/share',
                'class'    : 'twitter-share-button',
                'text'     : 'Tweet',
                'data-url' : conf.url,
                'data-text': (conf.title || '') + ' ' + conf.url,
                'data-lang': 'en'
            });

        if (!config.count) {
            $twitterHtml.attr('data-count', 'none');
        }

        return $twitterHtml;
    };

    me.createPinterestButton = function (config) {
        var conf = config || {},
            url = 'http://pinterest.com/pin/create/button/' +
                '?url=' + encodeURIComponent(conf.url) +
                '&media=' + encodeURIComponent(conf.image) +
                '&description=' + me.details.store.name + '-' + conf.title,

            $img = $('<img/>', {
                'src': "//assets.pinterest.com/images/PinExt.png"
            }),
            $pinterestHtml = $('<a/>', {
                'href': url,
                'target': '_blank'
            });

        $pinterestHtml.append($img);

        return $pinterestHtml;
    };
    
    // add mediator triggers if the module exists.
    if (window.Willet && window.Willet.mediator) {
        var mediator = window.Willet.mediator;
        mediator.on('buttonMaker.init', me.init);
        mediator.on('buttonMaker.loadFB', me.loadFB);
        mediator.on('buttonMaker.createSocialButtons', me.createSocialButtons);
        mediator.on('buttonMaker.createFBButton', me.createFBButton);
        mediator.on('buttonMaker.createTwitterButton', me.createTwitterButton);
        mediator.on('buttonMaker.createPinterestButton', me.createPinterestButton);
    } else {
        window.console && window.console.error && window.console.error(
            'Could not add tracking.js hooks to mediator');
    }

    return me;
}(Willet.buttonMaker || {}));