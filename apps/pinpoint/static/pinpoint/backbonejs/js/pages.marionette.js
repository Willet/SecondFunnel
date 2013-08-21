// JQuery Special event to listen to delete
$(function () {
    // stackoverflow.com/questions/2200494
    // does not work with jQuery UI
    // does not work when affected by html(), replace(), replaceWith(), ...
    var ev = new $.Event('remove'),
        orig = $.fn.remove;
    $.fn.remove = function () { 
        $(this).trigger(ev);
        return orig.apply(this, arguments);
    };
});


// Marionette TemplateCache extension to allow checking cache for template
Backbone.Marionette.TemplateCache._exists = function (templateId) {
    // Checks if the Template exists in the cache, if not found
    // updates the cache with the template (if it exists), otherwise fail
    // returns true if exists otherwise false.
    var cached = this.templateCaches[templateId];

    if (cached) {
        return true;
    }

    // template exists but was not cached
    var cachedTemplate = new Backbone.Marionette.TemplateCache(templateId);
    try {
        cachedTemplate.load();
        // Only cache on success
        this.templateCaches[templateId] = cachedTemplate;
    } catch (err) {
        if (!(err.name && err.name == "NoTemplateError")) {
            throw(err);
        }
    }
    return !!this.templateCaches[templateId];
};

// Accept an arbitrary number of template selectors instead of just one.
// function will return in a short-circuit manner once a template is found.
Backbone.Marionette.View.prototype.getTemplate = function () {
    "use strict";
    var i, templateIDs = Backbone.Marionette.getOption(this, "templates"),
        template = Backbone.Marionette.getOption(this, "template"),
        temp, templateExists;

    if (templateIDs) {
        for (i = 0; i < templateIDs.length; i++) {
            temp = _.template(templateIDs[i], {
                'data': Backbone.Marionette.getOption(this, "model").attributes
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


// TODO: Seperate this into modules/seperate files
// Declaration of the SecondFunnel JS application
var SecondFunnel = new Backbone.Marionette.Application();
window.SecondFunnel = SecondFunnel;
// Custom event trigger/listener
SecondFunnel.vent = _.extend({}, Backbone.Events);

var Tile = Backbone.Model.extend({
    defaults: {
        // Default product tile settings, some tiles don't
        // come specifying a type or caption
        'caption': "I don't even",
        'tile-id': 0,
        'content-type': "product"
    },

    initialize: function (data) {
        for (var key in data) {
            this.set(key, data[key]);
        }
    },

    getType: function () {
        // Get the content type of this tile
        return this.attributes['content-type'].toLowerCase();
    },

    isProduct: function () {
        return this.getType() == 'product';
    },

    getId: function () {
        // Get the ID of this tile (for DB queries)
        return this.attributes['tile-id'];
    }
});

var LayoutEngine = Backbone.Model.extend({
    // Our layoutEngine, acts as a BlackBox for whatever we're using
    selector: PAGES_INFO.discoveryItemSelector,
    options: {
        itemSelector: PAGES_INFO.discoveryItemSelector,
        isResizeBound: true,
        visibleStyle: {
            'opacity': 1,
            'webkit-transform': 'none'
        },
        isAnimated: true,
        columnWidth: PAGES_INFO.columnWidth(),
        transitionDuration: PAGES_INFO.masonryAnimationDuration + 's'
    },

    initialize: function ($elem, options) {
        _.extend(this, {'options': options });
        $elem.masonry(this.options).masonry('bindResize');
        this.$el = $elem;
    },

    call: function (callback, $fragment) {
        if (!(typeof callback === 'string' && callback in this)) {
            var msg = !(typeof callback === 'string')? "Unsupported type " + (typeof callback) +
                    " passed to Layout Engine." :
                    "LayoutEngine has no property " + callback + ".";
            SecondFunnel.vent.trigger('log', msg);
            return undefined;
        }
        var args = Array.prototype.slice.apply(arguments);
        args = args.slice(2);
        args.unshift(this[callback], $fragment);

        return this.imagesLoaded.apply(this, args);
    },

    append: function ($fragment, callback) {
        //$fragment.appendTo(this.$el).hide();
        this.reload();
        return callback? callback($fragment) : this;
    },

    reload: function ($fragment) {
        this.$el.masonry('reloadItems');
        this.$el.masonry();
        return this;
    },

    insert: function ($target, $fragment, callback) {
        $fragment.insertAfter($target);
        this.reload();
        return callback? callback($fragment) : this;
    },

    imagesLoaded: function (callback, $fragment) {
        // Calls the broken handler to remove broken images as they appear;
        // when all images are loaded, calls the appropriate layout function
        var self = this,
            args = Array.prototype.slice.apply(arguments),
            imgLoad = imagesLoaded($fragment.children(':not(iframe) > img'));
        // Remove broken images as they appear
        imgLoad.on('progress', function (instance, image) {
            var $img = $(image.img),
                $elem = $img.parents(self.selector);

            if ( !image.isLoaded ) {
                $img.remove();
            } else {
                // Append to container and called appended
                self.$el.append($elem).masonry('appended', $elem);
            }
        }).on('always', function () {
            // When all images are loaded, show the non-broken ones and reload
            args = args.slice(1);
            callback.apply(self, args);
        });
        return this;
    }
});

var IntentRank = Backbone.Model.extend({
    // intentRank module
    base: "http://intentrank-test.elasticbeanstalk.com/intentrank",
    templates: {
        'campaign': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/getresults",
        'content': "<%=url%>/store/<%=store.name%>/campaign/<%=campaign%>/content/<%=id%>/getresults"
    },
    store: PAGES_INFO.store,
    campaign: PAGES_INFO.campaign,

    getResults: function (options, callback) {
        var uri = _.template(this.templates[options.type],
                _.extend({}, options, this, {
                    'url': this.base
                })),
            args = Array.prototype.slice.apply(arguments);
        args = args.length > 2 ? args.slice(2) : [];

        $.ajax({
            url: uri,
            data: {
                'results': 10 // TODO: Should be calculated somehow
            },
            contentType: "json",
            dataType: 'jsonp',
            timeout: 5000,
            success: function (results) {
                args.unshift(results);
                return callback.apply(callback, args);
            },
            error: function (jxqhr, textStatus, error) {
                args.unshift([]);
                return callback.apply(callback, args);
            }
        });
    }
});

var TileCollection = Backbone.Collection.extend({
    // Our TileCollection manages ALL the tiles on the page.
    model: function (attrs) {
        var SubClass = 'Tile';
        if (window[SubClass]) {
            return new window[SubClass](attrs);
        }
        return new Tile(attrs);  // base class
    },
    loading: false,
    totalItems: null,

    initialize: function (arrayOfData) {
        // Our TileCollection starts by rendering several Tiles using the
        // data it is passed.
        for (var data in arrayOfData) {
            // Generate Tile
            this.add(new Tile(data));
        }
    }
});

var TileView = Backbone.Marionette.Layout.extend({
    // Manages the HTML/View of a SINGLE tile on the page (single pinpoint block)
    tagName: "div", // TODO: Should this be a setting?
    template: "#product_tile_template",
    className: PAGES_INFO.discoveryItemSelector.substring(1),

    events: {
        'click': "onClick",
        'mouseenter': "onHover",
        "mouseleave": "onHover"
    },

    'regions': {
        'socialButtons': '.social-buttons'
    },

    initialize: function (options) {
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

        if (this.model.getType() === 'youtube') {
            _.extend(this.model.attributes, {
                'thumbnail': 'http://i.ytimg.com/vi/' + data['original-id'] +
                    '/hqdefault.jpg'
            });
            this.$el.addClass('wide');
        }

        _.bindAll(this, 'close');
        // If the tile model is removed, remove the DOM element
        this.listenTo(this.model, 'destroy', this.close);
    },

    renderVideo: function () {
        // Renders a YouTube video in the tile
        var thumbId = 'thumb' + this.cid,
            $thumb = this.$('div.thumbnail');
        $thumb.attr('id', thumbId).wrap('<div class="video-container" />');

        var player = new YT.Player(thumbId, {
            width: $thumb.width(),
            height: $thumb.height(),
            videoId: this.model.attributes['original-id'] || this.model.id,
            playerVars: {
                'autoplay': 1,
                'controls': 0
            },
            events: {
                'onReady': $.noop,
                'onStateChanges': this.onVideoEnd,
                'onError': $.noop
            }
        });

    },

    close: function () {
        // As it stands, since we aren't using a REST API, we don't store
        // the models anywhere so we don't need to destroy them.
        // Remove view and unbind listeners
        this.$el.remove();
        this.unbind();
        this.views = [];
    },

    onHover: function (ev) {
        // Trigger tile hover event with event and tile
        SecondFunnel.vent.trigger("tileHover", ev, this);
        if (this.socialButtons) {
            var inOrOut = (ev.type === 'mouseenter') ? 'fadeIn': 'fadeOut';
            this.socialButtons.$el[inOrOut](200);

            var facebookButton = this.socialButtons.$el.find('.facebook');
            if (window.FB.XFBML && facebookButton && facebookButton.length >= 1) {
                if (!facebookButton.attr('id')) {
                    // generate a unique id for this facebook button
                    // so fb can parse it.
                    var fbId = this.socialButtons.currentView.cid + '-fb';
                    facebookButton.attr('id', fbId);
                    window.FB.XFBML.parse(fbId);
                }
            }
        }
    },

    onClick: function (ev) {
        "use strict";
        if (this.model.getType() === 'youtube') {
            this.renderVideo();
        } else {
            var tile = this.model,
                preview = new PreviewWindow({'model': tile});
            preview.render();
            preview.content.show(new PreviewContent({'model': tile}));
        }
        SecondFunnel.vent.trigger("tileClicked", this);
    },

    'onRender': function () {
        // Listen for the image being removed from the DOM, if it is, remove
        // the View/Model to free memory
        this.$("img").on('remove', this.close);
        this.socialButtons.show(new SocialButtons());
    },

    onVideoEnd: function (ev) {
        SecondFunnel.vent.trigger("videoEnded", ev, this);
    }
});

var SocialButtons = Backbone.Marionette.ItemView.extend({
    // override the template by passing it in: new SocialButtons({ template: ... })
    // template can be a selector or a function(json) ->  <_.template>
    'template': '#social_buttons_template',
    'buttonsTypes': ['facebook', 'twitter', 'pinterest'],  // required to support
    // 'model': undefined,  // auto-serialization of constructor(obj)
    // 'collection': undefined,  // auto-serialization of constructor([obj])
    // 'tagName': "div",
    // 'className': 'social-buttons',  // default: empty div
    // getTemplate: function (/* this */) { return '#<template>'; },
    'initialize': _.once(function (noop) {
        if (window.FB) {
            window.FB.init({
                cookie: true,
                status: true,
                xfbml: true
            });
        }

        window.twttr.widgets.load();
        window.twttr.ready(function (twttr) {
            twttr.events.bind('tweet', function(event) {
                // TODO: actual tracking
                /*pagesTracking.registerEvent({
                    "network": "Twitter",
                    "type": "share",
                    "subtype": "shared"
                });*/
            });

            twttr.events.bind('click', function(event) {
                var sType;
                if (event.region === "tweet") {
                    sType = "clicked";
                } else if (event.region === "tweetcount") {
                    sType = "leftFor";
                } else {
                    sType = event.region;
                }

                // TODO: actual tracking
                /*pagesTracking.registerEvent({
                    "network": "Twitter",
                    "type": "share",
                    "subtype": sType
                });*/
            });
        });

        // pinterest does its own stuff - just include pinit.js
    }),
    'ui': {
        'facebook': "div.facebook",
        'twitter': "div.twitter",
        'pinterest': "div.pinterest"
    },
    'events': {
        'click .facebook': function (/* this */) {
            alert('wtf');
        },
        'hover': function (/* this */) {
            if (!this.$el.hasClass('loaded')) {
                // TODO: load something... but hasn't everything been loaded?
            }
        }
    },
    // 'triggers': { "click .facebook": "event1 event2" },
    // 'onBeforeRender': $.noop,
    'onRender': function () {
        this.$el.parent().hide();
    },
    // 'onDomRefresh': $.noop,
    // 'onBeforeClose': function () { return true; },
    // 'onClose': $.noop,
    'commas': false
});

var Discovery = Backbone.Marionette.CompositeView.extend({
    // Manages the HTML/View of ALL the tiles on the page (our discovery area)
    // tagName: "div"
    el: $(PAGES_INFO.discoveryTarget),
    itemView: TileView,
    intentRank: null,
    collection: null,
    layoutEngine: null,
    loading: false,

    // prevent default appendHtml behaviour (append in batch)
    'appendHtml': $.noop,

    initialize: function (options) {
        // Initialize IntentRank; use as a seperate module to make changes easier.
        SecondFunnel.intentRank = new IntentRank;
        // Black box Masonry (this will make migrating easier in the future)
        SecondFunnel.layoutEngine = new LayoutEngine(this.$el,
            options.masonry);

        this.collection = options.collection || new TileCollection;
        // Load additional results and add them to our collection
        this.attachListeners().getTiles();
    },

    attachListeners: function () {
        // Attach our listeners that can't be handled through events
        _.bindAll(this, 'pageScroll');
        $(window).scroll(this.pageScroll);

        // TODO: Find a better way than this...
        _.bindAll(this, 'toggleLoading', 'layoutResults',
            'updateContentStream');

        // Vent Listeners
        SecondFunnel.vent.on("tileClicked", this.updateContentStream);

        return this;
    },

    getTiles: function (options, $tile) {
        if (!this.loading) {
            this.toggleLoading();
            options = options || {};
            options.type = options.type || 'campaign';
            SecondFunnel.intentRank.getResults(options, 
                this.layoutResults, $tile);
        }
        return this;
    },

    layoutResults: function (data, $tile) {
        var self = this,
            start = self.collection.length,
            $fragment = $();

        _.each(data, function (tileData) {
            // Create the new tiles using the data
            var tile = new Tile(tileData),
                view = new TileView({model: tile});

            self.collection.add(tile);

            view.render();
            $fragment = $fragment.add(view.$el);
        });

        if ($fragment.length > 0) {
            if ($tile) {
                SecondFunnel.layoutEngine.call('insert', $fragment, $tile,
                    this.toggleLoading);
            } else {
                SecondFunnel.layoutEngine.call('append', $fragment,
                    this.toggleLoading);
            }
        } else {
            // Empty results, just toggle loading.
            this.toggleLoading();
        }
        return this;
    },

    updateContentStream: function (tile) {
        return this.getTiles({
            'type': "content",
            'id': tile.model.getId()
        }, tile.$el);
    },

    toggleLoading: function (self) {
        this.loading = !this.loading;
        return this;
    },

    pageScroll: function () {
        var pageBottomPos = $(window).innerHeight() + $(window).scrollTop(),
            documentBottomPos = $(document).height();

        if (pageBottomPos >= documentBottomPos - 500 && !this.loading) {
            this.getTiles();
        }
    }
});


var PreviewContent = Backbone.Marionette.ItemView.extend({
    'template': '#tile_preview_template',
    'templates': [
        '#<%= data.template %>_preview_template',  // but what's 'this'?
        '#tile_preview_template' // fallback
    ]
});


var PreviewWindow = Backbone.Marionette.Layout.extend({
    'tagName': "div",
    'className': "previewContainer",
    'template': "#preview_container_template",
    'events': {
        'click .close, .mask': function () {
            this.$el.fadeOut(PAGES_INFO.previewAnimationDuration).remove();
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
        this.socialButtons.show(new SocialButtons());
        $('body').append(this.$el.fadeIn(PAGES_INFO.previewAnimationDuration));
    }
});

function syntaxHighlight(json) {
    // something about internets http://stackoverflow.com/a/7220510/1558430
    if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 2);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g,
        '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
}

$(function () {
    // Add SecondFunnel component(s)
    SecondFunnel.addInitializer(function (options) {
        // Add our initiliazer, this allows us to pass a series of tiles
        // to be displayed immediately (and first) on the landing page.
        SecondFunnel.discovery = new Discovery({});
    });

    // Start the SecondFunnel app
    SecondFunnel.start(PAGES_INFO);
});
