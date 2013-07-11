// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth
var PAGES = (function ($, details, mediator) {
    "use strict";
    var i = 0,  // counter
        noop = function () {},
        domTemplateCache = {},
        MAX_RESULTS_PER_SCROLL = 50,  // prevent long imagesLoaded
        SHUFFLE_RESULTS = details.page.SHUFFLE_RESULTS || true,
        scripts,
        scriptsLoaded = [],
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
        layoutResults;

    function getLoadingBlocks(bool) {
        return loadingBlocks;
    }

    function setLoadingBlocks(bool) {
        loadingBlocks = bool;
    }

    function getModifiedTemplateName(name) {
        // returns the template name suitabl
        var i,
            type,
            templateNames = [
                'shop-the-look', 'featured-product',
                'product', 'combobox', 'youtube', 'image', //formerly instagram
                'product-preview', 'combobox-preview', 'image-preview',
                'image-product-preview'
            ],
            imageTypes = [
                // templates of these names will all use the "image" template.
                'styld-by', 'tumblr', 'pinterest', 'facebook', 'instagram'
            ];

        if (_.contains(templateNames, name)) {
            return name;
        }

        for (i = 0; i < imageTypes.length; i++) {
            type = imageTypes[i];
            switch (name) {
            case type:
                return 'image';
            case type + '-preview':
                return 'image-preview';
            case type + '-product-preview':
                return 'image-product-preview';
            default:
                // move on
            }
        }

        return name;
    }

    function size(url, desiredSize) {
        // NOTE: We do not check if the new image exists because we implicitly
        // trust that our service will contain the required image.
        // ... Also, because it could be expensive to check for the required
        // image before use
        var newUrl, filename;

        if (!sizableRegex.test(url) || !_.contains(imageSizes, desiredSize)) {
            return url;
        }

        // Replace filename with new size
        filename = url.substring(url.lastIndexOf('/') + 1);
        newUrl = url.replace(filename, desiredSize + '.jpg');

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
            try {
                keyOf = keyOf[listOfKeys[i]];
                if (keyOf === 'undefined') {
                    return refBuilder;
                }
            } catch (err) {
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

    function fisherYates(myArray, nb_picks) {
        // get #nb_picks random permutations of an array.
        // http://stackoverflow.com/a/2380070
        var i;
        for (i = myArray.length - 1; i > 1; i--) {
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
                function (match, templateId) {
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
        appropriateSize = isBlock ? 'compact' : 'master';
        lifestyleSize = isBlock ? 'large' : 'master';


        // _.isEmpty does its own _.has check.
        if (!_.isEmpty(context.data.image)) {
            context.data.image = size(context.data.image, appropriateSize);
        }

        if (!_.isEmpty(context.data.images)) {
            context.data.images = _.map(context.data.images, function (img) {
                return size(img, appropriateSize);
            });
        }

        if (!_.isEmpty(context.data['lifestyle-image'])) {
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
                srcElement,
                context = {};

            if (src === 'featured') {
                // this is supposed to make things easier for designers
                src = details.page['main-block-template'];
            }

            // if the required template is on the page, use it
            srcElement = $("[data-template-id='" + src + "']");
            if (srcElement.length) {
                // populate context with all available variables
                $.extend(context, originalContext, {
                    'page': details.page,
                    'store': details.store,
                    'data': $.extend({}, srcElement.data(), target.data())
                });

                target.html(renderTemplate(srcElement.html(), context));
            } else {
                target.html('Error: missing template #' + src);
            }
        });
    }
    /* --- END Utilities --- */

    /* --- START element bindings --- */
    function showPreview(me) {
        var i,
            data = $(me).data(),
            templateName = getModifiedTemplateName(data.template),
            $previewContainer = $('[data-template-id="preview-container"]'),
            $previewMask = $previewContainer.find('.mask'),
            $target = $previewContainer.find('.target.template'),
            templateId,
            template,
            renderedTemplate;

        // Since we don't know how to handle /multiple/ products
        // provide a way to access /one/ related product
        if (!_.isEmpty(data['related-products'])) {
            data['related-product'] = data['related-products'][0];
            templateName += '-product';
        }

        templateId = templateName + '-preview';

        template = $('[data-template-id="' + templateId + '"]').html();

        if (!template && (templateId.indexOf('image') === 0)) {
            // legacy themes don't have 'image-' templates
            templateId = 'instagram' + templateId.slice(5);
            template = $('[data-template-id="' + templateId + '"]').html();
        }

        if (_.isEmpty(template) || _.isEmpty($target)) {
            mediator.fire('log', ['oops @ no preview template']);
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
            window.FB.XFBML.parse($previewContainer.find('.social-buttons .button.facebook')[0]);
        }

        if (window.twttr) {
            window.twttr.widgets.load();
        }

        for (i in previewCallbacks) {
            if (previewCallbacks.hasOwnProperty(i)) {
                previewCallbacks[i]();
            }
        }

        mediator.fire('tracking.clearTimeout');
        mediator.fire('tracking.setSocialShareVars', [
            {"sType": "popup", "url": data.url}
        ]);

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

        mediator.fire('tracking.setSocialShareVars', []);

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    }

    function commonHoverOn(t, enableSocialButtons, enableTracking) {
        if (enableTracking) {
            mediator.fire('tracking.setSocialShareVars', [{
                "sType": "discovery",
                "url": $(t).data("label")
            }]);
            mediator.fire('tracking.clearTimeout');
        }

        if (enableTracking) {
            hoverTimer = Date.now();
        }

        if (enableSocialButtons) {
            var $buttons = $(t).find('.social-buttons') || $(t).parent().find('.social-buttons');
            $buttons.fadeIn('fast');

            if ($buttons && !$buttons.hasClass('loaded') && window.FB) {
                window.FB.XFBML.parse($buttons.find('.button.facebook')[0]);
                $buttons.addClass('loaded');
            }
        }
    }

    function commonHoverOff(t, hoverCallback, enableTracking) {
        var $buttons = $(t).parent().find('.social-buttons');
        $buttons.fadeOut('fast');

        if (!enableTracking) {
            return;
        }
        hoverTimer = Date.now() - hoverTimer;
        if (hoverTimer > 2000) {
            hoverCallback(t);
        }

        mediator.fire('tracking.clearTimeout');
        if (window.pagesTracking) {
            if (pagesTracking.socialShareType !== "popup") {
                pagesTracking._pptimeout = window.setTimeout(pagesTracking.setSocialShareVars, 2000);
            }
        } else {
            mediator.fire('error', ['cannot find pagesTracking']);
        }
    }

    function productHoverOn() {
        commonHoverOn(this, true, true);
    }

    function productHoverOff() {
        commonHoverOff(this, function (t) {
            mediator.fire('tracking.registerEvent', [{
                "type": "inpage",
                "subtype": "hover",
                "label": $(t).data("label")
            }]);
        }, true);
    }

    function youtubeHoverOn() {
        commonHoverOn(this, true, false);
    }

    function youtubeHoverOff() {
        commonHoverOff(this, noop, false);
    }

    function lifestyleHoverOn() {
        commonHoverOn(this, false, true);
    }

    function lifestyleHoverOff() {
        commonHoverOff(this, function (t) {
            mediator.fire('tracking.registerEvent', [{
                "type": "content",
                "subtype": "hover",
                "label": $(t).data("label")
            }]);
        }, true);
    }

    function loadInitialResults(seed) {
        mediator.fire('IR.changeSeed', [seed]);
        mediator.fire('IR.getInitialResults', [layoutResults]);
    }

    function loadMoreResults(callback, belowFold, related) {
        callback = callback || layoutResults;
        if (!loadingBlocks || related) {
            mediator.fire('IR.getMoreResults', [callback, belowFold, related]);
        }
    }

    function layoutRelated(product, relatedContent) {
        /* Load related content into the masonry instance.
           @return: none */
        var $discovery = $('.discovery-area'),
            $product = $(product),
            initialBottom = $product.position().top + $product.height(),
            $target = $product.next();

        // Find a target that is low enough on screen
        // TODO: can $target.next() also be above initialBottom?
        if (($target.position().top) <= initialBottom) {
            $target = $target.next();
        }

        // Inserts content after the clicked product block (Animated)
        relatedContent.insertAfter($target);
        $discovery.masonry('reload');
        relatedContent.show();
        /* // Inserts content after the clicked product block (Non-Animated)
           $.when($discovery.masonry('reload')).then(function(){ relatedContent.show();}); */
    }

    function pageScroll() {
        // calculates screen location and decide if more results
        // should be displayed.
        var $w            = $(window),
            discoveryBlocks = $('.discovery-area .block'),
            noResults     = (discoveryBlocks.length === 0),
            pageBottomPos = $w.innerHeight() + $w.scrollTop(),
            lowestBlock,
            lowestHeight,
            $divider = $(".divider"),
            divider_bottom = ($divider.length) ? $divider[0].getBoundingClientRect().bottom : 0;

        // user scrolled far enough not to be a "bounce"
        if (divider_bottom < 150) {  // arbitrary
            mediator.fire('tracking.notABounce', ["scroll"]);
        }

        discoveryBlocks.each(function() {
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
            loadMoreResults(layoutResults);
        }
    }

    function attachListeners() {
        var $discovery = $('.discovery-area');

        // use delegated events to reduce overhead
        $discovery.on('click', '.block.product:not(.unclickable), .block.combobox:not(.unclickable)', function (e) {
            showPreview(e.currentTarget);

            // update clickstream
            mediator.fire('IR.updateClickStream', [e.currentTarget, e]);
        });

        $discovery.on('click', '.block.image:not(.unclickable)', function (e) {
            showPreview(e.currentTarget);
        });

        // load related content; update contentstream
        $discovery.on('click', '.block:not(.youtube):not(.unclickable)', function(e) {
            mediator.fire('IR.updateContentStream', [e.currentTarget]);
        });

        // hovers
        $discovery.on({
            mouseenter: productHoverOn,
            mouseleave: productHoverOff
        }, '.block.product:not(.unclickable), .block.combobox:not(.unclickable) .product');

        $discovery.on({
            mouseenter: youtubeHoverOn,
            mouseleave: youtubeHoverOff
        }, '.block.youtube');

        $discovery.on({
            mouseenter: lifestyleHoverOn,
            mouseleave: lifestyleHoverOff
        }, '.block.combobox:not(.unclickable) .lifestyle');
    }

    /* --- END element bindings --- */

    function load(scripts) {
        var i, item, script;

        // Use a dictionary, or just check all script tags?
        for (i = 0; i < scripts.length; i++) {
            item = scripts[i];
            if (_.contains(scriptsLoaded, item.src)) {
                mediator.fire(
                    'log',
                    ['script ' + item.src + ' already loaded; skipping.']
                );
            } else {
                $.getScript(item.src || item, item.onload || noop);
                scriptsLoaded.push(item.src);
            }
        }
    }

    function init(readyFunc, layoutFunc) {
        layoutResults = layoutFunc;
        load(scripts);
        $(document).ready(readyFunc);
    }

    // script actually starts here
    var requiredInfo = [
        'backupResults', 'featured', 'page', 'product', 'store'
    ];
    for (i = 0; i < requiredInfo.length; i++) {
        details[requiredInfo[i]] = details[requiredInfo[i]] || {};
    }
    details.content = details.content || [];

    mediator.fire('buttonMaker.init', [details]);

    // Either a URL, or an object with 'src' key and optional 'onload' key
    scripts = [{
        'src'   : 'http://connect.facebook.net/en_US/all.js#xfbml=0',
        'onload': mediator.callback('buttonMaker.loadFB')
    }, {
        'src'   : '//platform.twitter.com/widgets.js',
        'onload': mediator.callback('tracking.registerTwitterListeners'),
        'id': 'twitter-wjs'
    }, {
        'src'   : '//assets.pinterest.com/js/pinit.js',
        'onload': noop
    }];

    return {
        'init': init,
        'addPreviewCallback': addPreviewCallback,
        'addOnBlocksAppendedCallback': addOnBlocksAppendedCallback,
        'setBlocksAppendedCallback': setBlocksAppendedCallback,
        'blocksAppendedCallbacks': blocksAppendedCallbacks,
        'renderTemplate': renderTemplate,
        'renderTemplates': renderTemplates,
        'loadInitialResults': loadInitialResults,
        'loadMoreResults': loadMoreResults,
        'layoutRelated': layoutRelated,
        'attachListeners': attachListeners,
        'hidePreview': hidePreview,
        'pageScroll': pageScroll,
        'MAX_RESULTS_PER_SCROLL': MAX_RESULTS_PER_SCROLL,
        'SHUFFLE_RESULTS': SHUFFLE_RESULTS,
        'fisherYates': fisherYates,
        'addReadyCallback': addReadyCallback,
        'checkKeys': checkKeys,
        'generateID': generateID,
        'details': details,
        'getLoadingBlocks': getLoadingBlocks,
        'setLoadingBlocks': setLoadingBlocks,
        'getModifiedTemplateName': getModifiedTemplateName
    };
}(jQuery,
    window.PAGES_INFO || window.TEST_PAGE_DATA || {},
    (Willet && Willet.mediator) || {}));


// full (desktop) component
PAGES.full = (function (me, mediator) {
    "use strict";

    me = {
        'layoutFunc': function (jsonData, belowFold, related) {
            // renders product divs onto the page.
            // suppose results is (now) a legit json object:
            // {products: [], videos: [(sizeof 1)]}
            try {
                if (jsonData.error) {
                    mediator.fire(
                        'error',  // usually "Campaign xxx has no product for id xxx"
                        [jsonData.error + ' (' + (jsonData.url || '') + ')']
                    );
                    return;
                }
            } catch (err) {
                /* neither an array nor object - even worse */
                mediator.fire('error', ['malformed jsonData', jsonData]);
                return;
            }
            if (!jsonData.length) {
                mediator.fire('error', ['IR returned zero results!']);
                return;
            }

            var $block,
                result,
                results = (PAGES.SHUFFLE_RESULTS) ?
                        (PAGES.fisherYates(jsonData, PAGES.MAX_RESULTS_PER_SCROLL) || []) :
                        $(jsonData).slice(0, PAGES.MAX_RESULTS_PER_SCROLL),  // no shuffle
                initialResults = Math.max(results.length, PAGES.MAX_RESULTS_PER_SCROLL),
                i,
                j,
                productDoms = [],
                template,
                templateEl,
                player,
                template_context,
                templateType,
                el,
                videos,
                revisedType;

            // add products
            for (i = 0; i < results.length; i++) {
                try {
                    result = results[i];
                    template_context = result;
                    templateType = PAGES.getModifiedTemplateName(result.template) || 'product';
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
                    case 'image':
                        if (!template) {
                            // Legacy themes do not support these templates
                            revisedType = 'instagram';
                            templateEl = $("[data-template-id='" + revisedType + "']");
                            template = templateEl.html();
                        }
                        break;
                    default:
                        break;
                    }

                    var rendered_block = PAGES.renderTemplate(template, {
                        'data': template_context,
                        'page': PAGES.details.page,
                        'store': PAGES.details.store
                    }, true);
                    if (!rendered_block.length) {
                        mediator.fire('error', ['warning: not drawing empty template block']);
                        break;
                    } else {
                        el = $(rendered_block);
                        el.data(template_context);  // populate the .product.block div with data

                        var templateElsLength = el.length;
                        for (j=0; j<templateElsLength; j++) {
                            // didn't have a better name for a loop
                            productDoms.push(el[j]);
                        }
                    }

                } catch (err) {  // hide rendering error
                    mediator.fire('log', ['oops @ item', err]);
                }
            }

            // Remove potentially bad content
            productDoms = _.filter(productDoms, function (elem) {
                return !_.isEmpty(elem);
            });

            $block = $(productDoms);  // an array of DOM elements

            // if it has a lifestyle image, add a wide class to it so it's styled properly
            $block.each(function () {
                var $elem = $(this),
                    $images = $elem.find('img'),

                    // Create a spinner image that can be used to indicate a block is loading.
                    $spinner = $('<img/>', {
                        'class': "image-loading-spinner",
                        'style': "padding-top:100px; padding-bottom:100px; width:32px !important; height:32px; position:relative; left:50%;",
                        'src': "https://s3.amazonaws.com/elasticbeanstalk-us-east-1-056265713214/images/ajax-spinner.gif"
                    });

                $elem.toLoad = $images.length;

                // If there's images to be loaded, place a spinner in the block and load the content
                // in the background.
                if (!related && $elem.toLoad > 0) {
                    // If the block actually has images, render the loading block.
                    $elem.find('div').hide();
                    $elem.addClass('unclickable').append($spinner);
                    $images.each(function () {
                        $(this).load(function () {
                            $elem.toLoad -= 1;
                            if ($elem.toLoad === 0) {
                                // This block is ready to go, render it on the page.
                                $elem.removeClass('unclickable').find('.image-loading-spinner').remove();
                                $elem.find('div').show();
                                // Trigger a window resize event because Masonry's resize logic is better (faster)
                                // than it's reload logic.
                                $(window).resize();
                            }
                        });
                    });
                }

                $images.error(function(){
                    var instance = $(this), 
                        isAdded = setInterval(function(){
                            if ($.contains(document.documentElement, instance[0])) {
                                instance.parent().parent().remove();
                                clearInterval(isAdded);
                            }
                        }, 500);
                });

                if ($elem.find('.lifestyle').length > 0) {
                    $elem.addClass('wide');
                }

                if ($elem.hasClass('instagram') && (Math.random() >= 0.5)) {
                    $elem.addClass('wide');
                }

                if (!related) {
                    $('.discovery-area').append($elem).masonry('appended', $elem, true);
                }
            });

            // Render youtube blocks with player
            videos = _.where(results, {'template': 'youtube'});  // (haystack, criteria)
            _.each(videos, function (video) {
                var video_id = video['original-id'] || video.id,
                    video_state_change = window.pagesTracking ?
                        _.partial(window.pagesTracking.videoStateChange, video_id) :
                            function () {/* dummy */};

                Willet.mediaAPI.getObject("video_gdata", video_id, function (video_data) {
                    var containers,
                        preferredThumbnailQuality = 'hqdefault',
                        thumbClass = 'youtube-thumbnail',
                        thumbURL = 'http://i.ytimg.com/vi/' + video_id +
                            '/' + preferredThumbnailQuality + '.jpg',
                        thumbObj,
                        thumbPath = ['entry', 'media$group', 'media$thumbnail'],
                        thumbChecker = PAGES.checkKeys(video_data, thumbPath),
                        thumbnailArray = thumbChecker.media$thumbnail || [];

                    thumbObj = _.findWhere(thumbnailArray, {
                        'yt$name': preferredThumbnailQuality
                    });
                    if (thumbObj && thumbObj.url) {
                        thumbURL = thumbObj.url;
                    }  // else fallback to the default thumbURL

                    containers = $(".youtube[data-label='" + video_id + "']");
                    containers.each(function () {
                        var container = $(this),
                            uniqueThumbnailID = PAGES.generateID('thumb-' + video_id),
                            thumbnail = $('<div />', {
                                'css': {  // this is to trim the 4:3 black bars
                                    'overflow': 'hidden',
                                    'height': 250 + 'px',
                                    'background-image': 'url("' + thumbURL + '")',
                                    'background-position': 'center center'
                                },
                                'id': uniqueThumbnailID
                            });

                        thumbnail
                            .hide()
                            .addClass('wide ' + thumbClass)
                            .click(function () {
                                // when the thumbnail is clicked, replace itself with
                                // the youtube video of the same size, then autoplay
                                player = new YT.Player(uniqueThumbnailID, {
                                    height: 250,
                                    width: 450,
                                    videoId: video_id,
                                    playerVars: {
                                        'autoplay': 1,
                                        'controls': 0
                                    },
                                    events: {
                                        'onReady': function (e) {
                                        },
                                        'onStateChange': video_state_change,
                                        'onError': function (e) {
                                        }
                                    }
                                });
                            });

                        if (container.find('.' + thumbClass).length === 0) {
                            // add a thumbnail only if there isn't one already
                            container.prepend(thumbnail);
                            mediator.fire('log', ['loaded video thumbnail ' + video_id]);
                        } else {
                            mediator.fire('log', ['prevented thumbnail dupe']);
                        }
                        container.children(".title").html(video_data.entry.title.$t);
                    });
                });
            });

            // make sure images are loaded or else masonry wont work properly
            $block.imagesLoaded(function ($images, $proper, $broken) {
                $broken.parents('.block').remove();
                $block.find('.block img[src=""]').parents('.block').remove();

                // Don't continue to load results if we aren't getting more results
                if (!related && initialResults > 0) {
                    setTimeout(function () {
                        PAGES.pageScroll();
                    }, 100);
                }

                $block.find('.pinpoint-youtube-area').click(function() {
                    $(this).html($(this).data('embed'));
                });

                for (var i in PAGES.blocksAppendedCallbacks) {
                    PAGES.setBlocksAppendedCallback(i, $block);
                }

                if (related) {
                    PAGES.layoutRelated(related, $block);
                    return;
                }

                // hack. tell masonry to reposition blocks
                $(window).resize();
                PAGES.setLoadingBlocks(false);
            });
        },
        'readyFunc': function () {
            // Special Setup
            PAGES.renderTemplates();

            PAGES.attachListeners();

            $('.discovery-area').masonry({
                itemSelector: '.block',

                columnWidth: function (containerWidth) {
                    return containerWidth / 4;
                },

                isResizable: true,
                isAnimated: true
            });

            $('.preview .mask, .preview .close').on('click', PAGES.hidePreview);

            $(window).scroll(PAGES.pageScroll);
            $(window).resize(PAGES.pageScroll);

            // Prevent social buttons from causing other events
            $('.social-buttons .button').on('click', function(e) {
                e.stopPropagation();
            });

            // Take any necessary actions
            PAGES.loadInitialResults();
        }
    };

    return me;
})(PAGES.full || {}, Willet.mediator);


// mobile component
PAGES.mobile = (function (me) {
    "use strict";

    var localData = {};

    me = {
        'layoutFunc': function (jsonData, belowFold, related) {
            var renderToView = function (viewSelector, templateName, context, append) {
                var template = $("[data-template-id='" + templateName + "']").html(),
                    renderedBlock;

                // template does not exist
                if (template === undefined) {
                    return;
                }

                renderedBlock = _.template(template, context);

                if (append) {
                    $(viewSelector).append(renderedBlock);
                } else {
                    $(viewSelector).html(renderedBlock);
                }
            };

            _.each(jsonData, function (data, index, list) {

                var objectId = data.id || data['original-id'],
                    templateName = PAGES.getModifiedTemplateName(data.template);

                // Old themes used 'instagram',
                // need to verify template exists
                if (templateName === 'image' &&
                    !$("[data-template-id='" + templateName + "']").html()) {
                    templateName = 'instagram';
                }

                // cache content's data for future rendering
                localData[templateName + objectId] = data;

                // render object if possible
                renderToView(".content_list", templateName, {
                    data: data
                }, true);

                // just rendered last element
                if (index === (list.length - 1)) {
                    PAGES.setLoadingBlocks(false);
                }
            });
        },
        'readyFunc': function () {

            if (MBP) {
                MBP.hideUrlBarOnLoad();
                MBP.preventZoom();
            }

            $(window).scroll(PAGES.pageScroll);
            $(window).resize(PAGES.pageScroll);

            Willet.mediator.fire('IR.loadInitialResults');
        }
    };

    return me;
})();