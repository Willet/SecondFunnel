/*global Image, Marionette, setTimeout, imagesLoaded, Backbone, jQuery, $, _,
console */
var SecondFunnel = new Marionette.Application(),
    broadcast,
    receive,
    debugOp,
    ev = new $.Event('remove'),
    orig = $.fn.remove;

SecondFunnel.options = window.PAGES_INFO || window.TEST_PAGE_DATA || {};

(function (details) {
    var pubDate;
    if (details && details.page && details.page.pubDate) {
        pubDate = details.page.pubDate;
    }

    // feature, not a bug
    if (window.console && console.log) {
        console.log("%cSecondFunnel", "font-family:sans-serif; font-size:32pt;");
        console.log('Published ' + pubDate);
    }
}(SecondFunnel.options));

// A ?debug value of > 1 will leak memory, and should not be used as reference
// heap sizes on production. ibm.com/developerworks/library/wa-jsmemory/#N101B0
(function (console, level, hash) {
    var hashIdx = hash.indexOf('debug=');
    try {
        // console logging thresholds
        SecondFunnel.QUIET = 0;
        SecondFunnel.ERROR = 1;
        SecondFunnel.WARNING = 2;
        SecondFunnel.LOG = 3;
        SecondFunnel.VERBOSE = 4;
        SecondFunnel.ALL = 5;

        // patch all console methods individually.
        console.debug = console.debug || $.noop;
        console.log = console.log || $.noop;
        console.warn = console.warn || $.noop;
        console.error = console.error || $.noop;

        if (window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1') {
            level = SecondFunnel.options.debug = SecondFunnel.ERROR;
        }

        if (hashIdx > -1) {
            level = SecondFunnel.options.debug = hash[hashIdx + 6];
        }

        // remove console functions depending on desired debug threshold.
        if (level < SecondFunnel.ERROR) {
            console.error = $.noop;
        }

        if (level < SecondFunnel.WARNING) {
            console.warn = $.noop;
        }

        if (level < SecondFunnel.LOG) {
            console.log = $.noop;
        }

        if (level < SecondFunnel.VERBOSE) {
            console.debug = $.noop;
        }
    } catch (e) {
        // this is an optional operation. never let this stop the script.
    }
}(window.console = window.console || {},
  SecondFunnel.options.debug,
  window.location.hash + window.location.search));

// http://stackoverflow.com/questions/1199352/
String.prototype.truncate = function (n, useSentenceBoundary, addEllipses) {
    var tooLong = this.length > n,
        s = tooLong ? this.substr(0, n) : this;
    if (tooLong && useSentenceBoundary && s.lastIndexOf('. ') > -1) {
        s = s.substr(0, s.lastIndexOf('. ') + 1);
    }
    if (tooLong && addEllipses) {
        s = s.substr(0, s.length - 3) + '...';
    }
    return s;
};

// JQuery Special event to listen to delete
// stackoverflow.com/questions/2200494
// does not work with jQuery UI
// does not work when affected by html(), replace(), replaceWith(), ...
$.fn.remove = function () {
    $(this).trigger(ev);
    if (orig) {
        return orig.apply(this, arguments);
    } else {
        return $(this);
    }
};

/**
 * @param {function} callback
 */
$.fn.scrollStopped = function (callback) {
    // stackoverflow.com/a/14035162/1558430
    $(this).scroll(function () {
        var self = this, $this = $(self);
        if ($this.data('scrollTimeout')) {
            clearTimeout($this.data('scrollTimeout'));
        }
        if (callback) {
            $this.data('scrollTimeout', setTimeout(callback, 500, self));
        }
    });
};

/**
 * Hides this page element, then shows another page element in place.
 * This is very similar to what JQM does.
 *
 * @param showWhich {jQuery}   selected page
 * @returns {jQuery}
 */
$.fn.swapWith = function (showWhich) {
    showWhich.css('display', showWhich.data('display') || 'block');
    this.data('offset', $(window).scrollTop()).css('display', 'none');
    $(window).scrollTop(showWhich.data('offset') || 0);

    return this;
};

$.fn.getClasses = $.fn.getClasses || function () {
    // random helper. get an element's list of classes.
    // example output: ['facebook', 'button']
    return _.compact(_.map($(this).attr('class').split(' '), $.trim));
};

$.getScripts = function (urls, callback, options) {
    // batch getScript with caching
    // callback receives as many ajax xhr objects as the number of urls.

    // like getScript, this function is incompatible with scripts relying on
    // its own tag existing on the page (e.g. firebug, facebook jssdk)
    var calls = _.map(urls, function (url) {
        var options = $.extend(options || {}, {
            'dataType': 'script',
            'crossDomain': true,
            'cache': true,
            'url': url
        });
        return $.ajax(options);
    });
    $.when.apply($, calls).done(callback, function () {
        broadcast('deferredScriptsLoaded', urls);
    });
};

// http://www.foliotek.com/devblog/getting-the-width-of-a-hidden-element-with-jquery-using-width/
// get element sizes while they are hidden / being they are appended
$.fn.getHiddenDimensions = function (includeMargin) {
    /*ignore jslint start*/
    var $item = this,
        props = { position: 'absolute', visibility: 'hidden', display: 'block' },
        dim = { width: 0, height: 0, innerWidth: 0, innerHeight: 0, outerWidth: 0, outerHeight: 0 },
        $hiddenParents = $item.parents().andSelf().not(':visible'),
        includeMargin = (includeMargin == null) ? false : includeMargin;

    var oldProps = [];
    $hiddenParents.each(function () {
        var old = {};

        for (var prop in props) {
            old[prop] = this.style[prop];
            this.style[prop] = props[prop];
        }

        oldProps.push(old);
    });

    dim.width = $item.width();
    dim.outerWidth = $item.outerWidth(includeMargin);
    dim.innerWidth = $item.innerWidth();
    dim.height = $item.height();
    dim.innerHeight = $item.innerHeight();
    dim.outerHeight = $item.outerHeight(includeMargin);

    $hiddenParents.each(function (i) {
        var old = oldProps[i];
        for (var name in props) {
            this.style[name] = old[name];
        }
    });

    return dim;
    /*ignore jslint end*/
};

// underscore's fancy pants capitalize()
_.mixin({
    'capitalize': function (string) {
        var str = string || "";
        return str.charAt(0).toUpperCase() + str.substring(1);
    },
    'get': function (obj, key, defaultValue) {
        // thin wrapper around obj key access that never throws an error.
        try {
            var val = obj[key];
            if (val !== undefined) {
                return obj[key];
            }
        } catch (err) {
            // default
        }
        return defaultValue;
    },
    'getKeyByValue': function (obj, value) {
        // reverse key search. There is no native function for this.
        var prop;
        for(prop in obj) {
            if(obj.hasOwnProperty(prop)) {
                 if(obj[prop] === value) {
                     return prop;
                 }
            }
        }
    },
    'sortByAssoc': function (obj, attrib) {
        // see sortBy; returns a list
    }
});

(function (views) {
    /**
     * View's render() is a noop. It won't trigger a NoTemplateError
     * like other Views do. Here's a patch.
     * @returns {*}
     */
    Marionette.View.prototype.render = function () {
        function throwError(message, name) {
            var error = new Error(message);
            error.name = name || 'Error';
            throw error;
        }
        if (!$(this.template).length) {
            throwError(this.template, "NoTemplateError");
        }

        // default functionality: $.noop()

        return this;
    };

    // patch render to always run widgets.
    _.each(views, function (ViewClass) {
        var oldRender = ViewClass.prototype.render || $.noop;
        ViewClass.prototype.render = function () {
            var result;
            try {
                // call the original function
                result = oldRender.apply(this, arguments);  // usually 'this'

                // do something else
                SecondFunnel.utils.runWidgets(this);

            } catch (err) {
                // failed... close the view
                broadcast('viewRenderError', err, this);

                // If template not found signal error in rendering view.
                if (err.name &&  err.name === "NoTemplateError") {
                    console.warn("Could not find template " +
                                 this.template + ". View did not render.");
                    // Trigger methods
                    this.isClosed = true;
                    // .triggerMethod only triggers methods defined in prototype
                    this.triggerMethod("missing:template");
                } else {
                    this.triggerMethod("render:error", err);
                }

                this.close();
            }

            // return the return of the original function, pretend nothing happened
            return result;
        };
    });
}([Marionette.View, Marionette.CompositeView, Marionette.ItemView]));

broadcast = function (eventName) {
    // alias for vent.trigger with a clear intent that the event triggered
    // is NOT used by internal code (pages.js).
    // calling method: (eventName, other stuff)
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    console.debug('Broadcasting "' + eventName + '" with args=%O', pArgs);
    SecondFunnel.vent.trigger.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.fire(eventName, pArgs);
    }
};

/**
 * alias for vent.on with a clear intent that the event triggered
 * is NOT used by internal code (pages.js).
 * calling method: (eventName, other stuff)
 */
receive = function (eventName) {
    var pArgs = Array.prototype.slice.call(arguments, 1);
    if (!window.SecondFunnel) {
        return;  // SecondFunnel not initialized yet
    }
    console.debug('Received "' + eventName + '" with args=%O', pArgs);
    SecondFunnel.vent.on.apply(SecondFunnel.vent, arguments);
    if (window.Willet && window.Willet.mediator) {  // to each his own
        Willet.mediator.on(eventName, pArgs);
    }
};

/**
 * similar usage as $.noop
 */
debugOp = function () {
    console.debug('%O, %O', this, arguments);
};
