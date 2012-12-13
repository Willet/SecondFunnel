// TODO: Split into submodules properly
// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth

// Why do we mix and match jQuery and native dom?
var PINPOINT = (function($, pageInfo){
    var createSocialButtons,
        createFBButton,
        createTwitterButton,
        createPinterestButton,
        details,
        featuredAreaSetup,
        getShortestColumn,
        hidePreview,
        init,
        invalidateIRSession,
        layoutResults,
        load,
        loadFB,
        loadTwitter,
        loadInitialResults,
        loadMoreResults,
        pageScroll,
        productHoverOn,
        productHoverOff,
        ready,
        scripts,
        showPreview,
        updateClickStream,
        userClicks = 0,
        clickThreshold = 3,
        spaceBelowFoldToStartLoading = 500,
        loadingBlocks = false,
        addOnBlocksAppendedCallback,
        blocksAppendedCallbacks = [],
        addPreviewCallback,
        previewCallbacks = [];

    details = pageInfo;
    details.store    = details.store    || {};
    details.featured = details.featured || {};
    details.campaign = details.campaign || {};

    /* --- START Utilities --- */
    getShortestColumn = function () {
        var $column;

        $('.discovery-area .column').each(function(index, column) {
            var height = $(column).height();

            if (!$column || (height < $column.height())) {
                $column = $(column);
            }
        });

        return $column;
    };
    /* --- END Utilities --- */

    /* --- START element bindings --- */
    showPreview = function() {
        var data     = $(this).data(),
            images,
            $element,
            $mask    = $('.preview .mask'),
            $preview = $('.preview.product'),
            $buttons,
            tag;

        // Fill in data
        $.each(data, function(key, value) {
            $element = $preview.find('.'+key)

            if (!$element.length) {
                // No further work to do
                return;
            }

            tag = $element.prop('tagName').toLowerCase();
            switch(key) {
                case 'url':
                    if (tag === 'a') {
                        $element.prop('href', value);
                    } else {
                        $element.html(value);
                    }
                    break;
                case 'image':
                    $element.empty();
                    $element.append($('<img/>', {
                        'src': value
                    }));
                    break;
                case 'images':
                    $element.empty();
                    images = value.split('|');
                    $.each(images, function(index, image) {
                        var $li = $('<li/>'),
                            $img = $('<img/>', {
                                'src': image
                            }),
                            $appendElem;

                        $appendElem = $img;
                        if (tag === 'ul') {
                            $li.append($img);
                            $appendElem = $li;
                        }
                        $element.append($appendElem);
                    });
                    break;
                default:
                    $element.html(value);
            }
        });

        // Create buttons
        $buttons = createSocialButtons({
            'title': data.title,
            'url'  : data.url,
            'image': data.image,
            'count': true
        });
        $preview.find('.social-buttons').replaceWith($buttons);

        // Parse Facebook, Twitter buttons
        FB.XFBML.parse($preview.find('.social-buttons .button.facebook')[0]);
        twttr.widgets.load();

        for (var i in previewCallbacks) {
            if (previewCallbacks.hasOwnProperty(i)) {
                previewCallbacks[i]();
            }
        }

        $preview.fadeIn(100);
        $mask.fadeIn(100);
    };

    addPreviewCallback = function(f) {
        previewCallbacks.push(f);
    }

    addOnBlocksAppendedCallback = function(f) {
        blocksAppendedCallbacks.push(f);
    }

    hidePreview = function() {
        var $mask    = $('.preview .mask'),
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
    };

    updateClickStream = function (event) {
        var $target = $(event.currentTarget),
            data      = $target.data(),
            id        = data.productId,
            exceededThreshold;

        userClicks += 1;
        exceededThreshold = ((userClicks % clickThreshold) == 0);

        $.ajax({
            url: '/intentrank/update-clickstream/',
            data: {
                'store': details.store.id,
                'campaign': details.campaign.id,
                'product_id': id
            },
            dataType: 'json',
            success: function() {
                if (exceededThreshold) {
                    loadMoreResults(true)
                }
            }
        });
    };

    loadInitialResults = function () {
        if (!loadingBlocks) {
            loadingBlocks = true;
            $.ajax({
                url: '/intentrank/get-seeds/',
                data: {
                    'store': details.store.id,
                    'campaign': details.campaign.id,
                    'seeds': details.featured.id
                },
                dataType: 'json',
                success: function(results) {
                    layoutResults(results);
                },
                failure: function() {
                    loadingBlocks = false;
                }
            });
        }
    };

    loadMoreResults = function(belowFold) {
        if (!loadingBlocks) {
            loadingBlocks = true;
            $.ajax({
                url: '/intentrank/get-results/',
                data: {
                    'store': details.store.id,
                    'campaign': details.campaign.id,
                    'results': 10 //TODO: Probably should be some calculated value
                },
                dataType: 'json',
                success: function(results) {
                    layoutResults(results, belowFold);
                },
                failure: function() {
                    loadingBlocks = false;
                }
            });
        }
    };

    invalidateIRSession = function () {
        $.ajax({
            url: '/intentrank/invalidate-session/',
            dataType: 'json'
        });
    };

    layoutResults = function (results, belowFold) {
        var $col,
            result,
            initialResults = results.length;

        // concatenate all the results together so they're in the same jquery object
        var blocks = "";
        for (var i = 0; i < results.length; i++) {
            blocks += results[i];
        }

        $block = $(blocks);

        // hide them so they can't be seen when masonry is placing them
        $block.css({opacity: 0});

        // if it has a lifestyle image, add a wide class to it so it's styled properly
        $block.each(function() {
            if ($(this).find('.lifestyle').length > 0) {
                $(this).addClass('wide');
            }
        })

        $('.discovery-area').append($block);

        // make sure images are loaded or else masonry wont work properly
        $block.imagesLoaded(function() {
            $('.discovery-area').masonry('appended', $block, true);
            $block.css({opacity: 1});

            // Don't continue to load results if we aren't getting more results
            if (initialResults > 0) {
                setTimeout(function() {pageScroll();}, 100);
            }

            $block.find('.pinpoint-youtube-area').click(function() {
                $(this).html($(this).data('embed'));
            });

            for (var i in blocksAppendedCallbacks) {
                if (blocksAppendedCallbacks.hasOwnProperty(i)) {
                    blocksAppendedCallbacks[i]($block);
                }
            }

            loadingBlocks = false;
        });
    };

    pageScroll = function () {
        var $w            = $(window),
            noResults     = ($('.discovery-area .block').length == 0),
            pageBottomPos = $w.innerHeight() + $w.scrollTop(),
            lowestBlock,
            lowestHeight;

        $('.discovery-area .block').each(function() {
            if (!lowestBlock || lowestBlock.offset().top < $(this).offset().top) {
                lowestBlock = $(this);
            }
        });
       
        if (!lowestBlock) {
            lowestHeight = 0;
        } else {
            lowestHeight = lowestBlock.offset().top + lowestBlock.height()
        }

        if ( noResults || (pageBottomPos + spaceBelowFoldToStartLoading > lowestHeight)) {
            loadMoreResults();
        }
    };

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
        $('.discovery-area').on('click', '.block.product', showPreview);
        $('.discovery-area').on('click', '.block.product', updateClickStream);
        $('.discovery-area').on('mouseenter', '.block.product', productHoverOn);
        $('.discovery-area').on('mouseleave', '.block.product', productHoverOff);

        $('.discovery-area').masonry({
            itemSelector: '.block',
            columnWidth: 960 / 4,
            isResizable: true
        });

        $('.preview .mask, .preview .close').on('click', hidePreview);

        $(window).scroll(pageScroll);
        $(window).resize(pageScroll);

        // Prevent social buttons from causing other events
        $('.social-buttons .button').on('click', function(e) {
            e.stopPropagation();
        });

        // Take any necessary actions
        loadInitialResults();
    };
    /* --- END element bindings --- */

    /* --- START Social buttons --- */
    loadFB = function () {
        FB.init({ 
          cookie:true, 
          status:true,
          xfbml:true
        });

        var $featuredFB = $('.featured .social-buttons .button.facebook');

        if ($featuredFB.length > 0) {
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
        'init': init,
        'invalidateSession': invalidateIRSession,
        'addPreviewCallback': addPreviewCallback,
        'addOnBlocksAppendedCallback': addOnBlocksAppendedCallback
    };
})(jQuery, window.PINPOINT_INFO || {});

PINPOINT.init();
