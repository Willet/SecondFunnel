// TODO: Split into submodules properly
// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth
var PAGES = (function($, pageInfo) {
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
        globalIdCounters = {},
        previewCallbacks = [],
        readyCallbacks = [],
        hoverTimer,
        sizableRegex = /images\.secondfunnel\.com/,
        imageSizes = [
            "icon", "thumb", "small", "compact", "medium", "large",
            "grande", "1024x1024", "master"
        ],
        templateNames = [
            'shop-the-look', 'featured-product',
            'product', 'combobox', 'youtube', 'image', //formerly instagram
            'product-preview', 'combobox-preview', 'image-preview', 'image-product-preview'
        ],
        imageTypes = [
            'styld-by', 'tumblr', 'pinterest', 'facebook', 'instagram'
        ];

    function getDisplayType() {
        //for now, we cheat to determine which display type to use.
        if ($.browser.mobile) {
            return 'mobile'
        }

        return 'full';
    }

    function setLoadingBlocks(bool) {
        loadingBlocks = bool;
    }

    function getModifiedTemplateName(name) {
        var i, type, preview, previewWithProducts;
        if (_.contains(templateNames, name)) {
            return name;
        }

        for (i = 0; i < imageTypes.length; i++) {
            type = imageTypes[i];
            if (name === type) {
                return 'image';
            }

            preview = type + '-preview';
            if (name === preview) {
                return 'image-preview';
            }

            previewWithProducts = type + '-product-preview';
            if (name === previewWithProducts) {
                return 'image-product-preview';
            }
        }

        return name;
    };

    function redirectToProperTheme() {
        var pathname = window.location.pathname,
            isOnMobilePage = pathname.indexOf("mobile.html", pathname.length - "mobile.html".length) !== -1,
            url = window.location.protocol + '//' + window.location.hostname + window.location.pathname,
            query = window.location.href.split('?')[1] || "";

        if ($.browser.mobile && !isOnMobilePage) {
            url += 'mobile.html' + (query ? '?' + query : "");
            window.location.replace(url);

        } else if (!$.browser.mobile && isOnMobilePage && window.location.hash.indexOf("disableRedirect") === -1) {
            url = url.replace('mobile.html', '') + (query ? '?' + query : "");
            window.location.replace(url);
        }
    }

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
    function checkKeys(testSubject, listOfKeys) {
        /* checks testSubject for required keys OF those sub-objects
         * until the lookup ends.
         *
         * checkKeys(console, ['log', 'abc'])
         * >> Object {log: function}  // because console.log.abc does not exist
         *
         * @type {Object}
         */
        var i = 0,
            keyOf = testSubject,
            refBuilder = {};
        do {
            keyOf = keyOf[listOfKeys[i]];
            if (typeof keyOf === 'undefined') {
                return refBuilder;
            }
            refBuilder[listOfKeys[i]] = keyOf;
        } while (++i < listOfKeys.length);
        return refBuilder;  // all requested key depths exist
    }

    function generateID(baseStr) {
        // multi-baseStr variant of generateID: stackoverflow.com/a/6861381
        globalIdCounters[baseStr] = globalIdCounters[baseStr] + 1 || 0;
        return baseStr + globalIdCounters[baseStr];
    }

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

    function renderTemplate(str, context, isBlock) {
        // MOD of
        // http://emptysquare.net/blog/adding-an-include-tag-to-underscore-js-templates/
        // match "<% include template-id %>" with caching
        var appropriateSize,
            lifestyleSize,
            replaced = str.replace(
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

        // Use 'appropriate' size images by default
        // TODO: Determine appropriate size
        appropriateSize = (isBlock) ? 'compact' : 'master';
        lifestyleSize = (isBlock) ? 'large' : 'master';


        if (_.has(context.data, 'image') && !_.isEmpty(context.data.image)) {
            context.data.image = size(context.data.image, appropriateSize);
        }

        if (_.has(context.data, 'images') && !_.isEmpty(context.data.images)) {
            context.data.images = _.map(context.data.images, function(img) {
                return size(img, appropriateSize)
            });
        }

        if (_.has(context.data, 'lifestyle-image')
            && !_.isEmpty(context.data['lifestyle-image'])) {
            context.data['lifestyle-image'] = size(context.data['lifestyle-image'], lifestyleSize);
        }

        // Append template functions to data
        _.extend(context, {
            'sizeImage': size
        });

        return _.template(replaced, context);
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
                srcElement = $("[data-template-id='" + src + "']");
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

    function changeCategory(category) {
        var categories = details.page.categories;
        if (!categories || !_.findWhere(categories, {'id': ''+category})) {
            return
        }

        // If there are categories, and a valid category is supplied
        // change the category
        details.page.id = category;
        pagesTracking.changeCampaign(category);
    }

    function changeSeed(seed) {
        // If you're calling this function, you probably know what
        // you're doing...

        // Usually called in conjunction with `changeCategory`...

        if (!seed) {
            return;
        }

        details.product['product-id'] = seed;
    }
    /* --- END Utilities --- */

    /* --- START element bindings --- */
    function showPreview(me) {
        var data = $(me).data(),
            templateName = getModifiedTemplateName(data.template),
            $previewContainer = $('[data-template-id="preview-container"]'),
            $previewMask = $previewContainer.find('.mask'),
            $target = $previewContainer.find('.target.template'),
            templateId,
            template, renderedTemplate;

        // Since we don't know how to handle /multiple/ products
        // provide a way to access /one/ related product
        if (_.has(data, 'related-products')
            && !_.isEmpty(data['related-products'])) {
            data['related-product'] = data['related-products'][0];
        }

        if (_.has(data, 'related-products')
            && !_.isEmpty(data['related-products'])) {
            templateName += '-product';
        }

        templateId = templateName + '-preview';

        template = $('[data-template-id="' + templateId + '"]').html();

        if (!template && (templateId.indexOf('image') == 0)) {
            // legacy themes don't have 'image-' templates
            templateId = 'instagram' + templateId.slice(5);
            template = $('[data-template-id="' + templateId + '"]').html();
        }

        if (_.isEmpty(template) || _.isEmpty($target)) {
            console.log('oops @ no preview template');
            return;
        }

        data.is_preview = !_.isUndefined(data.is_preview) ? data.is_preview : true;

        renderedTemplate = renderTemplate(template, {
            'data': data,
            'page': details.page,
            'store': details.store
        });

        $target.html(renderedTemplate);

        // Parse Facebook, Twitter buttons
        if (window.FB) {
            FB.XFBML.parse($previewContainer.find('.social-buttons .button.facebook')[0]);
        }

        if (window.twttr) {
            twttr.widgets.load();
        }

        for (var i in previewCallbacks) {
            if (previewCallbacks.hasOwnProperty(i)) {
                previewCallbacks[i]();
            }
        }

        if (window.pagesTracking) {
            pagesTracking.clearTimeout();
            pagesTracking.setSocialShareVars({"sType": "popup", "url": data.url});
        }

        $previewContainer.fadeIn(100);
        $previewMask.fadeIn(100);
    }

    function addPreviewCallback(f) {
        previewCallbacks.push(f);
    }

    function addOnBlocksAppendedCallback(f) {
        blocksAppendedCallbacks.push(f);
    }

    function setBlocksAppendedCallback(i, $block) {
        if (blocksAppendedCallbacks.hasOwnProperty(i)) {
            blocksAppendedCallbacks[i]($block);
        }
    }

    function addReadyCallback(f) {
        readyCallbacks.push(f);
    }

    function hidePreview () {
        var $mask    = $('.preview .mask'),
            $preview = $('.preview.container');

        window.pagesTracking && pagesTracking.setSocialShareVars();

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    }

    function commonHoverOn(t, enableSocialButtons, enableTracking) {
        if (window.pagesTracking && enableTracking) {
            pagesTracking.setSocialShareVars({
                "sType": "discovery",
                "url": $(t).data("label")
            });
            pagesTracking.clearTimeout();
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

        if (window.pagesTracking && enableTracking) {
            pagesTracking.clearTimeout();
            if (pagesTracking.socialShareType !== "popup") {
                pagesTracking._pptimeout = window.setTimeout(pagesTracking.setSocialShareVars, 2000);
            }
        }
    }

    function productHoverOn () {
        commonHoverOn(this, true, true);
    }

    function productHoverOff () {
        commonHoverOff(this, function (t) {
            window.pagesTracking && pagesTracking.registerEvent({
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
            window.pagesTracking && pagesTracking.registerEvent({
                "type": "content",
                "subtype": "hover",
                "label": $(t).data("label")
            });
        }, true);
    }

    function updateClickStream(t, event) {
        /* Loads more content if user clicks has exceeded threshold.  On each click, loads related content below
           a block that the user has clicked. */
        var $target = $(event.currentTarget),
            data      = $target.data(),
            id        = data['product-id'] || data['id'],
            exceededThreshold;

        if (details.page.offline) {
            return;
        }

        userClicks += 1;
        exceededThreshold = ((userClicks % clickThreshold) == 0);
        
        $.ajax({
            url: PAGES_INFO.base_url + '/intentrank/update-clickstream/?callback=?',
            data: {
                'store': details.store.id,
                'campaign': details.page.id,
                'product_id': id
            },
            dataType: 'jsonp',
            success: function() {
                if (exceededThreshold) {
                    loadMoreResults(true)
                }
            }
        });
    }

    function updateContentStream( product ) {
        /* @return: none */
        loadMoreResults( false, product );
    }

    function layoutRelated( product, relatedContent ) {
        /* Load related content into the masonry instance.
           @return: none */
        var $discovery = $('.discovery-area'),
            $product = $(product),
            initialBottom = $product.position().top + $product.height(),
            $target = $product.next();

        // Find a target that is low enough on screen
        if (($target.position().top) <= initialBottom) {
            $target = $target.next()
        }

        // Inserts content after the clicked product block (Animated)
        relatedContent.insertAfter($target);
        $discovery.masonry('reload');
        relatedContent.show();
        /* // Inserts content after the clicked product block (Non-Animated)
           $.when($discovery.masonry('reload')).then(function(){ relatedContent.show();}); */
    }


    function loadInitialResults (seed) {
        if (!loadingBlocks) {
            changeSeed(seed);

            loadingBlocks = true;
            if (!_.isEmpty(details.backupResults)) {
                layoutResults(details.backupResults);
                details.backupResults = [];
            } else {
                if (!details.page.offline) {
                    $.ajax({
                        url: PAGES_INFO.base_url + '/intentrank/get-seeds/?callback=?',
                        data: {
                            'store': details.store.id,
                            'campaign': details.page.id,
                            'seeds': details.product['product-id']
                        },
                        dataType: 'jsonp',
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
    }

    function loadMoreResults(belowFold, related) {
        if (!loadingBlocks || related) {
            if (!related) {
                loadingBlocks = true;
            }
            if (!details.page.offline) {
                $.ajax({
                    url: PAGES_INFO.base_url + '/intentrank/get-results/?callback=?',
                    data: {
                        'store': details.store.id,
                        'campaign': details.page.id,

                        //TODO: Probably should be some calculated value
                        'results': 10,

                        // normally ignored, unless IR call fails and we'll resort to getseeds
                        'seeds': details.featured.id
                    },
                    dataType: 'jsonp',
                    success: function(results) {
                        layoutResults(results, belowFold, related);
                    },
                    error: function() {
                        console.log('loading backup results');
                        layoutResults(details.backupResults, belowFold, related);
                        if (!related) {
                            loadingBlocks = false;
                        }
                    }
                });
            } else {
                layoutResults(details.content, undefined, related);
            }
        }
    }

    function invalidateIRSession () {
        $.ajax({
            url: PAGES_INFO.base_url + '/intentrank/invalidate-session/?callback=?',
            dataType: 'jsonp'
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
            window.pagesTracking && pagesTracking.notABounce("scroll");
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
            showPreview(e.currentTarget);
        });

        $discovery.on('click', '.block.image', function (e) {
            showPreview(e.currentTarget);
        });

        // update clickstream
        $discovery.on('click', '.block.product, .block.combobox', function (e) {
            updateClickStream(e.currentTarget, e);
        });

        // load related content; update contentstream
        $discovery.on('click', '.block:not(.youtube)', function(e) {
            updateContentStream(e.currentTarget);
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
                    window.pagesTracking && pagesTracking.registerEvent({
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

    function init (readyFunc, layoutFunc) {
        console.log('init');

        // ensure we actually determine if we're desktop or mobile
        // regex from http://detectmobilebrowsers.com/
        (function(a){(jQuery.browser=jQuery.browser||{}).mobile=/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))})(navigator.userAgent||navigator.vendor||window.opera);

        redirectToProperTheme();

        ready = readyFunc;
        layoutResults = layoutFunc;

        load(scripts);
        $(document).ready(ready);
    }

    // script actually starts here
    details = pageInfo;
    details.backupResults = details.backupResults || // slightly more customized
                            details.randomResults || // than totally random
                            {};
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
        'onload': window.pagesTracking?
                  pagesTracking.registerTwitterListeners:
                  function () { /* dummy */ },
        'id': 'twitter-wjs'
    }, {
        'src'   : '//assets.pinterest.com/js/pinit.js',
        'onload': function() { /* dummy */ }
    }];

    return {
        'init': init,
        'invalidateSession': invalidateIRSession,
        'addPreviewCallback': addPreviewCallback,
        'addOnBlocksAppendedCallback': addOnBlocksAppendedCallback,
        'setBlocksAppendedCallback': setBlocksAppendedCallback,
        'blocksAppendedCallbacks': blocksAppendedCallbacks,
        'renderTemplate': renderTemplate,
        'renderTemplates': renderTemplates,
        'loadInitialResults': loadInitialResults,
        'layoutRelated': layoutRelated,
        'attachListeners': attachListeners,
        'hidePreview': hidePreview,
        'pageScroll': pageScroll,
        'MAX_RESULTS_PER_SCROLL': MAX_RESULTS_PER_SCROLL,
        'fisherYates': fisherYates,
        'addReadyCallback': addReadyCallback,
        'changeCategory': changeCategory,
        'checkKeys': checkKeys,
        'generateID': generateID,
        'details': details,
        'setLoadingBlocks': setLoadingBlocks,
        'getModifiedTemplateName': getModifiedTemplateName,
        'changeSeed': changeSeed
    };
})(jQuery, window.PAGES_INFO || window.TEST_PAGE_DATA || {});
