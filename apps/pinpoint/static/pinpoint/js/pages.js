// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth
var PAGES = (function ($, details, Willet) {
    "use strict";
    var i = 0,  // counter
        domTemplateCache = {},
        MAX_RESULTS_PER_SCROLL = 50,  // prevent long imagesLoaded
        SHUFFLE_RESULTS = details.page.SHUFFLE_RESULTS || false,
        mediator = Willet.mediator,
        browser = Willet.browser || {'mobile': false},
        mediaAPI = Willet.mediaAPI,
        scripts,
        scriptsLoaded = [],
        spaceBelowFoldToStartLoading = 500,
        templatesOnPage = {},  // dict of dicts
        loadingBlocks = false,
        globalIdCounters = {},
        hoverTimer,
        sizableRegex = /images\.secondfunnel\.com/,
        $wnd = $(window);

    function getLoadingBlocks() {
        return loadingBlocks;
    }

    function setLoadingBlocks(bool) {
        loadingBlocks = bool;
    }

    function getModifiedTemplateName(name) {
        // returns the template name suitable
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
                'styld.by', 'styld-by',
                'tumblr', 'pinterest', 'facebook', 'instagram'
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

    function getByAttrib(key, value, x, scope) {
        // attribute selector - shorthand for either
        // $('[data-key="value"]')
        // or
        // $('[key="value"]').
        // x and scope are optional. x defaults to 'data'.

        if (x === undefined) {
            x = 'data';
        }
        if (x !== '') {
            x = x + '-';
        }
        scope = scope || document;  // the whole page. window doesn't work.
        return $('[' + x + key + '="' +
            value.replace(/([ #;&,.+*~\':"!^$[\]()=>|\/@])/g,'\\$1') +
            '"]', scope);
    }

    function groupByAttrib($elements, key, data) {
        // given a list of element selector results, group them by
        // one of their common properties (denoted by key).
        // all properties are grouped by their STRING representation,
        // for safety and the 'undefined' special case.
        // data is optional. if it is true, data() is used in place of prop().
        var accessor = data ? 'data' : 'prop';
        return _.groupBy(
            _.map($elements, function (elem) {
                return $(elem);
            }),
            function (elem) {
                return elem[accessor](key);
            }
        );
    }

    function getTemplate(templateId) {
        // returns the required template.
        // right now, it only resolves mobile templates for mobile devices.
        // in the event that a mobile template is not found, the full template
        // will be served in place.
        var templateEls = templatesOnPage[templateId];

        if (browser.mobile && templateEls && templateEls.mobile) {
            // return "the first jquery-wrapped item in the list of this key"
            return templateEls.mobile[0].eq(0);
        } else {
            // if nothing specified or no mobile theme, pick the first one.
            // it can be an empty jquery object. (for e.g. 'image' template)
            try {
                return templateEls.desktop[0].eq(0);
            } catch (err) { }
            try {
                return templateEls['undefined'][0].eq(0);  // type undeclared
            } catch (err) { }
        }

        if (templateId !== 'preview') {
            // 'preview' is an exception (circular target-src reference)
            mediator.fire('error', ['oops, no template ' + templateId]);
        }
        // no such template - return an object that has .html()
        return $('');
    }

    function loadTemplates() {
        // saves all javascript templates on the page to a dict of dicts.
        // {
        //     product: {
        //         desktop: $(theElement),
        //         mobile: $(theElement),
        //     },
        //     combobox: {
        //         desktop: $(theElement),
        //         mobile: $(theElement),
        //     },
        //     ...
        // }
        // The idea is to call this function only once per page load.
        // Calling it more than once (perhaps to refresh themes?)
        //   will eliminate the performance improvements that it introduces.
        var templateIndicator = 'template-id',  // what makes a template a template
            templateEls = $('[data-' + templateIndicator + ']'),
            groupedTemplateEls;

        groupedTemplateEls = _.groupBy(templateEls, function (el) {
            return $(el).data('template-id');
        });

        _.each(groupedTemplateEls, function (value, key, list) {
            // for 'image', then for everyone else
            list[getModifiedTemplateName(key)] = list[key] =
                groupByAttrib($(value), 'media', true);
        });

        templatesOnPage = groupedTemplateEls;  // export
        return groupedTemplateEls;
    }

    function size(url, desiredSize) {
        // NOTE: We do not check if the new image exists because we implicitly
        // trust that our service will contain the required image.
        // ... Also, because it could be expensive to check for the required
        // image before use
        var newUrl,
            filename,
            imageSizes = [
                "icon", "thumb", "small", "compact", "medium", "large",
                "grande", "1024x1024", "master"
            ];

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

    function loadYoutubeVideo(videoID, thumbnailID, onStateChange) {
        // @return: None
        var player = new YT.Player(thumbnailID, {
            height: 250,
            width: 450,
            videoId: videoID,
            playerVars: {
                'autoplay': 1,
                'controls': 0
            },
            events: {
                'onReady': $.noop,
                'onStateChange': onStateChange,
                'onError': $.noop
            }
        });
    }

    function getYoutubeThumbnail(videoID, videoData) {
        // videoData is optional.
        // @return: string
        var preferredThumbnailQuality = 'hqdefault',
            thumbURL = 'http://i.ytimg.com/vi/' + videoID +
                '/' + preferredThumbnailQuality + '.jpg',
            thumbObj,
            thumbPath = ['entry', 'media$group', 'media$thumbnail'],
            thumbChecker,
            thumbnailArray;

        if (videoData) {
            thumbChecker = checkKeys(videoData, thumbPath);
            thumbnailArray = thumbChecker.media$thumbnail || [];
            thumbObj = _.findWhere(thumbnailArray, {
                'yt$name': preferredThumbnailQuality
            });
            if (thumbObj && thumbObj.url) {
                thumbURL = thumbObj.url;
            }  // else fallback to the default thumbURL
        }

        return thumbURL;
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
                        var $el = getTemplate(templateId);
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

    function isScrolledIntoView($elem, completely) {
        // mod of http://stackoverflow.com/a/488073/1558430
        // only checks for up-down scrolling.
        // completely: whether this is false when the elem is partially visible
        var docViewTop = $wnd.scrollTop(),
            docViewBottom = docViewTop + $wnd.height(),
            elemTop = $elem.offset().top,
            elemBottom = elemTop + $elem.height();

        if (completely) {
            return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
        } else {
            return ((elemTop <= docViewBottom) && (elemBottom >= docViewTop));
        }
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
            srcElement = getTemplate(src);
            if (srcElement.length) {
                // populate context with all available variables
                $.extend(context, originalContext, {
                    'page': details.page,
                    'store': details.store,
                    'data': $.extend({}, srcElement.data(), target.data())
                });

                context.data.show_count = true;

                target.html(renderTemplate(srcElement.html(), context));
            } else {
                target.html('Error: missing template #' + src);
            }
        });
    }
    /* --- END Utilities --- */

    /* --- START element bindings --- */
    function showPreview(me) {
        var data = $(me).data(),
            templateName = getModifiedTemplateName(data.template),
            $previewContainer = getTemplate("preview-container"),  // built-in
            $previewMask = $previewContainer.find('.mask'),
            $target = $previewContainer.find('.template.target'),
            fbButtons,
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

        template = getTemplate(templateId).html();

        if (!template && (templateId.indexOf('image') === 0)) {
            // legacy themes don't have 'image-' templates
            templateId = 'instagram' + templateId.slice(5);
            template = getTemplate(templateId).html();
        }

        if (!template || _.isEmpty($target)) {
            mediator.fire('log', ['oops, no preview template ' + templateName, templateId]);
            return;
        }

        data.is_preview = !_.isUndefined(data.is_preview) ? data.is_preview : true;

        renderedTemplate = renderTemplate(template, {
            'data': data,
            'page': details.page,
            'store': details.store
        });

        $target.html(renderedTemplate);

        mediator.fire('PAGES.previewOpened');
        mediator.fire('tracking.clearTimeout');
        mediator.fire('tracking.setSocialShareVars', [
            {"sType": "popup", "url": data.url}
        ]);

        $previewContainer.css('display', 'table').fadeIn(100);
        if ($previewMask.length) {
            $previewMask.fadeIn(100);
        }

        // Parse Facebook, Twitter buttons
        if (window.FB) {
            fbButtons = $previewContainer.find('.social-buttons .button.facebook, .fb-like');
            if (fbButtons.length) {
                // if it does not exist, script will init
                // ALL buttons on the page at once
                window.FB.XFBML.parse(fbButtons[0]);
            }
        }

        if (window.twttr) {
            window.twttr.widgets.load();
        }

        // late binding for all close buttons
        $('.preview .mask, .preview .close').on('click', hidePreview);
    }

    function addPreviewCallback(func) {
        // used by some themes. func accepts no arguments.
        mediator.on('PAGES.previewOpened', func);
    }

    function addOnBlocksAppendedCallback(func) {
        // used by some themes. func accepts no arguments.
        mediator.on('PAGES.blocksAppended', func);
    }

    function hidePreview() {
        var $mask    = $('.preview .mask'),
            $preview = $('.preview.container');

        mediator.fire('tracking.setSocialShareVars', []);

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    }

    function reloadMasonry(options) {
        // Convenince method for triggering reload of Masonry
        $('.content_list, .discovery-area').each(function () {
            options = options || {
                itemSelector: '.block',
                columnWidth: $(this).width() / 4,
                isResizeBound: true,
                visibleStyle: {
                    opacity: 1
                },
                isAnimated: !browser.mobile,
                transitionDuration: (browser.mobile) ? 0 : '0.4s'
            };

            $(this).masonry(options).masonry('reload');
        });
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
        if (browser.mobile) {
            // no social buttons on top of products on mobile
            commonHoverOn(this, false, true);
        } else {
            commonHoverOn(this, true, true);
        }
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
        commonHoverOn(this, !browser.mobile, false);
    }

    function youtubeHoverOff() {
        commonHoverOff(this, $.noop, false);
    }

    function comboboxHoverOn() {
        commonHoverOn(this, !browser.mobile, true);
    }

    function comboboxHoverOff() {
        commonHoverOff(this, function (t) {
            mediator.fire('tracking.registerEvent', [{
                "type": "content",
                "subtype": "hover",
                "label": $(t).data("label")
            }]);
        }, true);
    }
    
    function lifestyleHoverOn() {
        commonHoverOn(this, !browser.mobile, false);
    }

    function lifestyleHoverOff() {
        commonHoverOff(this, $.noop, false);
    }

    function loadResults(belowFold, related, callback) {
        callback = callback || layoutResults;
        if (!loadingBlocks || related) {
            mediator.fire('IR.getResults', [callback, belowFold, related]);
        }
    }

    function lifestyleHoverOn() {
        commonHoverOn(this, true, false);
    }

    function lifestyleHoverOff() {
        commonHoverOff(this, $.noop, false);
    }

    function loadInitialResults(seed) {
        mediator.fire('IR.changeSeed', [seed]);
        mediator.fire('IR.getInitialResults', [layoutResults]);
    }

    function loadMoreResults(callback, belowFold, related) {
        // @deprecated
        return loadResults(belowFold, related, callback);
    }

    function layoutResults(jsonData, belowFold, related) {
        // renders product divs onto the page.
        // suppose results is (now) a legit json object:
        // {products: [], videos: [(sizeof 1)]}
        var $block, el, j, initialResults, productDoms = [], results,
            revisedType, template, templateEl, templateType, videos;

        // check for rogue json data.
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

        if (SHUFFLE_RESULTS) {  // first we shuffle it (if needed)
            results = _.shuffle(jsonData);
        }
        // then we limit it
        results = $(results || jsonData).slice(0, MAX_RESULTS_PER_SCROLL);
        initialResults = Math.max(results.length, MAX_RESULTS_PER_SCROLL);

        // add products
        _.each(results, function (result) {  // [template context]
            try {
                templateType = PAGES.getModifiedTemplateName(result.template) || 'product';
                templateEl = PAGES.getTemplate(templateType);
                template = templateEl.html();

                // in case an image is wrong, don't bother with the product
                if (result.image === "None") {
                    return;
                }

                switch (templateType) {
                case 'product':
                    // in case an image is lacking, don't bother with the product
                    if (!result.image) {
                        return;
                    }

                    // use the resized images
                    result.image = result.image.replace("master.jpg", "medium.jpg");
                    break;
                case 'combobox':
                    // in case an image is lacking, don't bother with the product
                    if (!result.image) {
                        return;
                    }
                    break;
                case 'image':
                    if (!template) {
                        // Legacy themes do not support these templates
                        revisedType = 'instagram';
                        templateEl = PAGES.getTemplate(revisedType);
                        template = templateEl.html();
                    }
                    break;
                default:
                    break;
                }

                var renderedBlock = PAGES.renderTemplate(template, {
                    'data': result,
                    'page': PAGES.details.page,
                    'store': PAGES.details.store
                }, true);
                if (!renderedBlock.length) {
                    mediator.fire('error', ['skipping empty template block']);
                    return;
                } else {
                    el = $(renderedBlock);
                    el.data(result);  // populate the .product.block div with data

                    var templateElsLength = el.length;
                    for (j=0; j<templateElsLength; j++) {
                        // didn't have a better name for a loop
                        productDoms.push(el[j]);
                    }
                }

            } catch (err) {  // hide rendering error
                mediator.fire('error', ['oops @ item', err]);
            }
        });

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
                $elem.find('div').addClass('hidden');
                $elem.addClass('unclickable').append($spinner);
                $images.each(function () {
                    $(this).load(function () {
                        $elem.toLoad -= 1;
                        if ($elem.toLoad === 0) {
                            // This block is ready to go, render it on the page.
                            $elem.removeClass('unclickable').find('.image-loading-spinner').remove();
                            $elem.find('div').removeClass('hidden');
                            // Trigger a window resize event because Masonry's resize logic is better (faster)
                            // than it's reload logic.
                            $wnd.resize();
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
                        $.noop;

            mediaAPI.getObject("video_gdata", video_id, function (video_data) {
                // get results from the page...
                // ... and from unrendered results
                var containers = $(".youtube[data-label='" + video_id + "']"),
                    new_containers = $block.filter(".youtube[data-label='" + video_id + "']"),
                    thumbClass = 'youtube-thumbnail',
                    thumbURL = getYoutubeThumbnail(video_id, video_data);

                containers = containers.add(new_containers);

                containers.each(function () {
                    var container = $(this),
                        uniqueThumbnailID = generateID('thumb-' + video_id),
                        thumbnail = $('<div />', {
                            'css': {  // this is to trim the 4:3 black bars
                                'overflow': 'hidden',
                                'height': 250 + 'px',
                                'background-image': 'url("' + thumbURL + '")',
                                'background-position': 'center center'
                            },
                            'id': uniqueThumbnailID
                        });

                    // when the thumbnail is clicked, replace itself with
                    // the youtube video of the same size, then autoplay
                    thumbnail
                        .addClass('wide ' + thumbClass)
                        .click(function () {
                            loadYoutubeVideo(video_id, uniqueThumbnailID,
                                             video_state_change);
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

        $block.imagesLoaded(function ($images, $proper, $broken) {
            // make sure images are loaded or else masonry wont work properly
            if ($broken && $broken.length) {
                // possible that if all images are proper,
                // this is undefined; i.e.
                // Uncaught TypeError: Cannot call method 'parents' of undefined
                $broken.parents('.block').remove();
            }
            $block.find('.block img[src=""]').parents('.block').remove();

            // get more results if we haven't filled the screen yet
            if (!related && initialResults > 0) {
                setTimeout(function () {
                    PAGES.pageScroll();
                }, 100);
            }

            $block.find('.pinpoint-youtube-area').click(function() {
                $(this).html($(this).data('embed'));
            });

            mediator.fire('PAGES.blocksAppended', [$block]);

            if (related) {
                PAGES.layoutRelated(related, $block);
                return;
            }

            // tell masonry to reposition blocks
            reloadMasonry();
            PAGES.setLoadingBlocks(false);
        });
    }

    function layoutRelated(product, relatedContent) {
        /* Load related content into the masonry instance.
           @return: none */
        var $product = $(product),
            initialBottom = $product.position().top + $product.height(),
            $target = $product.next();

        // Find a target that is low enough on screen
        // TODO: can $target.next() also be above initialBottom?
        if (($target.position().top) <= initialBottom) {
            $target = $target.next();
        }

        // Inserts content after the clicked product block (Animated)
        relatedContent.insertAfter($target);
        reloadMasonry();
        relatedContent.show();
    }

    function pageScroll() {
        // calculates screen location and decide if more results
        // should be displayed.
        var discoveryBlocks = $('.block', '.discovery-area'),
            noResults     = (discoveryBlocks.length === 0),
            pageBottomPos = $wnd.innerHeight() + $wnd.scrollTop(),
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
            lowestHeight = lowestBlock.offset().top + lowestBlock.height();
        }

        if (noResults || (pageBottomPos + spaceBelowFoldToStartLoading > lowestHeight)) {
            loadResults(layoutResults);
        }

        $('.block', '.discovery-area').each(function (idx, obj) {
            // broadcast which blocks are visible
            var $block = $(obj),
                blockWasInView = $block.hasClass('in-view') || false,
                blockIsInView = isScrolledIntoView($block, false);
            $block.toggleClass('in-view', blockIsInView);  // tell the block

            if (blockWasInView !== blockIsInView && $block.hasClass('wide')) {
                // visibility changed
                if (blockIsInView) {
                    $block.find('.tap_indicator')
                        .removeClass('fadeIn')
                        .addClass('animated fadeOut');
                } else {
                    $block.find('.tap_indicator')
                        .removeClass('fadeOut')
                        .addClass('animated fadeIn');
                }
            }
        });
    }

    function windowResize() {
        // if the browser changes size, switch to mobile templates,
        // even if the device is not mobile, and vice versa.
        // this cannot "un-render" js templates previously rendered with
        // a different-size template.
        var oldState = browser.mobile;
        browser.mobile = ($wnd.width() < 1024);

        if (browser.mobile !== oldState) {  // if it changed
            if (browser.mobile) {
                // style tag has no disabled attrib, but the DOM has it
                $('style.mobile-only').prop('disabled', '');
                $('style.desktop-only').prop('disabled', 'disabled');
            } else {
                $('style.mobile-only').prop('disabled', 'disabled');
                $('style.desktop-only').prop('disabled', '');
            }
        }

        var $discovery = $('.discovery-area'),
            discoveryWidth = $discovery.width(),
            discoveryHeight = $discovery.height(),
            oldDiscoveryWidth = $discovery.data('width'),
            oldDiscoveryHeight = $discovery.data('height');
        if (discoveryWidth !== oldDiscoveryWidth ||
                discoveryHeight !== oldDiscoveryHeight) {
            // size of discovery area changed - update masonry
            reloadMasonry();
            // and update the old widths/heights
            $discovery.data({
                'width': discoveryWidth,
                'height': discoveryHeight
            });
        }
    }

    function attachListeners() {
        var $discovery = $('.discovery-area');
        if ($discovery.length) {
            // use delegated events to reduce overhead
            $discovery.on('click', '.block.product:not(.unclickable), ' +
                                   '.block.combobox:not(.unclickable)',
                function (e) {
                    showPreview(e.currentTarget);
                    mediator.fire('IR.updateClickStream', [e.currentTarget, e]);
                });

            $discovery.on('click', '.block.image:not(.unclickable)',
                function (e) {
                    showPreview(e.currentTarget);
                });

            // load related content; update contentstream
            $discovery.on('click', '.block:not(.youtube):not(.unclickable)',
                function (e) {
                    mediator.fire('IR.updateContentStream', [e.currentTarget]);
                });

            // hovers
            $discovery.on({
                'mouseenter': productHoverOn,
                'mouseleave': productHoverOff
            }, '.block.product:not(.unclickable), .block.combobox:not(.unclickable) .product');

            $discovery.on({
                'mouseenter': youtubeHoverOn,
                'mouseleave': youtubeHoverOff
            }, '.block.youtube');

            $discovery.on({
                'mouseenter': comboboxHoverOn,
                'mouseleave': comboboxHoverOff
            }, '.block.combobox:not(.unclickable) .lifestyle');

            // Is this safe enough?
            $discovery.on({
                'mouseenter': lifestyleHoverOn,
                'mouseleave': lifestyleHoverOff
            }, '.block.image:not(.unclickable)');
        }

        // Prevent social buttons from causing other events
        $('.social-buttons').find('.button').on('click', function (e) {
            e.stopPropagation();
        });

        $wnd.resize(_.throttle(windowResize, 1000))
            .resize(_.throttle(pageScroll, 300))
            .scroll(pageScroll);

        if (window.MBP) {
            // @mobile
            window.MBP.hideUrlBarOnLoad();
            window.MBP.preventZoom();
        }

        $discovery.on({
            mouseenter: comboboxHoverOn,
            mouseleave: comboboxHoverOff
        }, '.block.combobox:not(.unclickable) .lifestyle');

        // Is this safe enough?
        $discovery.on({
            mouseenter: lifestyleHoverOn,
            mouseleave: lifestyleHoverOff
        }, '.block.image:not(.unclickable)');
    }
    /* --- END element bindings --- */

    function load(scripts) {
        // loads a list of scripts by url.
        _.each(scripts, function (script) {
            if (!_.contains(scriptsLoaded, script.src)) {
                $.getScript(script.src || script, script.onload || $.noop);
            } else {
                mediator.fire('error', [script.src + ' already loaded; skipping.']);
            }
        });
    }

    function ready() {
        // Special Setup
        loadTemplates(); // populate list of templates in templatesOnPage
        renderTemplates();
        attachListeners();

        // Initialize Masonry
        reloadMasonry();
        $('.content_list, .discovery-area').masonry('bindResize');

        // Take any necessary actions
        mediator.fire('PAGES.ready', []);
        loadInitialResults();
    }

    function init(readyFunc, layoutFunc) {
        // both functions are optional.

        var pubDate;
        if (details && details.page && details.page.pubDate) {
            pubDate = details.page.pubDate;
        }
        mediator.fire('log', [  // feature, not a bug
            '____ ____ ____ ____ _  _ ___     ____ _  _ ' +
            '_  _ _  _ ____ _    \n[__  |___ |    |  | |' +
            '\\ | |  \\    |___ |  | |\\ | |\\ | |___ | ' +
            '   \n___] |___ |___ |__| | \\| |__/    |   ' +
            ' |__| | \\| | \\| |___ |___ \n' +
            '           Published ' + pubDate]);


        if (readyFunc) {  // override
            ready = readyFunc;
        }
        if (layoutFunc) {  // override
            layoutResults = layoutFunc;
        }
        load(scripts);
        $(document).ready(ready);
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
        'onload': $.noop
    }];

    // not sure why we exposed hidePreview... here are deprecation hooks.
    mediator.on('PAGES.showPreview', showPreview);
    mediator.on('PAGES.hidePreview', hidePreview);

    return {
        'init': _.once(init),
        'addPreviewCallback': addPreviewCallback,
        'addOnBlocksAppendedCallback': addOnBlocksAppendedCallback,
        'renderTemplate': renderTemplate,
        'renderTemplates': renderTemplates,
        'reloadMasonry': reloadMasonry,
        'loadInitialResults': loadInitialResults,
        'loadMoreResults': loadMoreResults,
        'layoutResults': layoutResults,
        'layoutRelated': layoutRelated,
        'attachListeners': attachListeners,
        'pageScroll': pageScroll,
        'details': details,
        'getLoadingBlocks': getLoadingBlocks,
        'setLoadingBlocks': setLoadingBlocks,
        'getModifiedTemplateName': getModifiedTemplateName,
        'getTemplate': getTemplate
    };
}(jQuery, window.PAGES_INFO || window.TEST_PAGE_DATA, Willet));


// mobile component
PAGES.mobile = (function (me, Willet) {
    "use strict";

    var localData = {},
        mediator = Willet.mediator;

    me = {
        'renderToView': function (viewSelector, templateName, context, append) {
            var template = PAGES.getTemplate(templateName).html(),
                renderedBlock;

            // template does not exist
            if (template === undefined || template === '') {
                return;
            }

            renderedBlock = _.template(template, context);
            renderedBlock = $(renderedBlock);
            renderedBlock.data(context);

            if (append) {
                $(viewSelector).append(renderedBlock);
            } else {
                $(viewSelector).html(renderedBlock);
            }
        },

        'layoutFunc': function (jsonData, belowFold, related) {
            _.each(jsonData, function (data, index, list) {

                var objectId = data.id || data['original-id'],
                    templateName = PAGES.getModifiedTemplateName(data.template);

                // Old themes used 'instagram',
                // need to verify template exists
                if (templateName === 'image' &&
                        !PAGES.getTemplate(templateName).html()) {
                    templateName = 'instagram';
                }

                // cache content's data for future rendering
                localData[templateName + objectId] = data;

                // render object if possible
                // .content_list is here for backward compatibility only
                me.renderToView(".content_list, .discovery-area", templateName, {
                    data: data
                }, true);

                // just rendered last element
                if (index === (list.length - 1)) {
                    PAGES.setLoadingBlocks(false);
                }
            });
        }
    };

    // @deprecated
    window.render_to_view = me.renderToView;  // old themes compatability
    window.local_data = me.local_data = me.localData = localData;  // old themes compatability

    return me;
}(PAGES.mobile || {}, Willet));
