// dammit jim, I'm a developer, not a scientist
// https://forum.javascriptmvc.com/topic/any-hints-of-what-is-wrong#32525000001144009

var Willet = window.Willet || {};

Willet.pages = Willet.pages || (function ($, _, Willet, undefined) {
    "use strict";

    var observatory = new can.Observe({/* default KVs */}),
        iif = function (cond, ifTrue, ifFalse) {
            return cond ? ifTrue : ifFalse;
        },
        init,
        mediator = Willet.mediator,
        getTemplate,
        addTileClass,
        getTileModel,
        getTileView,
        classes = {};

    // set up observatory (changes that ought to be observed)
    observatory.bind('change', function (ev, attr, how, newVal, oldVal) {
        // in practice, you should make new .bind()s without the mediator.
        Willet.mediator.fire('Pages.observeChanged',
            [ev, attr, how, newVal, oldVal]);
    });
    observatory.bind('browser.mobile', function (ev, attr, how, newVal, oldVal) {
        // in practice, you should make new .bind()s without the mediator.
        Willet.mediator.fire('Pages.resize',
            [ev, attr, how, newVal, oldVal]);
    });

    classes.TileModel = can.Model.extend({
        'findAll': {
            // partial jsonp solution: http://canjs.com/docs/can.Model.findAll.html
            // "force" a jsonp request to get all objects
            // Note: .findAll can also accept an array, but you probably should not be doing that.
            // http://haacked.com/archive/2008/11/20/anatomy-of-a-subtle-json-vulnerability.aspx
            'url': PAGES_INFO.IRResourceUrl,
            'dataType': "jsonp"
        }
    }, {  // default instance attributes
        // three-way bindings
        'view': undefined,
        'element': undefined,

        'clickable': true,
        'socialButtons': [],  // default: no buttons
        'price': 0,
        'propBag': $.noop  // @override
    });

    // listen to changes to the tile and update the view if it knows which one it is.
    classes.TileModel.bind('updated', function (ev, tile) {
        if (tile.view) {
            console.log('updating tile.');
            tile.element.html(tile.view.repr());
        }
    });


    classes.TileView = can.Control.extend({
        'init': function () {
            // "shows" a given tile by attaching it to an element.
            this.options.model.view = this;  // coupling
        },
        'defaults': {  // magic
            // 'wide': false  // via this.options.wide, or new thingy("#elem", {wide: false})
        },
        'template': function () {
            var templateHTML = '(base tile template missing!)',
                templateName = this.options.model.template;
            return getTemplate(templateName).html() ||
                   $('#tile_template').html() ||  // fallback
                   templateHTML;  // if fallback is missing too
        },
        'repr': function () {  // TODO; figure out how to make masonry accept doc fragments
            return _.template(this.template(), {
                'data': $.extend(
                    {},
                    this.options.model,           // default attributes
                    {'wide': this.wide()},        // default override
                    this.options.model.propBag()  // subclass override
                )
            });
        },
        'wide': function () {  // @override
            switch (this.template) {
            case 'image':
            case 'instagram':
            case 'tumblr':
            case 'styld-by':
            case 'styld.by':
            case 'pinterest':
            case 'facebook':
                if (options.imageTileWide !== undefined) {
                    return (Math.random() < options.imageTileWide);
                }
                return (Math.random() < 0.5);
            default:
                return false;
            }
        },
        'appendTo': function ($container) {
            // this tile puts its template inside the container when it's
            // done loading.
            var view = this,
                $element = this.element;
            $element.imagesLoaded(function (instance) {
                if (!($container && $container.length)) {
                    throw ("Container reference missing!");
                }

                // events don't get registered. have to put it here :(
                $(instance.elements).click(_.bind(view.click, view));

                $container.append(instance.elements);
                $container.masonry('appended', instance.elements); // !!
                $container.masonry('layout');
            });
        },
        'image': function (url, fakeWidth) {
            // using its size, estimate the best choice of image size to use.
            // if the image is not provided by the image service, the same url
            // is returned.
            var sizableRegex = /images\.secondfunnel\.com/,
                imageSizes = [
                    "icon",  // 24 x 32  (sizes aren't always correct)
                    "thumb",  // 37 x 50
                    "small",  // 75 x 100
                    "compact",  // 120 x 160
                    "medium",  // 180 x 240
                    "large",  // 360 x 480
                    "grande",  // 450 x 600
                    "1024x1024",  // 1024 x 1024
                    "master"  // 1500 x 2000
                ],
                maxWidth;
            if (!sizableRegex.test(url)) {
                return url;  // not resizable
            }

            // calculate the pixel-perfect width of 'the thing'.
            maxWidth = (fakeWidth || this.element.width()) *
                       (window.devicePixelRatio || 1);

            // return the size that is at least as big as the container.
            if (maxWidth <= 24) {
                return 'icon';
            }
            if (maxWidth <= 37) {
                return 'thumb';
            }
            if (maxWidth <= 75) {
                return 'small';
            }
            if (maxWidth <= 120) {
                return 'compact';
            }
            if (maxWidth <= 180) {
                return 'medium';
            }
            if (maxWidth <= 360) {
                return 'large';
            }
            if (maxWidth <= 450) {
                return 'grande';
            }
            if (maxWidth <= 1024) {
                return '1024x1024';
            }
            return 'master';
        },
        'error': function () {
            // @override. what constitutes an error for your subclassed tile?
            // bearing in mind that this.element isn't anything
            this.element.remove();
        },
        'click': function () {  // @override
            // the default tile opens a preview given an instance of itself.
            var preview = new classes.PreviewWindowView(
                this.options.element,
                this.options.model
            );
            preview.open();
        }
    });

    classes.PreviewWindowView = can.Control.extend({
        // extend this to show a different template (or something)
        'init': function ($element, options) {
            // $element: the element with our data
            // options: overrides to be given to the data
            this.element = $element;
            this.options = options;

            var context = {'data': $.extend({}, this.element.data(), this.options)},
                previewTemplate = this.template(context),
                $previewContainer = $(_.template(previewTemplate.html(), context)),  // built-in
                $previewMask = $previewContainer.find('.mask');

            // save references
            this.options.container = $previewContainer;
            this.options.mask = $previewMask;

            this.options.container
                .find('.mask, .close')
                .click(_.bind(this.close, this));
        },
        'template': function (context) {
            // returns the html contents of whichever template is available
            // and this controller thinks should be used
            var previewContainer = getTemplate('preview_container'),  // i.e. preview_container_template
                intendedPreviewName,
                intendedPreview, subTemplate;
            if (!previewContainer.length) {
                throw ('Missing preview container!');
            }

            // if this thing belongs to a product, show the product
            intendedPreviewName = this.options.template;
            if (!_.isEmpty(context['related-products'])) {
                context['related-product'] = context['related-products'][0];
                intendedPreviewName += '-product';
            }

            intendedPreview = getTemplate(intendedPreviewName + '_preview');  // i.e. product_preview_template
            if (!intendedPreview.length) {
                intendedPreview = $('#tile_preview_template');  // fallback
            }

            // strip <script template> tags (they don't have DOM structure)
            previewContainer = $(previewContainer.html());

            // put preview content into the container.
            subTemplate = _.template(intendedPreview.html(), context);
            $('.template.target', previewContainer).replaceWith(subTemplate);
            return $('<script />').append(previewContainer);  // rewrap
        },
        'fadeDuration': function () {
            // 768 is the boundary between desktop and mobile modes
            // $(window) is calculated ~4 times per preview showing.
            if ($(window).width() >= 768) {
                return this.options.previewAnimationDuration;
            }
            return this.options.previewMobileAnimationDuration || 0;
        },
        'open': function () {
            // create a preview container, then show it
            this.options.container
                .appendTo('body')
                .css('display', 'table')
                .fadeIn(this.fadeDuration());
            if (this.options.mask && this.options.mask.length) {
                this.options.mask.fadeIn(this.fadeDuration());
            }
        },
        'close': function () {
            // fade out the container and mask, then remove them
            this.options.container
                .add(this.options.mask)
                .fadeOut(this.fadeDuration())
                .remove();
        },
        '.close click': function ($el, ev) {  // broken
            this.close();
        }
    });

    classes.DiscoveryArea = can.Control.extend({  // Controller
        'init': function () {
            // available to you in this scope: this.element, this.options
            this.reloadMasonry.apply(this);
            this.getResults();  // once
        },
        'reloadMasonry': function (overrides) {
            // reload masonry with its needed options
            var options = this.options,
                settings = $.extend({}, {
                    'columnWidth': options.columnWidth(this.element),
                    'animationDuration': options.masonryAnimationDuration,
                    'itemSelector': options.discoveryItemSelector,
                    'bindResize': true
                }, overrides);
            this.element.masonry(settings);
        },
        'getResults': function (/* seeds: undefined */) {
            // overcome CanJS's extend limitation by fetching objects ourselves.
            var options = this.options,
                completeCallback = _.bind(this.layoutResults, this),
                createModels = function (tilesData, textStatus, jqXHR) {
                    // create Tiles with their subclasses, (preferably) not Tile.
                    var i, tileModels = [], tileModel, tileData, TileSubclass;
                    for (i = 0; i < tilesData.length; i++) {
                        tileData = tilesData[i];
                        TileSubclass = getTileModel(tileData.template);
                        tileModel = new TileSubclass(tileData);
                        tileModels.push(tileModel);
                    }
                    return completeCallback(tileModels);
                };

            // use custom ajax call to get tiles of any class
            $.ajax({
                'url': options.IRResourceUrl,
                'dataType': 'jsonp',
                'data': {
                    'results': options.IRResultsCount
                    // 'seeds': seeds
                },
                'timeout': options.IRTimeout,
                'success': createModels,
                'error': function () {
                    createModels(options.backupResults, null, null);
                }
            });
        },
        'layoutResults': function (tileModels) {
            var i, $el, tileView, SubclassView, $element = this.element;

            for (i = 0; i < tileModels.length; i++) {
                // get a TileView best-suited for its template.
                SubclassView = getTileView(tileModels[i].template);

                tileView = new SubclassView($('<div />'), {
                    'model': tileModels[i],
                    'containerElement': $element  // reference back to the discovery area
                });

                // replace dummy div with its representation
                tileView.element = $(tileView.repr());

                // three-way bindings, i.e. you can now do
                //   $('.tile').eq(0).data('view')   (view)
                //     .options.model                (model)
                //       .view                       (view)
                //         .element                  (element)
                tileView.element.data({
                    'view': tileView,
                    'model': tileView.options.model
                });

                if (tileView.wide()) {
                    tileView.element.addClass('wide');
                }

                tileView.appendTo($element);  // !! not a jQuery call
            }
        },
        'checkHeight': function () {
            // calculates screen location and decide if more results
            // should be displayed.
            var discoveryBlocks = this.element.find('.tile').slice(-5),
                // only the last 4 tiles can be at the bottom of the page.
                // made it 5 just to be safe.
                noResults     = (discoveryBlocks.length === 0),
                pageBottomPos = $(window).innerHeight() + $(window).scrollTop(),
                lowestBlock,
                lowestHeight;

            discoveryBlocks.each(function () {
                if (!lowestBlock || lowestBlock.offset().top < $(this).offset().top) {
                    lowestBlock = $(this);
                }
            });

            if (!lowestBlock) {
                lowestHeight = 0;
            } else {
                lowestHeight = lowestBlock.offset().top + lowestBlock.height();
            }

            if (noResults || (pageBottomPos + 500 > lowestHeight)) {
                this.getResults();
            }
        },
        '{window} scroll': function ($el, ev) {
            this.checkHeight();
        },
        '{window} resize': function ($el, ev) {
            // spec: if a browser is ‘mobile’ when the page loads, it stays ‘mobile’ even if the orientation changes
            // Willet.browser = Willet.browser || {};
            // Willet.browser.mobile = ($(window).width() < 768);
        },

        '.tile click': function ($el, ev) {
            return;
            if (!$el.hasClass('unclickable')) {
                // do what it does best
                new classes.PreviewWindowView($el, $el.data('model')).open();
            }  // else: it's unclickable, do nothing
        },
        '{tile} destroyed': function ($el, ev) {  // predefined magic
            // ...
        },
        '(selector) (event)': function ($el, ev) {
            // ...
        } // (more events)
    });

    getTemplate = function (templateId) {
        // searches for a template to use.
        // priority: gap_something_mobile_template
        //           gap_something_template
        //               something_mobile_template
        //               something_template
        //           empty template
        // templates are retrieved by ID because getElementById is still the
        // fastest across all browsers. (and that having multiple templates
        // of the same name doesn't make sense)
        var template = [];
        if (PAGES_INFO.storeName) {
            if (Willet.browser.mobile) {
                template = $('#' + PAGES_INFO.storeName + '_' + templateId + '_mobile_template');
            }
            if (!template.length) {
                template = $('#' + PAGES_INFO.storeName + '_' + templateId + '_template');
            }
        }
        if (Willet.browser.mobile) {
            template = $('#' + templateId + '_mobile_template');
        }
        if (!template.length) {
            template = $('#' + templateId + '_template');
        }
        if (!template.length) {
            template = $('');
        }
        return template;
    };

    addTileClass = function (name, constructor) {
        // allows arbitrary Tile definitions to be added to the list of
        // available classes.
        //
        classes[name] = constructor;
    };

    getTileModel = function (name) {
        // given a name (e.g. "youtube"), give you the class YoutubeTileModel
        // or if not found, TileModel.
        try {
            var preferredClass = can.capitalize(name) + 'TileModel';
            if (classes[preferredClass] !== undefined) {  // class defined
                return classes[preferredClass];
            }
        } catch (err) { }
        return classes.TileModel;
    };

    getTileView = function (name) {
        // given a name (e.g. "youtube"), give you the class YoutubeTileView
        // or if not found, TileView.
        try {
            var preferredClass = can.capitalize(name) + 'TileView';
            if (classes[preferredClass] !== undefined) {  // class defined
                return classes[preferredClass];
            }
        } catch (err) { }
        return classes.TileView;
    };


    /*(function konamiHandler(callback) {
        // register hidden service
        // on mobile, it is up up down down left right left right tap tap tap
        var konami = new Konami(callback);
    }(PAGES_INFO.konami || $.noop));*/

    function createBindable(FutureController, futureElement, options) {
        var fakeBind = new FutureController(futureElement, options);
        fakeBind.element = futureElement;
        fakeBind.on();
        return fakeBind;
    }

    function rebindEverything() {

    }

    init = function (options) {
        // run a controller that sets up everything.
        var RootController = can.Control.extend({
                'init': function ($element, options) {
                    var discovery = new classes.DiscoveryArea($element, options);  // create a controller-view pair
                }
            }),
            target = iif(typeof options.discoveryTarget === 'string',
                         $(options.discoveryTarget),
                         options.discoveryTarget),

            // kickstart (init route controller)
            root = new RootController(target, options);

        // other (legacy) stuff
        if (window.MBP) {
            MBP.hideUrlBarOnLoad();
            MBP.preventZoom();
        }
    };

    return {  // public interface (more interfaces available via mediator)
        'init': _.once(init),
        'classes': classes,  // export tile definition
        'addTileClass': addTileClass,
        'getTileModel': getTileModel,
        'getTileView': getTileView,
        'getTemplate': getTemplate
    };

// this line will throw exceptions as reasonably as possible
}(window.jQuery, window._, window.Willet));


function include(templateId) {
    // top scope. used by underscore.
    "use strict";
    var $el = Willet.pages.getTemplate(templateId);
    return $el.length ? $el.html() : '';
}


(function () {
    "use strict";
    // obj.watch: https://gist.github.com/eligrey/384583

    var link = function (m, v, c) {
        this._attrs = m;
        this._view = v;
        this._controller = c;
    };
    link.prototype.m = function () {  // var-args
        var args = arguments;
        this._attrs = this._attrs || {};  // default

        switch (args.length) {
        case 0:  // return all attrs
            return this._attrs;
        case 1:
            switch (typeof args[0]) {
            case 'object':  // merge this dict into current dict.
                for (var i in args[0]) {
                    if (args[0].hasOwnProperty(i)) {
                        this._attrs[i] = args[0][i];
                    }
                }
                return this._attrs;
            case 'string':  // return single value.
            default:
                return this._attrs[args[0]];
            }
        case 2:  // set K = V.
            this._attrs[args[0]] = args[1];
            return this._attrs;
        default:
            throw "ArgCountException";
        }
    };
    link.prototype.v = function () {  // var-args
        var args = arguments;
        switch (args.length) {
        case 0:  // return the view
            return this._view;
        case 1:  // set the view
            this._view = args[0];
            // TODO: rebind controllers
        default:
            throw "ArgCountException";
        }
    };
    link.prototype.c = function () {  // var-args
        var args = arguments;
        switch (args.length) {
        case 0:  // return the controller
            return this._controller;
        case 1:  // set the controller
            switch (typeof args[0]) {
            case 'object':
                if ($.isPlainObject(args[0])) {  // event-func pairs
                    this._controller = args[0];
                } else if ($.isArray(args[0])) {  // list of event-func KVs
                    throw "NotImplemented";
                } else {  // then what is it?
                    throw "MalformedObjectException";
                }
                return this._controller;
            case 'string':  // whatever this is, return it
                return this._controller[args[0]];
            }
            this._view.on(this._controller);
        case 2:  // assumed (string), (function)
            this._view.off(this._controller);  // unregister current ones
            this._controller[args[0]] = args[1];  // SUBSTITUTES old event
            this._view.on(this._controller);  // re-register them
        default:
            throw "ArgCountException";
        }
    };
}());