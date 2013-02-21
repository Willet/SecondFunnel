// TODO: Split into submodules properly
// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth

// Why do we mix and match jQuery and native dom?
var PINPOINT = (function($, pageInfo){
    var addReadyCallback,
        createSocialButtons,
        createFBButton,
        createTwitterButton,
        createPinterestButton,
        details,
        domTemplateCache = {},
        getShortestColumn,
        hidePreview,
        init,
        invalidateIRSession,
        layoutResults,
        load,
        loadFB,
        loadInitialResults,
        loadMoreResults,
        pageScroll,
        commonHoverOn,
        commonHoverOff,
        lifestyleHoverOn,
        lifestyleHoverOff,
        productHoverOn,
        productHoverOff,
        ready,
        renderTemplate,
        renderTemplates,
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
        previewCallbacks = [],
        readyCallbacks = [],
        hoverTimer;

    details = pageInfo;
    details.store    = details.store || {};
    details.page     = details.page  || {};
    details.product  = details.page.product || {};

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
        // display overlay with more information about the selected product
        // data is retrieved from .block.product divs
        var data     = $(this).data(),
            images,
            $element,
            $mask    = $('.preview .mask'),
            $preview = $('.preview.product'),
            $buttons,
            tag;

        // Fill in data
        $.each(data, function(key, value) {
            $element = $preview.find('.'+key).not('.target');

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
                        'src': value.replace("master.jpg", "large.jpg")
                    }));
                    break;
                case 'images':
                    $element.empty();
                    $.each(value, function(index, image) {
                        var $li = $('<li/>'),
                            $img = $('<img/>', {
                                'src': image.replace("master.jpg", "thumb.jpg")
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

        pinpointTracking.clearTimeout();
        pinpointTracking.setSocialShareVars({"sType": "popup", "url": data.url});

        $preview.fadeIn(100);
        $mask.fadeIn(100);
    };

    addPreviewCallback = function(f) {
        previewCallbacks.push(f);
    };

    addOnBlocksAppendedCallback = function(f) {
        blocksAppendedCallbacks.push(f);
    };

    addReadyCallback = function(f) {
        readyCallbacks.push(f);
    };

    hidePreview = function() {
        var $mask    = $('.preview .mask'),
            $preview = $('.preview.product');

        pinpointTracking.setSocialShareVars();

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    };

    commonHoverOn = function (t, enableSocialButtons) {
        pinpointTracking.setSocialShareVars({"sType": "discovery", "url": $(t).parent().data("url")});
        pinpointTracking.clearTimeout();

        if (enableSocialButtons) {
            var $buttons = $(t).parent().find('.social-buttons');
            $buttons.fadeIn('fast');

            hoverTimer = Date.now();

            if ($buttons && !$buttons.hasClass('loaded') && window.FB) {
                FB.XFBML.parse($buttons.find('.button.facebook')[0]);
                $buttons.addClass('loaded');
            }
        }
    };

    commonHoverOff = function (t, hoverCallback) {
        var $buttons = $(t).parent().find('.social-buttons');
        $buttons.fadeOut('fast');

        hoverTimer = Date.now() - hoverTimer;
        if (hoverTimer > 1000) {
            hoverCallback(t);
        }

        pinpointTracking.clearTimeout();
        if (pinpointTracking.socialShareType !== "popup") {
            pinpointTracking._pptimeout = window.setTimeout(pinpointTracking.setSocialShareVars, 2000);
        }
    };

    productHoverOn = function () {
        commonHoverOn(this, true);
    }

    productHoverOff = function () {
        commonHoverOff(this, function (t) {
            pinpointTracking.registerEvent({
                "type": "inpage",
                "subtype": "hover",
                "label": $(t).parent().data("url")
            });
        });
    };

    lifestyleHoverOn = function () {
        commonHoverOn(this, false);
    };

    lifestyleHoverOff = function () {
        commonHoverOff(this, function (t) {
            pinpointTracking.registerEvent({
                "type": "content",
                "subtype": "hover",
                "label": $(t).children().attr("src")
            });
        });
    };

    updateClickStream = function (event) {
        var $target = $(event.currentTarget),
            data      = $target.data(),
            id        = data['product-id'],
            exceededThreshold;

        userClicks += 1;
        exceededThreshold = ((userClicks % clickThreshold) == 0);

        $.ajax({
            url: '/intentrank/update-clickstream/',
            data: {
                'store': details.store.id,
                'campaign': details.page.id,
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

    renderTemplate = function (str, data) {
        // MOD of
        // http://emptysquare.net/blog/adding-an-include-tag-to-underscore-js-templates/
        // match "<% include template-id %>" with caching
        var replaced = str.replace(
            /<%\s*include\s*(.*?)\s*%>/g,
            function(match, templateId) {
                if (domTemplateCache[templateId]) {
                    // cached
                    return domTemplateCache[templateId];
                } else {
                    var $el = $('[data-template-id="' + templateId + '"]');
                    if ($el.length) {
                        // cache
                        domTemplateCache[templateId] = $el.html();
                    }
                    return $el.length ? $el.html() : '';
                }
            }
        );

        return _.template(replaced, data);
    };

    renderTemplates = function (data) {
        // finds templates currently on the page, and drops them onto their
        // targets (elements with classes 'template' and 'target').
        // Targets need a data-src attribute to indicate the template that
        // should be used.
        // data can be passed in, or left as default on the target element
        // as data attributes.
        var excludeTemplates, excludeTemplatesSelector;

        switch (details.page['main-block-template']) {
            case 'shop-the-look':
                excludeTemplates = ['featured-product'];
                break;
            case 'featured-product':
                excludeTemplates = ['shop-the-look'];
                break;
            default:
                excludeTemplates = '';
        }

        $.each(excludeTemplates, function (key, value) {
            excludeTemplates[key] = "[data-src='" + value + "']";
        });
        excludeTemplatesSelector = excludeTemplates.join(', ');

        $('.template.target').not(excludeTemplatesSelector).each(function () {
            var originalContext = data || {},
                target = $(this),
                src = target.data('src') || '',
                srcElement = $("[data-template-id='" + src + "']"),
                context = {};

            $.extend(context, originalContext, {
                'page': details.page,
                'store': details.store,
                'data': target.data() || {}
            });

            // if the required template is on the page, use it
            if (srcElement.length) {
                target.html(renderTemplate(srcElement.html(), context));
            } else {
                target.html('Error: required template #' + src +
                            ' does not exist');
            }
        });

        for (var i in readyCallbacks) {
            if (readyCallbacks.hasOwnProperty(i)) {
                readyCallbacks[i]();
            }
        }
    };

    loadInitialResults = function () {
        if (!loadingBlocks) {
            loadingBlocks = true;
            $.ajax({
                url: '/intentrank/get-seeds/',
                data: {
                    'store': details.store.id,
                    'campaign': details.page.id,
                    'seeds': details.product.id
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
                    'campaign': details.page.id,

                    //TODO: Probably should be some calculated value
                    'results': 10,

                    // normally ignored, unless IR call fails and we'll resort to getseeds
                    'seeds': details.product.id
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

    layoutResults = function (jsonData, belowFold) {
        // renders product divs onto the page.
        // suppose results is (now) a legit json object:
        // {products: [], videos: [(sizeof 1)]}
        var $block,
            result,
            i,
            productDoms = [],
            results = jsonData || [],
            initialResults = results.length,
            template, player,
            template_context, templateType, el, videos;

        // concatenate all the results together so they're in the same jquery object
        for (i = 0; i < results.length; i++) {
            try {
                result = results[i]
                template_context = result;
                templateType = result.template || 'product';
                template = $("[data-template-id='" + templateType + "']").html()

                switch (templateType) {
                    case 'product':
                        // in case an image is lacking, don't bother with the product
                        if (template_context.image == "None") {
                            continue;
                        }

                        // use the resized images
                        template_context.image = template_context.image.replace("master.jpg", "compact.jpg");
                        break;
                    case 'combobox':
                        break;
                    case 'youtube':
                        break;
                    default:
                        break;
                }

                el = $(renderTemplate(template, {
                    'data': template_context,
                    'page': details.page,
                    'store': details.store
                }));
                el.data(template_context);  // populate the .product.block div with data
                productDoms.push(el[0]);
            } catch (err) {
                // hide rendering error
                console && console.log && console.log('oops @ item');
            }
        }

        // Remove potentially bad content
        productDoms = _.filter(productDoms, function(elem) {return !_.isEmpty(elem);});

        $block = $(productDoms);  // an array of DOM elements

        // if it has a lifestyle image, add a wide class to it so it's styled properly
        $block.each(function() {
            var $elem = $(this);
            // hide them so they can't be seen when masonry is placing them
            $elem.css({opacity: 0});

            if ($elem.find('.lifestyle').length > 0) {
                $elem.addClass('wide');
            }
            $('.discovery-area').append($elem[0]);
        });

        // Render youtube blocks with player
        videos = _.where(results, {'template': 'youtube'});
        _.each(videos, function(result) {
            player = new YT.Player(result.id, {
                height: result.height,
                width: result.width,
                videoId: result.id,
                playerVars: {
                    'autoplay': result.autoplay,
                    'controls': 0
                },
                events: {
                    'onReady': function(e) {},
                    'onStateChange': pinpointTracking.videoStateChange,
                    'onError': function(e) {}
                }
            });
        });

        // make sure images are loaded or else masonry wont work properly
        $block.imagesLoaded(function($images, $proper, $broken) {
            $broken.parents('.block.product').remove();
            $block.find('.block.product img[src=""]').parents('.block.product').remove();

            $('.discovery-area').masonry('appended', $block, true);
            $block.css({opacity: 1});

            // Don't continue to load results if we aren't getting more results
            if (initialResults > 0) {
                setTimeout(function() {
                    pageScroll();
                }, 100);
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
            noResults     = ($('.discovery-area .block').length === 0),
            pageBottomPos = $w.innerHeight() + $w.scrollTop(),
            lowestBlock,
            lowestHeight,
            $divider = $(".divider"),
            divider_bottom = ($divider.length) ? $divider[0].getBoundingClientRect().bottom : 0;

        // user scrolled far enough not to be a "bounce"
        if (divider_bottom < 150) {
            pinpointTracking.notABounce("scroll");
        }

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

    ready = function() {
        // Special Setup
        renderTemplates();

        // Event Handling
        // when someone clicks on a product, show the product details overlay
        $('.discovery-area').on('click', '.block.product', showPreview);

        // and update the clickstream
        $('.discovery-area').on('click', '.block.product', updateClickStream);

        $('.discovery-area').on('mouseenter', '.block.product .product', productHoverOn);
        $('.discovery-area').on('mouseleave', '.block.product .product', productHoverOff);

        $('.discovery-area').on('mouseenter', '.block.product .lifestyle', lifestyleHoverOn);
        $('.discovery-area').on('mouseleave', '.block.product .lifestyle', lifestyleHoverOff);

        $('.discovery-area').masonry({
            itemSelector: '.block',

            columnWidth: function (containerWidth) {
                return containerWidth / 4;
            },

            isResizable: true,
            isAnimated: true
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

        FB.Event.subscribe('edge.create',
            function(url) {
                pinpointTracking.registerEvent({
                    "network": "Facebook",
                    "type": "share",
                    "subtype": "liked",
                    "label": url
                });
            }
        );
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
    };

    createPinterestButton = function (config) {
        var conf = config || {};

        var url = 'http://pinterest.com/pin/create/button/' +
            '?url=' + encodeURIComponent(conf.url) +
            '&media=' + encodeURIComponent(conf.image) +
            '&description=' + details.store.name + '-' + conf.title;

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

    /* --- START Script loading --- */
    // Either a URL, or an object with 'src' key and optional 'onload' key
    scripts = [
    {
        'src'   : 'http://connect.facebook.net/en_US/all.js#xfbml=0',
        'onload': loadFB
    }, {
        'src'   : '//platform.twitter.com/widgets.js',
        'onload': pinpointTracking.registerTwitterListeners,
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
        load(scripts);
        $(document).ready(ready);
    };

    return {
        'init': init,
        'invalidateSession': invalidateIRSession,
        'addPreviewCallback': addPreviewCallback,
        'addOnBlocksAppendedCallback': addOnBlocksAppendedCallback,
        'addReadyCallback': addReadyCallback
    };
})(jQuery, window.PINPOINT_INFO || {});
