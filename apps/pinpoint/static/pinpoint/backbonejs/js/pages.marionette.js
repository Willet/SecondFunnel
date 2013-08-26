/*global setTimeout, imagesLoaded, Backbone, jQuery, $, _ */
// JSLint/Emacs js2-mode directive to stop global 'undefined' warnings.
if (!window.console) {  // shut up JSLint / good practice
    var console = window.console = {
        log: $.noop,
        error: $.noop
    };
}

// Declaration of the SecondFunnel JS application
var SecondFunnel = new Backbone.Marionette.Application();
SecondFunnel.vent = _.extend({}, Backbone.Events);  // Custom event trigger/listener

// keep reference to options. this needs to be done before classes are declared.
SecondFunnel.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};
SecondFunnel.option = function (name, defaultValue) {
    // convenience method for accessing PAGES_INFO or TEST_*
    var opt = Backbone.Marionette.getOption(SecondFunnel, name),
        keyNest = _.compact(name.split(/[:.]/)),
        keyName,
        cursor = SecondFunnel.options,
        i,
        depth;

    if (opt !== undefined && (keyNest.length === 1 && !_.isEmpty(opt))) {
        // getOption() returns a blank object when it thinks it is accessing
        // a nested option so we have to patch that up
        return opt;
    }
    // marionette sucks, so we'll do extra traversing to get stuff out of
    // our nested objects ourselves
    try {
        for (i = 0, depth = keyNest.length; i < depth; i++) {
            keyName = keyNest[i];
            cursor = cursor[keyName];
        }
        if (cursor !== undefined) {
            return cursor;
        }
    } catch (KeyError) {
        // requested traversal path does not exist. do the next line
        console.error('no such path');
    }
    return defaultValue;  // ...and defaultValue defaults to undefined
};
try {
    SecondFunnel.options.debug = 0;

    if (window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1') {
        SecondFunnel.options.debug = 1;
    }

    (function (hash) {
        var hashIdx = hash.indexOf('debug=');
        if (hashIdx > -1) {
            SecondFunnel.options.debug = hash[hashIdx + 6];
        }
    }(window.location.hash + window.location.search));
} catch (e) {
    // this is an optional operation. never let this stop the script.
}

// Marionette TemplateCache extension to allow checking cache for template
Backbone.Marionette.TemplateCache._exists = function (templateId) {
    // Checks if the Template exists in the cache, if not found
    // updates the cache with the template (if it exists), otherwise fail
    // returns true if exists otherwise false.
    var cached = this.templateCaches[templateId],
        cachedTemplate;

    if (cached) {
        return true;
    }

    // template exists but was not cached
    cachedTemplate = new Backbone.Marionette.TemplateCache(templateId);
    try {
        cachedTemplate.load();
        // Only cache on success
        this.templateCaches[templateId] = cachedTemplate;
    } catch (err) {
        if (!(err.name && err.name === "NoTemplateError")) {
            throw err;
        }
    }
    return !!this.templateCaches[templateId];
};

// Accept an arbitrary number of template selectors instead of just one.
// function will return in a short-circuit manner once a template is found.
Backbone.Marionette.View.prototype.getTemplate = function () {
    var i, templateIDs = Backbone.Marionette.getOption(this, "templates"),
        template = Backbone.Marionette.getOption(this, "template"),
        temp, templateExists, data;

    if (templateIDs) {
        if (typeof templateIDs === 'function') {
            // if given as a function, call it, and expect [<string> selectors]
            templateIDs = templateIDs(this);
        }

        for (i = 0; i < templateIDs.length; i++) {
            data = $.extend({},
                Backbone.Marionette.getOption(this, "model").attributes);
            data.template = SecondFunnel.getModifiedTemplateName(data.template);

            temp = _.template(templateIDs[i], {
                'options': SecondFunnel.options,
                'data': data
            });
            templateExists = Backbone.Marionette.TemplateCache._exists(temp);

            if (templateExists) {
                // replace this thing's desired template ID to the
                // highest-order template found
                template = temp;
                break;
            }
        }
    }

    return template;
};

// make new module full of transient utilities
SecondFunnel.module("observables", function (observables) {
    var testUA = function (regex) {
        return regex.test(window.navigator.userAgent);
    };

    observables.mobile = function () {
        return ($(window).width() < 768);  // 768 is set in stone now
    };
    observables.touch = function () {
        return ('ontouchstart' in document.documentElement);
    };

    observables.isAniPad = function () {
        // use of this function is highly discouraged, but you know it
        // will be used anyway
        return testUA(/ipad/i);
    };
});


SecondFunnel.module("intentRank",
    function (intentRank) {
        intentRank.base = "http://intentrank-test.elasticbeanstalk.com/intentrank";
        intentRank.templates = {
            'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
            'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
        };

        intentRank.initialize = function (options) {
            // Any additional init declarations go here
            var page = options.page || {},
                online = !page.offline;

            _.extend(intentRank, {
                'store': options.store,
                'campaign': options.campaign,
                // @deprecated: options.categories will be page.categories
                'categories': page.categories || options.categories || {},
                'backupResults': options.backupResults || [],
                'IRResultsCount': options.IRResultsCount || 10,
                'IRTimeout': options.IRTimeout || 5000,
                'content': options.content || [],
                'getResults': online ?
                              intentRank.getResultsOnline :
                              intentRank.getResultsOffline
            });

            broadcast('intentRankIntialized', intentRank);
        };

        intentRank.getResultsOffline = function (options, callback) {
            broadcast('beforeintentRankgetResultsOffline', options, callback, intentRank);
            var args = _.toArray(arguments).slice(2);
            args.unshift(intentRank.content);

            broadcast('intentRankgetResultsOffline', options, callback, intentRank);
            return callback.apply(callback, args);
        };

        intentRank.getResultsOnline = function (options, callback) {
            broadcast('beforeintentRankgetResultsOnline', options, callback, intentRank);

            var uri = _.template(intentRank.templates[options.type],
                    _.extend({}, options, intentRank, {
                        'url': intentRank.base
                    })),
                args = _.toArray(arguments).slice(2);

            $.ajax({
                url: uri,
                data: {
                    'results': intentRank.IRResultsCount
                },
                contentType: "json",
                dataType: 'jsonp',
                timeout: intentRank.IRTimeout,
                success: function (results) {
                    // Check for non-empty results.
                    results = results.length ? 
                        results :
                        // If no results, fetch from backup
                        _.shuffle(intentRank.backupResults);
                    args.unshift(results);
                    return callback.apply(callback, args);
                },
                error: function () {
                    SecondFunnel.vent.trigger('log', arguments[1]);
                    // On error, fall back to backup results
                    args.unshift(intentRank.backupResults);
                    return callback.apply(callback, args);
                }
            });

            broadcast('intentRankgetResultsOffline', options, callback, intentRank);
        };

        intentRank.changeCategory = function (category) {
            // Change the category; category has been validated
            // by the CategoryView, so a check isn't necessary
            broadcast('intentRankChangeCategory', category, intentRank);

            intentRank.campaign = category;
            return intentRank;
        };
    });


SecondFunnel.module("tracker",
    function (tracker) {
        // TODO: when done, split into its own file
        var _gaq = window._gaq || [],
            isBounce = true,  // this flag set to false once user scrolls down
            videosPlayed = [],
            parseUri = function (str) {
                // parseUri 1.2.2
                // (c) Steven Levithan <stevenlevithan.com>
                // MIT License
                var o = parseUri.options,
                    m = o.parser[o.strictMode ? "strict" : "loose"].exec(str),
                    uri = {},
                    i = 14;

                while (i--) {
                    uri[o.key[i]] = m[i] || "";
                }

                uri[o.q.name] = {};
                uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
                    if ($1) {
                        uri[o.q.name][$1] = $2;
                    }
                });

                return uri;
            },

            referrerName = function () {
                var host;

                if (document.referrer === "") {
                    return "noref";
                }

                host = parseUri(document.referrer).host;
                // want top level domain name (i.e. tumblr.com, not site.tumblr.com)
                host = host.split(".").slice(host.split(".").length - 2,
                    host.split(".").length).join(".");

                if (host === "") {
                    return "noref";
                }

                return host;
            },

            trackEvent = function (o) {
                var category = "appname=pinpoint|" +
                    "storeid=" + SecondFunnel.option('store:id') + "|" +
                    "campaignid=" + SecondFunnel.option('page:id') + "|" +
                    "referrer=" + referrerName() + "|" +
                    "domain=" + parseUri(window.location.href).host;

                _gaq.push(['_trackEvent', category, o.action, o.label, o.value || undefined]);
                broadcast('eventTracked', o, category);
            },

            setCustomVar = function (o) {
                var slotId = o.slotId,
                    name = o.name,
                    value = o.value,
                    scope = o.scope || 3; // 3 = page-level

                if (!(slotId && name && value)) {
                    return;
                }

                _gaq.push(['_setCustomVar', slotId, name, value, scope]);
            };

        tracker.registerEvent = function (o) {
            var actionData = [
                "network=" + o.network || "",
                "actionType=" + o.type,
                "actionSubtype=" + o.subtype || "",
                "actionScope=" + tracker.socialShareType
            ];

            tracker.notABounce(o.type);

            trackEvent({
                "action": actionData.join("|"),
                "label": o.label || tracker.socialShareUrl
            });
        };

        tracker.setSocialShareVars = function (o) {
            if (o && o.url && o.sType) {
                tracker.socialShareUrl = o.url;
                tracker.socialShareType = o.sType;
            } else {
                tracker.socialShareUrl = $("#featured_img").data("url");
                tracker.socialShareType = "featured";
            }
        };

        tracker.clearTimeout = function () {
            if (typeof tracker._pptimeout === "number") {
                window.clearTimeout(tracker._pptimeout);

                // TODO remove this? not valid in strict mode
                delete tracker._pptimeout;
            }
        };

        tracker.registerTwitterListeners = function () {
            if (!window.twttr) {
                return;
            }
            window.twttr.ready(function (twttr) {
                twttr.events.bind('tweet', function (event) {
                    tracker.registerEvent({
                        "network": "Twitter",
                        "type": "share",
                        "subtype": "shared"
                    });
                });

                twttr.events.bind('click', function (event) {
                    var sType;
                    if (event.region === "tweet") {
                        sType = "clicked";
                    } else if (event.region === "tweetcount") {
                        sType = "leftFor";
                    } else {
                        sType = event.region;
                    }
                    tracker.registerEvent({
                        "network": "Twitter",
                        "type": "share",
                        "subtype": sType
                    });
                });
            });
        };

        tracker.notABounce = _.once(function (how) {
            // visitor already marked as "non-bounce"
            // this function becomes nothing after it's first run, even
            // after re-initialisation, or if the function throws an exception.
            broadcast('notABounce', how, tracker);

            tracker.registerEvent({
                "type": "visit",
                "subtype": "noBounce",
                "label": how
            });
        });

        tracker.videoStateChange = function (videoId, event) {
            broadcast('videoStateChange', videoId, event, tracker);

            if (videosPlayed.indexOf(videoId) !== -1) {
                // not that video
                return;
            }

            if (event.data === window.YT.PlayerState.PLAYING) {
                videosPlayed.push(videoId);

                tracker.registerEvent({
                    "type": "content",
                    "subtype": "video",
                    "label": videoId
                });
            }
        };

        tracker.changeCampaign = function (campaignId) {
            setCustomVar({
                'slotId': 2,
                'name': 'CampaignID',
                'value': '' + campaignId
            });
        };

        tracker.init = function () {
            // this = SecondFunnel.vent
            // arguments = args[1~n] when calling .trigger()
            tracker.setSocialShareVars();

            // setTrackingDomHooks() on $.ready
        };

        // Backbone format: { '(event) (selectors)': function(ev), ...  }
        tracker.defaultEventMap = {
            // reset tracking scope: hover into featured product area
            "hover .featured": function () {
                // this = window because that's what $el is
                broadcast('featuredHover');
                tracker.clearTimeout();
                tracker.setSocialShareVars();
            },

            "hover .tile": function () {
                // this = window because that's what $el is
                broadcast('tileHover');
                tracker.registerEvent({
                    "type": "???",  // no known values for this new event
                    "subtype": "???",
                    "label": "???"
                });
            },

            "click .header a": function () {
                broadcast('headerHover');
                tracker.registerEvent({
                    "type": "clickthrough",
                    "subtype": "header",
                    "label": $(this).attr("href")
                });
            },

            "click .previewContainer .close": function () {
                broadcast('popupClosed');
                tracker.registerEvent({
                    "type": "???",  // no known values for this new event
                    "subtype": "???",
                    "label": "???"
                });
            },

            // buy now event
            "click a.buy": function (e) {
                broadcast('buyClick');
                tracker.registerEvent({
                    "type": "clickthrough",
                    "subtype": "buy",
                    "label": $(this).attr("href")
                });
            },

            // popup open event: product click
            "click .tile.product, .tile.combobox .product": function (e) {
                // TODO: data('label') === ?
                broadcast('tileClick');
                tracker.registerEvent({
                    "type": "inpage",
                    "subtype": "openpopup",
                    "label": $(this).data("label")
                });
            },

            // lifestyle image click
            "click .tile.combobox .lifestyle, .tile.image, .tile>img": function (e) {
                broadcast('lifestyleTileClick');
                tracker.registerEvent({
                    "type": "content",
                    "subtype": "openpopup",
                    "label": $(this).data("label")
                });
            },

            "click .pinterest": function (e) {
                // social hover and popup pinterest click events
                tracker.registerEvent({
                    "network": "Pinterest",
                    "type": "share",
                    "subtype": "clicked"
                });
            }
        };

        parseUri.options = {
            strictMode: false,
            key: [
                "source", "protocol", "authority", "userInfo", "user", "password",
                "host", "port", "relative", "path", "directory", "file", "query", "anchor"],
            q: {
                name: "queryKey",
                parser: /(?:^|&)([^&=]*)=?([^&]*)/g
            },
            parser: {
                strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
                loose: /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
            }
        };

        this.socialShareType = undefined;
        this.socialShareUrl = undefined;
        this._pptimeout = undefined;

        // add mediator triggers if the module exists.
        SecondFunnel.vent.on({
            'tracking:init': tracker.init,
            'tracking:registerEvent': tracker.registerEvent,
            'tracking:setSocialShareVars': tracker.setSocialShareVars,
            'tracking:clearTimeout': tracker.clearTimeout,
            'tracking:registerTwitterListeners': tracker.registerTwitterListeners,
            'tracking:notABounce': tracker.notABounce,
            'tracking:videoStateChange': tracker.videoStateChange,
            'tracking:changeCampaign': tracker.changeCampaign
        });

        // the app initializer init()s it
    });

SecondFunnel.module("layoutEngine",
    function (layoutEngine) {
        layoutEngine.options = {
            'isInitLayout': true,
            'isResizeBound': true,
            'visibleStyle': {
                'opacity': 1,
                '-webkit-transform': 'none'
            },
            'hiddenStyle': {
                'opacity': 0,
                '-webkit-transform': 'scale(1)'
            }
        };

        layoutEngine.initialize = function ($elem, options) {
            var mobile = SecondFunnel.observables.mobile();

            layoutEngine.selector = options.discoveryItemSelector;
            _.extend(layoutEngine.options, {
                'itemSelector': options.discoveryItemSelector,
                'columnWidth': options.columnWidth(),
                'isAnimated': !mobile,
                'transitionDuration': (mobile ?
                                       options.masonryMobileAnimationDuration :
                                       options.masonryAnimationDuration) + 's'
            }, options.masonry);

            $elem.masonry(layoutEngine.options).masonry('bindResize');
            layoutEngine.$el = $elem;
        };

        layoutEngine.call = function (callback, $fragment) {
            if (!(typeof callback === 'string' && callback in layoutEngine)) {
                var msg = !(typeof callback === 'string') ?
                          "Unsupported type " + (typeof callback) +
                              " passed to Layout Engine." :
                          "LayoutEngine has no property " + callback + ".";
                SecondFunnel.vent.trigger('log', msg);
                return layoutEngine;
            }
            var args = _.toArray(arguments);
            args[0] = layoutEngine[callback];
            return layoutEngine.imagesLoaded.apply(layoutEngine, args);
        };

        layoutEngine.append = function ($fragment, callback) {
            broadcast('fragmentAppended', $fragment);
            return callback ? callback($fragment) : layoutEngine;
        };

        layoutEngine.stamp = function (element) {
            broadcast('elementStamped', element);
            layoutEngine.$el.masonry('stamp', element);
            return layoutEngine;
        };

        layoutEngine.unstamp = function (element) {
            broadcast('elementUnstamped', element);
            layoutEngine.$el.masonry('unstamp', element);
            return layoutEngine;
        };

        layoutEngine.layout = function () {
            layoutEngine.$el.masonry('layout');
            return layoutEngine;
        };

        layoutEngine.reload = function ($fragment) {
            layoutEngine.$el.masonry('reloadItems');
            layoutEngine.$el.masonry();
            return layoutEngine;
        };

        layoutEngine.insert = function ($fragment, $target, callback) {
            var initialBottom = $target.position().top + $target.height();
            // Find a target that is low enough on the screen to insert after
            while ($target.position().top <= initialBottom &&
                $target.next().length > 0) {
                $target = $target.next();
            }
            $fragment.insertAfter($target);
            layoutEngine.reload();
            return callback ? callback($fragment) : layoutEngine;
        };

        layoutEngine.clear = function () {
            // Resets the LayoutEngine's instance so that it is empty
            layoutEngine.$el
                .masonry('destroy')
                .html("")
                .css('position', 'relative')
                .masonry(layoutEngine.options);
        };

        layoutEngine.imagesLoaded = function (callback, $fragment) {
            // Calls the broken handler to remove broken images as they appear;
            // when all images are loaded, calls the appropriate layout function
            var self = layoutEngine,
                args = _.toArray(arguments),
                imgLoad = imagesLoaded($fragment.children('img'));
            // Remove broken images as they appear
            imgLoad.on('progress',function (instance, image) {
                var $img = $(image.img),
                    $elem = $img.parents(self.selector);

                // TODO: This is the first point we know the dimensions of the image (until
                // image service returns dimensions).  What qualifies as too small?
                if (!image.isLoaded) {
                    $img.remove();
                } else {
                    // Append to container and called appended
                    self.$el.append($elem).masonry('appended', $elem);
                }
            }).on('always', function () {
                    // When all images are loaded, show the non-broken ones and reload
                    var $remaining = $fragment.filter(function () {
                        return !$.contains(document.documentElement,
                            $(this)[0]);
                    });
                    if ($remaining.length > 0) {
                        self.$el.append($remaining).masonry('appended',
                            $remaining);
                    }
                    args = args.slice(1);
                    callback.apply(self, args);
                });
            return layoutEngine;
        };
    });


var Tile = Backbone.Model.extend({
    'defaults': {
        // Default product tile settings, some tiles don't
        // come specifying a type or caption
        'caption': "Shop product",
        'tile-id': null,
        'content-type': "product",
        'related-products': []
    },

    'initialize': function (attributes, options) {
        var videoTypes = ["youtube", "video"],
            type = this.get('content-type').toLowerCase();

        this.type = 'image';
        this.attributes.caption = (this.attributes.caption === "None" ?
                                   " " :
                                   this.attributes.caption);
        if (_.contains(videoTypes, type)) {
            this.type = 'video';
        }
    },

    'is': function (type) {
        // check if a tile is of (type). the type is _not_ the tile's template.
        return this.get('content-type').toLowerCase() === type.toLowerCase();
    },

    'createView': function () {
        var targetClassName, TargetClass;

        switch (this.type) {
        case "video":
            TargetClass = VideoTileView;
            break;
        default:
            targetClassName = _.capitalize(this.type) + 'TileView';
            if (window[targetClassName] !== undefined) {
                TargetClass = window[targetClassName];
                break;
            }
            if (SecondFunnel.classRegistry &&
                SecondFunnel.classRegistry[targetClassName] !== undefined) {
                // if designers want to define a new tile view, they must
                // let SecondFunnel know about its existence.
                TargetClass = SecondFunnel.classRegistry[targetClassName];
                break;
            }
            TargetClass = TileView;
        }
        // undeclared / class not found in scope
        return new TargetClass({model: this});
    }
});

var TileCollection = Backbone.Collection.extend({
    // Our TileCollection manages ALL the tiles on the page.
    'model': function (attrs) {
        var SubClass = 'Tile';
        if (window[SubClass]) {
            return new window[SubClass](attrs);
        }
        return new Tile(attrs);  // base class
    },
    'loading': false,
    'totalItems': null,

    'initialize': function (arrayOfData) {
        // Our TileCollection starts by rendering several Tiles using the
        // data it is passed.
        for (var data in arrayOfData) {  // Generate Tile
            if (arrayOfData.hasOwnProperty(data)) {
                this.add(new Tile(data));
            }
        }
    }
});


var makeView = function (classType, params) {
    // view factory to allow views that bind to arbitrary regions
    // and use any template decided at runtime, e.g.
    //   someTemplate = '#derp1'
    //   a = makeView('Layout', {template: someTemplate})
    //   a.render()
    classType = classType || 'ItemView';
    return Backbone.Marionette[classType].extend(params);
};


var FeaturedAreaView = Backbone.Marionette.ItemView.extend({
    // $(...).html() defaults to the first item successfully selected
    // so featured will be used only if stl is not found.
    'model': new Tile(SecondFunnel.option('featured')),
    'template': "#stl_template, #featured_template, #hero_template",
    'onRender': function () {
        if (this.$el.length) {  // if something rendered, it was successful
            $('#hero-area').html(this.$el.html());
        }
    }
});


var TileView = Backbone.Marionette.Layout.extend({
    // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
    'tagName': "div", // TODO: Should this be a setting?
    'template': "#product_tile_template",
    'className': SecondFunnel.option('discoveryItemSelector', '').substring(1),

    'events': {
        'click': "onClick",
        'mouseenter': "onHover",
        "mouseleave": "onHover"
    },

    'regions': {
        'socialButtons': '.social-buttons',
        'tapIndicator': '.tap-indicator-target'
    },

    'initialize': function (options) {
        // Creates the TileView using the options.  Subclasses should not override this
        // method, rather provide an 'onInitialize' function
        var data = options.model.attributes,
            template = "#" + data.template + "_tile_template",
            self = this;

        if (Backbone.Marionette.TemplateCache._exists(template)) {
            this.template = template;
        }

        _.each(data['content-type'].toLowerCase().split(), function (cName) {
            self.className += " " + cName;
        });
        this.$el.attr({
            'class': this.className,
            'id': this.cid
        });

        _.bindAll(this, 'close');
        // If the tile model is removed, remove the DOM element
        this.listenTo(this.model, 'destroy', this.close);
        // Call onInitialize if it exists
        if (this.onInitialize) {
            this.onInitialize(options);
        }
        this.render();
    },

    'close': function () {
        // As it stands, since we aren't using a REST API, we don't store
        // the models anywhere so we don't need to destroy them.
        // Remove view and unbind listeners
        this.$el.remove();
        this.unbind();
        this.views = [];
    },

    'onHover': function (ev) {
        // Trigger tile hover event with event and tile
        SecondFunnel.vent.trigger("tileHover", ev, this);
        if (this.socialButtons && this.socialButtons.$el &&
            this.socialButtons.$el.children().length) {
            var inOrOut = (ev.type === 'mouseenter') ? 'fadeIn' : 'fadeOut';
            this.socialButtons.$el[inOrOut](200);
            this.socialButtons.currentView.load();
        }
    },

    'onClick': function (ev) {
        "use strict";
        var tile = this.model,
            preview = new PreviewWindow({
                'model': tile, 'caller': ev.currentTarget
            });

        preview.render();
        preview.content.show(new PreviewContent({
            'model': tile, 'caller': ev.currentTarget
        }));

        SecondFunnel.vent.trigger("tileClicked", ev, this);
    },

    'onBeforeRender': function () {
        var maxImageSize;
        try {
            maxImageSize = _.findWhere(this.model.images[0].sizes,
                {'name': 'master'})[0].width;

            if (Math.random() > 0.333 && maxImageSize >= 512) {
                this.$el.addClass('wide');
            }  // else: leave it as 1-col
        } catch (imageServiceNotReady) {
            if (Math.random() < 0.333) {
                this.$el.addClass('wide');
            }
        }
    },

    'onRender': function () {
        // Listen for the image being removed from the DOM, if it is, remove
        // the View/Model to free memory
        this.$("img").on('remove', this.close);
        if (SocialButtons.prototype.buttonTypes.length && !(SecondFunnel.observables.touch() || SecondFunnel.observables.mobile())) {
            this.socialButtons.show(new SocialButtons({model: this.model}));
        }
        this.tapIndicator.show(new TapIndicator());
    }
});

// TODO: Seperate this into modules/seperate files
var VideoTileView = TileView.extend({
    // VideoTile extends from TileView, allows playing of Video files; for
    // now, we only support YT
    'onInitialize': function (options) {
        // Add here additional things to do when loading a VideoTile
        this.$el.addClass('wide');

        if (this.model.is('youtube')) {
            _.extend(this.model.attributes, {
                'thumbnail': 'http://i.ytimg.com/vi/' + this.model.get('original-id') +
                    '/hqdefault.jpg'
            });
        }

        // Determine which click handler to use; determined by the
        // content type.
        var handler = _.capitalize(this.model.get('content-type'));
        this.onClick = this['on' + handler] || this.onVideo;
    },

    'onYoutube': function (ev) {
        // Renders a YouTube video in the tile
        "use strict";
        var thumbId = 'thumb-' + this.cid,
            $thumb = this.$('div.thumbnail'),
            self = this;

        if (typeof window.YT === 'undefined') {
            window.open(this.model.get('original-url'));
            return;
        }

        $thumb.attr('id', thumbId).wrap('<div class="video-container" />');
        var player = new window.YT.Player(thumbId, {
            'width': $thumb.width(),
            'height': $thumb.height(),
            'videoId': this.model.attributes['original-id'] || this.model.id,
            'playerVars': {
                'autoplay': 1,
                'controls': SecondFunnel.observables.mobile()
            },
            'events': {
                'onReady': $.noop,
                'onStateChange': function (newState) {
                    SecondFunnel.tracker.videoStateChange(
                        self.model.attributes['original-id'] || self.model.id,
                        newState
                    );
                    switch (newState) {
                    case window.YT.PlayerState.ENDED:
                        self.onPlaybackEnd();
                        break;
                    default:
                        break;
                    }
                },
                'onError': $.noop
            }
        });
    },

    'onVideo': function () {
        // TODO: Possible support for native video files?
        // Pass for now
    },

    'onPlaybackEnd': function (ev) {
        SecondFunnel.vent.trigger("videoEnded", ev, this);
    }
});

var SocialButtons = Backbone.Marionette.View.extend({
    // Acts as a manager for the social buttons; allows us to create arbitrary
    // social buttons.

    // override the template by passing it in: new SocialButtons({ template: ... })
    // template can be a selector or a function(json) ->  <_.template>
    'tagName': 'span',
    'showCount': SecondFunnel.option('showCount', true),
    'buttonTypes': SecondFunnel.option('socialButtons',
        ['facebook', 'twitter', 'pinterest']), // @override via constructor

    'initSocial': _.once(function () {
        // Only initialize the social aspects once; this load the FB script
        // and twitter handlers.
        if (window.FB && _.contains(this.buttonTypes, "facebook")) {
            window.FB.init({
                cookie: true,
                status: false, // No AppID
                xfbml: true
            });
        }

        if (window.twttr && window.twttr.widgets &&
            _.contains(this.buttonTypes, "twitter")) {
            window.twttr.widgets.load();
            window.twttr.ready(function (twttr) {
                twttr.events.bind('tweet', function (event) {
                    // TODO: actual tracking
                    SecondFunnel.tracker.registerEvent({
                        "network": "Twitter",
                        "type": "share",
                        "subtype": "shared"
                    });
                });

                twttr.events.bind('click', function (event) {
                    var sType;
                    if (event.region === "tweet") {
                        sType = "clicked";
                    } else if (event.region === "tweetcount") {
                        sType = "leftFor";
                    } else {
                        sType = event.region;
                    }

                    SecondFunnel.tracker.registerEvent({
                        "network": "Twitter",
                        "type": "share",
                        "subtype": sType
                    });
                });
            });
        }

        // pinterest does its own stuff - just include pinit.js.
        // however, if it is to be disabled, the div needs to go.
        // see 'render' of SocialButtons.
        return this;
    }),

    'initialize': function(options) {
        // Initializes the SocialButton CompositeView by determining what
        // social buttons to show and loading the initial config if necessary.
        var self = this;
        // Only load the social once
        this.initSocial();
        this.views = [];

        _.each(self.buttonTypes, function (type) {
            var count = options.showCount,
                button = null,
                template = "#" + type.toLowerCase() + "_social_button_template";
            if (!Backbone.Marionette.TemplateCache._exists(template)) {
                // TODO: What to do if social button template is missing?
                SecondFunnel.vent.trigger('log', "No social button template found for " + type);
                return false;
            }
            type = _.capitalize(type);
            switch (type) {
            case "Facebook":
                button = FacebookSocialButton;
                break;
            case "Twitter":
                button = TwitterSocialButton;
                break;
            case "Share":
                button = ShareSocialButton;
                break;
            default:
                button = SocialButtonView;
                break;
            }
            self.views.push(new button({
                'model': options.model,
                'template': template, 
                'showCount': self.showCount 
            }));
        });
    },

    'showCondition': function () {
        // @override to false under any condition you don't want buttons to show
        return true;
    },


    'load': function () {
        // Initialize each Social Button; lazy loading to improve
        // page load times.
        _.each(this.views, function (view) {
            view.load();
        });
        return this;
    },

    'render': function () {
        // Render each child view and append to master.
       var self = this;
        _.each(self.views, function (view) {
            view.render();
            self.$el.append(view.$el);
        });
        return this;
    }
});

var SocialButtonView = Backbone.Marionette.ItemView.extend({
    // Base object for Social buttons, when adding a new Social button, extend
    // from this class and modify as necessary.
    'events': {
        'click': function (ev) {
            ev.stopPropagation(); // you did not click below the button
        },
        'hover': function (/* this */) {
            if (!this.$el.hasClass('loaded')) {
                // TODO: load something... but hasn't everything been loaded?
                var derp;
            }
        }
    },

    'initialize': function (options) {
        // Assign attributes to the object
        _.extend(this, options);
    },

    'load': function () {
        // @override: subclasses should override this method
        return this;
    },

    'templateHelpers': function (/* this */) {  // or {k: v}
        //github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.view.md#viewtemplatehelpers

        // Template Helpers; add additional data to the data we're serializing to
        // render our template.
        var helpers = {},
            data = this.model.attributes,
            page = SecondFunnel.option('page', {}),
        // TODO: this will err on product.url if page.product is undefined
            product = data || page.product,
            image = page['stl-image'] || page['featured-image'] || data.image || data.url;

        helpers.url = encodeURIComponent(product.url || image);
        helpers.product = {
            'url': product.url
        };
        helpers.showCount = this.showCount;
        helpers.image = image;

        // Call the after template handler to allow subclasses to modify this
        // data
        return this.onTemplateHelpers ?
            this.onTemplateHelpers(helpers):
            helpers;
    },

    // 'triggers': { "click .facebook": "event1 event2" },
    // 'onBeforeRender': $.noop,
    'onRender': function () {
        // Hide this element when it's rendered.
        this.$el.parent().hide();
        this.$el = this.$el.children();
        this.setElement(this.$el);
    },
    // 'onDomRefresh': $.noop,
    // 'onBeforeClose': function () { return true; },
    // 'onClose': $.noop,
    'commas': false
});

var FacebookSocialButton = SocialButtonView.extend({
    // Subclass of the SocialButtonView for FaceBook Social Buttons.
    'load': function () {
        // Onload, render the button and remove the placeholder
        var facebookButton = this.$el;
        if (window.FB && window.FB.XFBML && facebookButton &&
            facebookButton.length >= 1) {
            if (!facebookButton.attr('id')) {
                // generate a unique id for this facebook button
                // so fb can parse it.
                var fbId = this.cid + '-fb';
                facebookButton.attr('id', fbId);

                // this makes 1 iframe request to fb per button regardless
                // so stretch out its loading by a second and make the
                // the page look less owned by the lag
                window.FB.XFBML.parse(facebookButton[0], function () {
                    facebookButton.find('.placeholder').remove();
                });
            }
        }
        return this;
    },

    'onRender': function () {
        // On load we want to add the class 'no-count' if
        // showCount is false.
        this.$el = this.$el.children();
        this.setElement(this.$el);
        if (!this.showCount) {
            this.$el.addClass('no-count');
        }
    },

    'onTemplateHelpers': function (helpers) {
        // Additional attributes to add to our template data. 
        var url = (helpers.product.url || helpers.image);
        if (url && url.indexOf("facebook") > -1) {
            url = "http://www.facebook.com/" + /(?:fbid=|http:\/\/www.facebook.com\/)(\d+)/.exec(url)[1];
        }
        helpers.url = url;
        return helpers;
    }
});

var TwitterSocialButton = SocialButtonView.extend({
    // Subclass of the SocialButtonView for Twitter Social Buttons.
    'load': function () {
        // Load the widget when called.
        try {
            window.twttr.widgets.load();
        } catch (err) {
            // do other things
        }
        return this;
    }
});

var ShareSocialButton = SocialButtonView.extend({
    // Subclass of SocialButtonView for triggering a Share popup
    'events': {
        'click': function (ev) {
            // Creates a new popup instead of the default action
            ev.stopPropagation();
            ev.preventDefault();
            var popup = new SharePopup({
                'url': this.options.url,
                'model': this.options.model,
                'showCount': this.options.showCount
            });
            popup.render();
        }
    },

    'onTemplateHelpers': function (helpers) {
        // Catch url for reference on click
        this.options.url = helpers.url;
        return helpers;
    }
});

var SharePopup = Backbone.Marionette.ItemView.extend({
    // Displays a popup that provides the viewer with a plethora of other
    // social share options as defined by the designer/developer.
    'tagName': "div",
    'className': "shareContainer previewContainer",
    'template': "#share_popup_template",
    'buttons': SecondFunnel.option('shareSocialButtons', []),

    'events': {
        'click .close, .mask': function (ev) {
            this.$el.fadeOut(100).remove();
            this.unbind();
            this.views = [];
        }
    },

    'initialize': function (options) {
        this.buttons = _.map(this.buttons, function (obj) {
            obj.url = _.template(obj.url, options);
            return obj;
        });
    },

    'templateHelpers': function () {
        return {
            'buttons': this.buttons
        };
    },

    'onRender': function () {
        this.$el.css({'display': "table"});
        $('body').append(this.$el.fadeIn(100));
    }
});

var Discovery = Backbone.Marionette.CompositeView.extend({
    // Manages the HTML/View of ALL the tiles on the page (our discovery area)
    // tagName: "div"
    'el': $(SecondFunnel.option('discoveryTarget')),
    'itemView': TileView,
    'collection': null,
    'loading': false,
    'lastScrollTop': 0,

    // prevent default appendHtml behaviour (append in batch)
    'appendHtml': $.noop,

    'initialize': function (options) {
        var self = this;
        // Initialize IntentRank; use as a seperate module to make changes easier.
        SecondFunnel.intentRank.initialize(options);
        // Black box Masonry (this will make migrating easier in the future)
        SecondFunnel.layoutEngine.initialize(this.$el,
            options);
        this.collection = new TileCollection();
        this.categories = new CategorySelector(options.categories || []);
        this.attachListeners();

        // If the collection has initial values, lay them out
        if (options.initialResults && options.initialResults.length > 0) {
            this.layoutResults(options.initialResults, undefined, function () {
                self.getTiles();
            });
        } else {
            // Load additional results and add them to our collection
            this.getTiles();
        }
    },

    'attachListeners': function () {
        // TODO: Find a better way than this...
        _.bindAll(this, 'pageScroll', 'toggleLoading',
            'layoutResults');
        $(window).scroll(this.pageScroll);

        // Vent Listeners
        SecondFunnel.vent.on("tileClicked", this.updateContentStream, this);
        SecondFunnel.vent.on('changeCampaign', this.categoryChanged, this);
        return this;
    },

    'getTiles': function (options, $tile) {
        if (!this.loading) {
            this.toggleLoading();
            options = options || {};
            options.type = options.type || 'campaign';
            SecondFunnel.intentRank.getResults(options,
                this.layoutResults, $tile);
        }
        return this;
    },

    'layoutResults': function (data, tile, callback) {
        var self = this,
            $fragment = $();
        callback = callback || this.toggleLoading;

        if (tile) {
            // Add any related products to our data
            data = tile.model.get('related-products').concat(data);
            // Prevent loading the same content again
            tile.model.set('related-products', []);
        }

        // Finally check if we still don't have anything
        if (data.length === 0) {
            return this.toggleLoading();
        }

        // If we have data to use.
        _.each(data, function (tileData) {
            // Create the new tiles using the data
            var tile = new Tile(tileData),
                img = tile.get('image'),
                view = tile.createView();

            self.collection.add(tile);
            $fragment = $fragment.add(view.$el);
        });

        if (tile) {
            SecondFunnel.layoutEngine.call('insert', $fragment, tile.$el,
                callback);
        } else {
            SecondFunnel.layoutEngine.call('append', $fragment,
                callback);
        }
        return this;
    },

    'filter': function (content, selector) {
        // Filter the content in the LayoutEngine based on the selector
        // passed.
        var filters = this.filters || [];
        filters = selector ? filters.concat(selector) : filters;

        _.each(filters, function (filter) {
            if (typeof filter === 'function') {
                content = _.filter(content, filter);
            }
        });
        return content;
    },

    'updateContentStream': function (ev, tile) {
        // Loads in related content below the specified tile
        var id = tile.model.get('tile-id');
        return id === null ? this :
               this.getTiles({
                   'type': "content",
                   'id': id
               }, tile);
    },

    'categoryChanged': function (ev, category) {
        // Changes the category (campaign) by refreshign IntentRank, clearing
        // the Layout Engine and collecting new tiles.
        var self = this;
        if (this.loading) {
            setTimeout(function () {
                self.categoryChanged(ev, category);
            }, 100);
        } else {
            SecondFunnel.intentRank.changeCategory(category.model.get('id'));
            SecondFunnel.layoutEngine.clear();
            return this.getTiles();
        }
        return this;
    },

    'toggleLoading': function (bool) {
        if (typeof bool === 'boolean') {
            this.loading = bool;
        } else {
            this.loading = !this.loading;
        }
        return this;
    },

    'pageScroll': function () {
        var pageBottomPos = $(window).innerHeight() + $(window).scrollTop(),
            documentBottomPos = $(document).height(),
            viewportHeights = $(window).innerHeight() * (SecondFunnel.option('prefetchHeight',
                1));

        if (pageBottomPos >= documentBottomPos - viewportHeights && !this.loading) {
            this.getTiles();
        }

        // detect scrolling detection. not used for anything yet.
        var st = $(window).scrollTop();
        if (st > this.lastScrollTop) {
            broadcast('scrollDown', this);
        } else {
            broadcast('scrollUp', this);
        }
        this.lastScrollTop = st;
    }
});


var Category = Backbone.Model.extend({
    // Base empty category, no functionality needed here
});

var CategoryView = Backbone.Marionette.ItemView.extend({
    'events': {
        'click': function (ev) {
            ev.preventDefault();
            SecondFunnel.vent.trigger('changeCampaign', ev, this);
        }
    },

    'initialize': function (options) {
        // Initializes the category view, expects some el to use
        this.el = options.el;
        this.$el = $(this.el);
        delete options.$el;
        this.model = new Category(options);
    }
});

var CategorySelector = Backbone.Marionette.CompositeView.extend({
    // This ItemView does not create an element, rather is passed
    // the element that it will use for category selection
    itemView: CategoryView,

    'initialize': function (categories) {
        // Initialize a category view for each object with a
        // data-category option.
        var views = [];
        $('[data-category]').each(function () {
            var id = $(this).attr('data-category');
            if (_.findWhere(categories, {'id': Number(id)})) {
                // Make sure category is a valid one.
                views.push(new CategoryView({
                    'id': id,
                    'el': this
                }));
            }
        });
        this.views = views;
    }
});


var PreviewContent = Backbone.Marionette.ItemView.extend({
    'template': '#tile_preview_template',
    'templates': function (currentView) {
        var defaultTemplateRules = [
            // supported contexts: options, data
            '#<%= options.store.name %>_<%= data.template %>_mobile_preview_template',
            '#<%= options.store.name %>_<%= data.template %>_preview_template',
            '#<%= data.template %>_mobile_preview_template',
            '#<%= data.template %>_preview_template',
            '#tile_mobile_preview_template', // fallback
            '#tile_preview_template' // fallback
        ];

        if (!SecondFunnel.observables.mobile()) {
            // remove mobile templates if it isn't mobile, since they take
            // higher precedence by default
            defaultTemplateRules = _.reject(defaultTemplateRules,
                function (t) {
                    return t.indexOf('mobile') >= 0;
                });
        }
        return defaultTemplateRules;
    },
    'onRender': function () {
        // ItemViews don't have regions - have to do it manually
        if (!(SecondFunnel.observables.touch() || SecondFunnel.observables.mobile())) {
            var buttons = new SocialButtons({model: this.model}).render().load().$el;
            this.$('.social-buttons').append(buttons);
        }
    }
});


var PreviewWindow = Backbone.Marionette.Layout.extend({
    'tagName': "div",
    'className': "previewContainer",
    'template': "#preview_container_template",
    'events': {
        'click .close, .mask': function () {
            this.$el.fadeOut(SecondFunnel.option('previewAnimationDuration')).remove();
        }
    },
    'regions': {
        'content': '.template.target',
        'socialButtons': '.social-buttons'
    },
    'onBeforeRender': function () {
    },
    'templateHelpers': function () {
        // return {data: $.extend({}, this.options, {template: this.template})};
    },
    'onRender': function () {
        this.$el.css({display: "table"});
        $('body').append(this.$el.fadeIn(SecondFunnel.option('previewAnimationDuration')));
    }
});


var TapIndicator = Backbone.Marionette.ItemView.extend({
    'template': "#tap_indicator_template",
    'className': 'tap_indicator animated fadeIn',
    'onBeforeRender': function () {
        // http://jsperf.com/hasclass-vs-toggleclass
        // toggleClass with a boolean is 55% slower than manual checks
        if (SecondFunnel.observables.touch()) {
            $('html').addClass('touch-enabled');
        } else {
            $('html').removeClass('touch-enabled');
        }
    }
});


var EventManager = Backbone.View.extend({
    // Top-level event binding wrapper. all events bubble up to this level.
    // the theme can declare as many event handlers as they like by creating
    // their own new EventManager({ event: handler, event: ... })s.
    'el': $(window).add($(document)),
    'initialize': function (bindings) {
        var self = this;
        _.each(bindings, function (func, key, l) {
            var event = key.substr(0, key.indexOf(' ')),
                selectors = key.substr(key.indexOf(' ') + 1);
            self.$el.on(event, selectors, func);
            if (SecondFunnel.option('debug', false)) {
                console.log('regEvent ' + key);
            }
        });
    }
});


var broadcast = function () {
    // alias for vent.trigger with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (SecondFunnel.option('debug') > 1) {
        console.log('Broadcasting "' + arguments[0] + '" with args=%O', pArgs);
    }
    SecondFunnel.vent.trigger.apply(SecondFunnel, arguments);
    if (window.Willet && Willet.mediator) {  // to each his own
        Willet.mediator.fire(arguments[0], pArgs);
    }
};


SecondFunnel.addInitializer(function (options) {
    // JQuery Special event to listen to delete
    // stackoverflow.com/questions/2200494
    // does not work with jQuery UI
    // does not work when affected by html(), replace(), replaceWith(), ...
    var ev = new $.Event('remove'),
        orig = $.fn.remove;
    $.fn.remove = function () {
        $(this).trigger(ev);
        return orig.apply(this, arguments);
    };

    $.fn.getClasses = $.fn.getClasses || function () {
        // random helper. get an element's list of classes.
        // example output: ['facebook', 'button']
        return _.compact($(this).attr('class').split(' ').map($.trim));
    };

    // underscore's fancy pants capitalize()
    _.mixin({
        'capitalize': function (string) {
            return string.charAt(0).toUpperCase() + string.substring(1).toLowerCase();
        }
    });
});

// Add SecondFunnel component(s)
SecondFunnel.addInitializer(function (options) {
    window.SecondFunnel = SecondFunnel;

    SecondFunnel.getModifiedTemplateName = function (name) {
        return name.replace(/(styld[\.\-]by|tumblr|pinterest|facebook|instagram)/i,
            'image');
    };
});

SecondFunnel.addInitializer(function (options) {
    // delegated analytics bindings
    var defaults = new EventManager(SecondFunnel.tracker.defaultEventMap),
        customs = new EventManager(options.events);
});

SecondFunnel.addInitializer(function (options) {
    if (SecondFunnel.option('debug', false) > 5) {
        $(document).ready(function () {
            // don't use getScript, firebug needs to know its src path
            // and getScript removes the tag so firebug doesn't know what to do
            var tag = document.createElement('script');
            tag.src = "https://getfirebug.com/firebug-lite.js";

            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        });
    }
});

SecondFunnel.addInitializer(function (options) {
    try {
        var fa = new FeaturedAreaView;
        fa.render();
        broadcast('featureAreaRendered', fa);
    } catch (err) {
        // marionette throws an error if no hero templates are found or needed.
        // it is safe to ignore it.
        broadcast('featureAreaNotRendered');
    }
});

SecondFunnel.addInitializer(function (options) {
    // Add our initializer, this allows us to pass a series of tiles
    // to be displayed immediately (and first) on the landing page.
    broadcast('beforeInit');
    SecondFunnel.discovery = new Discovery(options);
    SecondFunnel.tracker.init();
    broadcast('finished');
});
