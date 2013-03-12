// TODO: Split into submodules properly
// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth
var PINPOINT = (function($, pageInfo) {
    var console = window.console || {
            // dummy
            'log': function () {},
            'error': function () {}
        },
        details,
        domTemplateCache = {},
        MAX_RESULTS_PER_SCROLL = 50,  // prevent long imagesLoaded
        scripts,
        userClicks = 0,
        clickThreshold = 3,
        spaceBelowFoldToStartLoading = 500,
        loadingBlocks = false,
        blocksAppendedCallbacks = [],
        previewCallbacks = [],
        readyCallbacks = [],
        hoverTimer,
        sizableRegex = /images\.secondfunnel\.com/,
        imageSizes = [
            "icon", "thumb", "small", "compact", "medium", "large",
            "grande", "1024x1024", "master"
        ];

    function size(url, size) {
        var newUrl, filename;

        if (!sizableRegex.test(url)
            || !_.contains(imageSizes, size)) {
            return url;
        }

        // Replace filename with new size
        filename = url.substring(url.lastIndexOf('/')+1)
        newUrl = url.replace(filename, size + '.jpg');

        // NOTE: We do not check if the new image exists because we implicitly
        // trust that our service will contain the required image.
        // ... Also, because it could be expensive to check for the required
        // image before use

        return newUrl;
    }

    /* --- START Utilities --- */
    function getShortestColumn () {
        var $column;
        $('.discovery-area .column').each(function(index, column) {
            var height = $(column).height();

            if (!$column || (height < $column.height())) {
                $column = $(column);
            }
        });
        return $column;
    }

    function fisherYates(myArray, nb_picks) {
        // get #nb_picks random permutations of an array.
        // http://stackoverflow.com/a/2380070
        for (var i = myArray.length - 1; i > 1; i--) {
            var r = Math.floor(Math.random() * i);
            var t = myArray[i];
            myArray[i] = myArray[r];
            myArray[r] = t;
        }

        return myArray.slice(0, nb_picks);
    }

    function renderTemplate(str, data) {
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

        // Append template functions to data
        _.extend(data, {
            'sizeImage': size
        });

        return _.template(replaced, data);
    }

    function renderTemplates(data) {
        // finds templates currently on the page, and drops them onto their
        // targets (elements with classes 'template' and 'target').
        // Targets need a data-src attribute to indicate the template that
        // should be used.
        // data can be passed in, or left as default on the target element
        // as data attributes.


        // select every ".template.target" element and render them with their data-src
        // attribute: data-src='abc' rendered by a data-template-id='abc'
        $('.template.target').each(function () {
            var originalContext = data || {},
                target = $(this),
                src = target.data('src') || '',
                srcElement = $("[data-template-id='" + src + "']"),
                context = {};

            if (src === 'featured') {
                src = details.page['main-block-template'];
                srcElement = $("[data-template-id='" + src + "']")
            }

            // populate context with all available variables
            $.extend(context, originalContext, {
                'page': details.page,
                'store': details.store,
                'data': $.extend({}, srcElement.data(), target.data())
            });

            // if the required template is on the page, use it
            if (srcElement.length) {
                target.html(renderTemplate(srcElement.html(), context));
            } else {
                target.html('Error: required template #' + src +
                    ' does not exist');
            }
        });
    }
    /* --- END Utilities --- */

    /* --- START element bindings --- */
    function showImagePreview(t) {
        showPreview(t, 'image-preview');
    }

    function showProductPreview (t) {
        showPreview(t, 'preview');
    }

    function showPreview(me, templateName) {
        var data     = $(me).data(),
            $preview = $('.preview.container'),
            $mask    = $('.preview .mask'),
            templateEl = $("[data-template-id='" + templateName + "']"),
            template = templateEl.html(),
            renderedTemplate,
            target = $('.target.template[data-src="preview"]');

        data.is_preview = data.is_preview || true;

        if(!templateEl.length || !target.length) {
            console.log('oops @ no preview template');
            return;
        }

        renderedTemplate = renderTemplate(template, {
            'data': data,
            'page': details.page,
            'store': details.store
        });

        target.html(renderedTemplate);

        // Parse Facebook, Twitter buttons
        if (window.FB) {
            FB.XFBML.parse($preview.find('.social-buttons .button.facebook')[0]);
        }

        if (window.twttr) {
            twttr.widgets.load();
        }

        for (var i in previewCallbacks) {
            if (previewCallbacks.hasOwnProperty(i)) {
                previewCallbacks[i]();
            }
        }

        if (window.pinpointTracking) {
            pinpointTracking.clearTimeout();
            pinpointTracking.setSocialShareVars({"sType": "popup", "url": data.url});
        }

        $preview.fadeIn(100);
        $mask.fadeIn(100);
    }

    function addPreviewCallback(f) {
        previewCallbacks.push(f);
    }

    function addOnBlocksAppendedCallback(f) {
        blocksAppendedCallbacks.push(f);
    }

    function addReadyCallback(f) {
        readyCallbacks.push(f);
    }

    function hidePreview () {
        var $mask    = $('.preview .mask'),
            $preview = $('.preview.container');

        window.pinpointTracking && pinpointTracking.setSocialShareVars();

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    }

    function commonHoverOn(t, enableSocialButtons, enableTracking) {
        if (window.pinpointTracking && enableTracking) {
            pinpointTracking.setSocialShareVars({
                "sType": "discovery",
                "url": $(t).data("label")
            });
            pinpointTracking.clearTimeout();
        }

        if (enableTracking) {
            hoverTimer = Date.now();
        }

        if (enableSocialButtons) {
            var $buttons = $(t).find('.social-buttons') || $(t).parent().find('.social-buttons');
            $buttons.fadeIn('fast');

            if ($buttons && !$buttons.hasClass('loaded') && window.FB) {
                FB.XFBML.parse($buttons.find('.button.facebook')[0]);
                $buttons.addClass('loaded');
            }
        }
    }

    function commonHoverOff(t, hoverCallback, enableTracking) {
        var $buttons = $(t).parent().find('.social-buttons');
        $buttons.fadeOut('fast');

        if (enableTracking) {
            hoverTimer = Date.now() - hoverTimer;
            if (hoverTimer > 2000) {
                hoverCallback(t);
            }
        }

        if (window.pinpointTracking && enableTracking) {
            pinpointTracking.clearTimeout();
            if (pinpointTracking.socialShareType !== "popup") {
                pinpointTracking._pptimeout = window.setTimeout(pinpointTracking.setSocialShareVars, 2000);
            }
        }
    }

    function productHoverOn () {
        commonHoverOn(this, true, true);
    }

    function productHoverOff () {
        commonHoverOff(this, function (t) {
            window.pinpointTracking && pinpointTracking.registerEvent({
                "type": "inpage",
                "subtype": "hover",
                "label": $(t).data("label")
            });
        }, true);
    }

    function youtubeHoverOn () {
        commonHoverOn(this, true, false);
    }

    function youtubeHoverOff () {
        commonHoverOff(this, function() {}, false);
    }

    function lifestyleHoverOn () {
        commonHoverOn(this, false, true);
    }

    function lifestyleHoverOff () {
        commonHoverOff(this, function (t) {
            window.pinpointTracking && pinpointTracking.registerEvent({
                "type": "content",
                "subtype": "hover",
                "label": $(t).data("label")
            });
        }, true);
    }

    function updateClickStream(t, event) {
        var $target = $(event.currentTarget),
            data      = $target.data(),
            id        = data['product-id'],
            exceededThreshold;

        if (details.page.offline) {
            return;
        }

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
    }

    function loadInitialResults () {
        if (!loadingBlocks) {
            loadingBlocks = true;
            if (!details.page.offline) {
                $.ajax({
                    url: '/intentrank/get-seeds/',
                    data: {
                        'store': details.store.id,
                        'campaign': details.page.id,
                        'seeds': details.product['product-id']
                    },
                    dataType: 'json',
                    success: function(results) {
                        layoutResults(results);
                    },
                    error: function() {
                        console.log('loading backup results');
                        layoutResults(details.backupResults);
                        loadingBlocks = false;
                    }
                });
            } else {
                layoutResults(details.content);
            }
        }
    }

    function loadMoreResults(belowFold) {
        if (!loadingBlocks) {
            loadingBlocks = true;
            if (!details.page.offline) {
                $.ajax({
                    url: '/intentrank/get-results/',
                    data: {
                        'store': details.store.id,
                        'campaign': details.campaign.id,

                        //TODO: Probably should be some calculated value
                        'results': 10,

                        // normally ignored, unless IR call fails and we'll resort to getseeds
                        'seeds': details.featured.id
                    },
                    dataType: 'json',
                    success: function(results) {
                        layoutResults(results, belowFold);
                    },
                    error: function() {
                        console.log('loading backup results');
                        layoutResults(details.backupResults, belowFold);
                        loadingBlocks = false;
                    }
                });
            } else {
                layoutResults(details.content);
            }
        }
    }

    function invalidateIRSession () {
        $.ajax({
            url: '/intentrank/invalidate-session/',
            dataType: 'json'
        });
    }

    function layoutResults(jsonData, belowFold) {
        // renders product divs onto the page.
        // suppose results is (now) a legit json object:
        // {products: [], videos: [(sizeof 1)]}
        var $block,
            result,
            results = fisherYates(jsonData, MAX_RESULTS_PER_SCROLL) || [],
            initialResults = Math.max(results.length, MAX_RESULTS_PER_SCROLL),
            i,
            productDoms = [],
            template, templateEl, player,
            template_context, templateType, el, videos,
            appearanceProbability;

        // add products
        for (i = 0; i < results.length; i++) {
            try {
                result = results[i]
                template_context = result;
                templateType = result.template || 'product';
                templateEl = $("[data-template-id='" + templateType + "']");
                template = templateEl.html();

                switch (templateType) {
                    case 'product':
                        // in case an image is lacking, don't bother with the product
                        if (!template_context.image || template_context.image == "None") {
                            continue;
                        }

                        // use the resized images
                        template_context.image = template_context.image.replace("master.jpg", "compact.jpg");
                        break;
                    case 'combobox':
                        // in case an image is lacking, don't bother with the product
                        if (!template_context.image || template_context.image == "None") {
                            continue;
                        }
                        break;
                    case 'youtube':
                        break;
                    default:
                        break;
                }

                // attach default prob to the context
                appearanceProbability = template_context['appearance-probability'] ||
                    templateEl.data('appearance-probability') || 1;
                appearanceProbability = parseFloat(appearanceProbability);

                // appearanceProbability dictates if a block that has its own
                // probability of being rendered will be rendered. if specified,
                // the value should go from 0 (not shown at all) or 1 (always).
                if (appearanceProbability < 1) {
                    if (Math.random() < appearanceProbability) {
                        break;  // no luck, not rendering
                    }
                }

                rendered_block = renderTemplate(template, {
                    'data': template_context,
                    'page': details.page,
                    'store': details.store
                });
                if (!rendered_block.length) {
                    // template did not render.
                    break;
                } else {
                    el = $(rendered_block);
                    el.data(template_context);  // populate the .product.block div with data
                    productDoms.push(el[0]);
                }

            } catch (err) {  // hide rendering error
                console.log('oops @ item');
            }
        }

        // Remove potentially bad content
        productDoms = _.filter(productDoms, function(elem) {return !_.isEmpty(elem);});

        $block = $(productDoms);  // an array of DOM elements

        // if it has a lifestyle image, add a wide class to it so it's styled properly
        $block.each(function() {
            var $elem = $(this),
                rand_num = Math.random();
            // hide them so they can't be seen when masonry is placing them
            $elem.hide();

            if ($elem.find('.lifestyle').length > 0) {
                $elem.addClass('wide');
            }

            if ($elem.hasClass('instagram')
                && (rand_num >= 0.5)) {
                $elem.addClass('wide');
            }

            $('.discovery-area').append($elem);
        });

        // Render youtube blocks with player
        videos = _.where(results, {'template': 'youtube'});
        _.each(videos, function(result) {
            var video_state_change = window.pinpointTracking?
                _.partial(pinpointTracking.videoStateChange, result.id):
                function() {/* dummy */};

            api.getObject("video_gdata", result.id, function (video_data) {
                $(".youtube[data-label='" + result.id + "']").children(".title").html(
                    video_data.entry.title.$t
                );
            });

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
                    'onStateChange': video_state_change,
                    'onError': function(e) {}
                }
            });
        });

        // make sure images are loaded or else masonry wont work properly
        $block.imagesLoaded(function($images, $proper, $broken) {
            $broken.parents('.block.product').remove();
            $block.find('.block.product img[src=""]').parents('.block.product').remove();

            $('.discovery-area').masonry('appended', $block, true);
            $block.show();

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
    }

    function pageScroll () {
        var $w            = $(window),
            noResults     = ($('.discovery-area .block').length === 0),
            pageBottomPos = $w.innerHeight() + $w.scrollTop(),
            lowestBlock,
            lowestHeight,
            $divider = $(".divider"),
            divider_bottom = ($divider.length) ? $divider[0].getBoundingClientRect().bottom : 0;

        // user scrolled far enough not to be a "bounce"
        if (divider_bottom < 150) {
            window.pinpointTracking && pinpointTracking.notABounce("scroll");
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

        if (noResults || (pageBottomPos + spaceBelowFoldToStartLoading > lowestHeight)) {
            loadMoreResults();
        }
    }

    function attachListeners () {
        var $discovery = $('.discovery-area');

        // use delegated events to reduce overhead
        $discovery.on('click', '.block.product, .block.combobox', function (e) {
            showProductPreview(e.currentTarget, e);
        });
        $discovery.on('click', '.block.image', function (e) {
            showImagePreview(e.currentTarget, e);
        });

        // update clickstream
        $discovery.on('click', '.block.product, .block.combobox', function (e) {
            updateClickStream(e.currentTarget, e);
        });

        // hovers
        $discovery.on({
            mouseenter: productHoverOn,
            mouseleave: productHoverOff
        }, '.block.product, .block.combobox .product');

        $discovery.on({
            mouseenter: youtubeHoverOn,
            mouseleave: youtubeHoverOff
        }, '.block.youtube');

        $discovery.on({
            mouseenter: lifestyleHoverOn,
            mouseleave: lifestyleHoverOff
        }, '.block.combobox .lifestyle');
    }

    function ready () {
        // Special Setup
        renderTemplates();

        attachListeners();

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
    }
    /* --- END element bindings --- */

    /* --- START Social buttons --- */
    function loadFB () {
        if (FB) {
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
                    window.pinpointTracking && pinpointTracking.registerEvent({
                        "network": "Facebook",
                        "type": "share",
                        "subtype": "liked",
                        "label": url
                    });
                }
            );
        } else {
            (console.error || console.log)('FB button is blocked.');
        }
    }

    function createSocialButtons(config) {
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
    }

    function createFBButton(config) {
        var conf = config || {};

        var fbxml = "<fb:like " +
                "href='" + (conf.url || '') + "' " +
                "layout='" + (conf.button_count || 'button_count') + "' " +
                "width='" + (conf.width || 80) + "' " +
                "show_faces='" + (conf.show_faces || false) + "' " +
            "></fb:like>";

        return $(fbxml);
    }

    function createTwitterButton(config) {
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

    function createPinterestButton(config) {
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
    }
    /* --- END Social buttons --- */

    function load(scripts) {
        var item, script;

        // TODO: Check if already loaded?
        // Use a dictionary, or just check all script tags?
        for (var i=0; i < scripts.length; i++) {
            item = scripts[i];
            $.getScript(item.src || item, item.onload || function() {});
        }
    }

    function init () {
        load(scripts);
        $(document).ready(ready);
    }

    // script actually starts here
    details = pageInfo;
    details.backupResults = details.backupResults || // slightly more customized
                            details.randomResults || // than totally random
                            {};
    details.campaign = details.campaign || {};
    details.content = details.content || [];
    details.featured = details.featured || {};
    details.page = details.page || {};
    details.product = details.page.product || {};
    details.store = details.store || {};

    // Either a URL, or an object with 'src' key and optional 'onload' key
    scripts = [{
        'src'   : 'http://connect.facebook.net/en_US/all.js#xfbml=0',
        'onload': loadFB
    }, {
        'src'   : '//platform.twitter.com/widgets.js',
        'onload': window.pinpointTracking?
                  pinpointTracking.registerTwitterListeners:
                  function () { /* dummy */ },
        'id': 'twitter-wjs'
    }];

    return {
        'init': init,
        'invalidateSession': invalidateIRSession,
        'addPreviewCallback': addPreviewCallback,
        'addOnBlocksAppendedCallback': addOnBlocksAppendedCallback,
        'addReadyCallback': addReadyCallback
    };
})(jQuery, window.PINPOINT_INFO || window.TEST_PAGE_DATA || {});
