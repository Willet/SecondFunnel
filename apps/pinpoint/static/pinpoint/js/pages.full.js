var PAGES = PAGES || {};

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
            var $block,
                result,
                results = (PAGES.SHUFFLE_RESULTS) ?
                        (PAGES.fisherYates(jsonData, PAGES.MAX_RESULTS_PER_SCROLL) || []) :
                        $(jsonData).slice(0, PAGES.MAX_RESULTS_PER_SCROLL),  // no shuffle
                initialResults = Math.max(results.length, PAGES.MAX_RESULTS_PER_SCROLL),
                i,
                productDoms = [],
                template,
                templateEl,
                player,
                template_context,
                templateType,
                el,
                videos,
                appearanceProbability,
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
                    case 'youtube':
                        break;
                    case 'image':
                        // Legacy themes do not support these templates
                        revisedType = 'instagram';
                        if (!template) {
                            templateEl = $("[data-template-id='" + revisedType + "']");
                            template = templateEl.html();
                        }
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

                        productDoms.push(el[0]);
                    }

                } catch (err) {  // hide rendering error
                    mediator.fire('log', ['oops @ item', err]);
                }
            }

            // Remove potentially bad content
            productDoms = _.filter(productDoms, function(elem) {return !_.isEmpty(elem);});

            $block = $(productDoms);  // an array of DOM elements

            // if it has a lifestyle image, add a wide class to it so it's styled properly
            $block.each(function() {
                var $elem = $(this),
                    $images = $elem.find('img'),
                    rand_num = Math.random();

                // Create a spinner image that can be used to indicate a block is loading.
                var $spinner = $('<img/>', {
                    'class': "image-loading-spinner",
                    'style': "padding-top:100px; padding-bottom:100px; width:32px; height:32px; position:relative; left:50%;",
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
                            if ($elem.toLoad == 0) {
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

                if ($elem.find('.lifestyle').length > 0) {
                    $elem.addClass('wide');
                }

                if ($elem.hasClass('instagram')
                    && (rand_num >= 0.5)) {
                    $elem.addClass('wide');
                }

                if (!related) $('.discovery-area').append($elem).masonry('appended', $elem, true);
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

                        thumbnail.hide();

                        thumbnail.addClass('wide ' + thumbClass).click(function () {
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
            $block.imagesLoaded(function($images, $proper, $broken) {
                $broken.parents('.block').remove();
                $block.find('.block img[src=""]').parents('.block').remove();

                // Don't continue to load results if we aren't getting more results
                if (!related && initialResults > 0) {
                    setTimeout(function() {
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

                PAGES.setLoadingBlocks(false);

                // hack. tell masonry to reposition blocks
                $(window).resize();
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
            PAGES.setLoadingBlocks(true);
            PAGES.loadInitialResults();
            PAGES.setLoadingBlocks(false);
        }
    };

    return me;
})(PAGES.full || {}, Willet.mediator);