// TODO: Split into submodules properly
// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth

// Why do we mix and match jQuery and native dom?
var PINPOINT = (function($){
    var createSocialButtons,
        createFBButton,
        createTwitterButton,
        createPinterestButton,
        featuredAreaSetup,
        hidePreview,
        init,
        load,
        loadFB,
        loadTwitter,
        productHoverOn,
        productHoverOff,
        ready,
        scripts,
        showPreview;

    /* --- START Utilities --- */
    /* --- END Utilities --- */

    /* --- START element bindings --- */
    showPreview = function() {
        var data     = $(this).data(),
            images,
            $element,
            $mask    = $('.preview.mask'),
            $preview = $('.preview.product'),
            $buttons;

        // Fill in data
        $.each(data, function(key, value) {
            $element = $preview.find('.'+key)
            $element.empty();
            switch(key) {
                case 'image':
                    $element.append($('<img/>', {
                        'src': value
                    }))
                    break;
                case 'images':
                    images = value.split('|');
                    $.each(images, function(index, image) {
                        $element.append($('<img/>', {
                            'src': image
                        }))
                    });
                    break;
                default:
                    $element.html(value)
            }
        });

        // Create buttons
        $buttons = createSocialButtons({
            'title': data.title,
            'url'  : data.url,
            'image': data.image
        });
        $preview.find('.social-buttons').replaceWith($buttons);

        // Parse Facebook, Twitter buttons
        FB.XFBML.parse($preview.find('.social-buttons .button.facebook')[0]);
        twttr.widgets.load();

        $preview.fadeIn(100);
        $mask.fadeIn(100);
    };

    hidePreview = function() {
        var $mask    = $('.preview.mask'),
            $preview = $('.preview.product');

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    };

    productHoverOn = function () {
        var $buttons = $(this).find('.social-buttons');
        $buttons.fadeIn('fast');

        if ($buttons && !$buttons.hasClass('loaded') && window.FB) {
            FB.XFBML.parse($buttons.find('.button.facebook')[0]);
            $buttons.addClass('loaded');
        }
    };

    productHoverOff = function () {
        var $buttons = $(this).find('.social-buttons');
        $buttons.fadeOut('fast');
    }

    featuredAreaSetup = function () {
        var $featuredArea = $('.featured'),
            data = $featuredArea.data(),
            url = data['url'],
            title = data['name'],
            fbButton = createFBButton({ 'url': url }),
            twitterButton;

        twitterButton = createTwitterButton({
            'url'  : url,
            'title': title,
            'count': true
        })

        $featuredArea.find('.button.twitter').empty().append(twitterButton);
        $featuredArea.find('.button.facebook').empty().append(fbButton);
        if (window.FB) {
            FB.XFBML.parse($featuredArea.find('.button.facebook')[0]);
        }
        if (window.twttr && window.twttr.widgets) {
            twttr.widgets.load();
        }
    };

    ready = function() {
        // Special Setup
        featuredAreaSetup();

        // Event Handling
        $('.block.product').on('click', showPreview);
        $('.preview .mask, .preview .close').on('click', hidePreview);
        $('.block.product').hover(productHoverOn, productHoverOff);

        // Prevent social buttons from causing other events
        $('.social-buttons .button').on('click', function(e) {
            e.stopPropagation();
        })
    };
    /* --- END element bindings --- */

    /* --- START Social buttons --- */
    loadFB = function () {
        var $featuredFB = $('.featured .social-buttons .button.facebook');

        if ($featuredFB) {
            FB.XFBML.parse($featuredFB[0]);
        }

        FB.Event.subscribe('xfbml.render', function(response) {
            $(".loaded").find(".loading-container").css('visibility', 'visible');
            $(".loaded").find(".loading-container").hide();
            $(".loaded").find(".loading-container").fadeIn('fast');
        });
    };

    loadTwitter = function () {
    };

    createSocialButtons = function (config) {
        var conf           = config || {};
        var $socialButtons = $('<div/>', {'class': 'social-buttons'});

        var $fbButton        = $('<div/>', {'class': 'facebook button'});
        $fbButton.append(createFBButton(conf));

        var $twitterButton   = $('<div/>', {'class': 'twitter button'});
        $twitterButton.append(createTwitterButton(conf));

        var $pinterestButton = $('<div/>', {'class': 'pinterest button'});
        $pinterestButton.append(createPinterestButton(conf));

        $socialButtons.append($fbButton).append($twitterButton).append($pinterestButton);
        return $socialButtons;
    };

    createFBButton = function(config) {
        var conf = config || {};

        var fbxml = "<fb:like " +
                "href='" + (conf.url || '') + "' " +
                "layout='" + (conf.button_count || 'button_count') + "' " +
                "width='" + (conf.width || 80) + "' " +
                "show_faces='" + (conf.show_faces || false) + "' " +
            "></fb:like>";

        return $(fbxml);
    };

    createTwitterButton = function(config) {
        var conf = config || {};

        var $twitterHtml = $('<a/>', {
            'href'     : 'https://twitter.com/share',
            'class'    : 'twitter-share-button',
            'text'     : 'Tweet',
            'data-url' : conf.url,
            'data-text': (conf.title || '') + ' ' + conf.url,
            'data-lang': 'en'
        });

        if (!config.count) {
            $twitterHtml.attr('data-count', 'none')
        }

        return $twitterHtml;
    }

    createPinterestButton = function (config) {
        var conf = config || {};

        var url = 'http://pinterest.com/pin/create/button/' +
            '?url=' + encodeURIComponent(conf.url) +
            '&media=' + encodeURIComponent(conf.image);


        var $img = $('<img/>', {
            'src': "//assets.pinterest.com/images/PinExt.png"
        });

        var $pinterestHtml = $('<a/>', {
            'href': url,
            'target': '_blank'
        });

        $pinterestHtml.append($img);

        return $pinterestHtml;
    };
    /* --- END Social buttons --- */

    /* --- START tracking --- */
    // override existing implementations of methods
    var oldLoadTwitter = loadTwitter;
    loadTwitter = function() {
        oldLoadTwitter();
    }

    var oldLoadFB = loadFB;
    loadFB = function() {
        oldLoadFB();
    }
    /* --- END tracking --- */

    /* --- START Script loading --- */
    // Either a URL, or an object with 'src' key and optional 'onload' key
    scripts = [
        ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js',
    {
        'src'   : 'http://connect.facebook.net/en_US/all.js#xfbml=0',
        'onload': loadFB
    }, {
        'src'   : '//platform.twitter.com/widgets.js',
        'onload': loadTwitter,
        'id': 'twitter-wjs'
    }];

    load = function(scripts) {
        var item, script;

        // TODO: Check if already loaded?
        // Use a dictionary, or just check all script tags?
        for (var i=0; i < scripts.length; i++) {
            item = scripts[i];
            $.getScript(item.src || item, item.onload || function() {});
        }
    };
    /* --- END Script loading --- */

    init = function() {
        var _gaq = window._gaq || (window._gaq = []);

        _gaq.push(['_setAccount', 'UA-35018502-1']);
        _gaq.push(['_trackPageview']);

        load(scripts);
        $(document).ready(ready);
    };

    return {
        'init': init
    };
})(jQuery);

PINPOINT.init();
