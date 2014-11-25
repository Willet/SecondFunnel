'use strict';
/**
 * @module jQuery Extensions
 *
 * Patches $ object
 *
 */
module.exports = function (module, App, Backhone, Marionette, $, _) {

    // Needed for updated remove func
    var ev = new $.Event('remove'),
        orig = $.fn.remove;
    var extendFns = {
        'remove': function () {
            // JQuery Special event to listen to delete
            // stackoverflow.com/questions/2200494
            // does not work with jQuery UI
            // does not work when affected by html(), replace(), replaceWith(), ...
            $(this).trigger(ev);
            if (orig) {
                return orig.apply(this, arguments);
            } else {
                return $(this);
            }
        },
        'scrollStopped': function (callback) {
            /**
             * @param {function} callback
             */
            // stackoverflow.com/a/14035162/1558430
            $(this).scroll(function () {
                var self = this, $this = $(self);
                if ($this.data('scrollTimeout')) {
                    clearTimeout($this.data('scrollTimeout'));
                }
                if (callback) {
                    $this.data('scrollTimeout', setTimeout(callback, 60, self));
                }
            });
            return $(this);
        },
        'swapWith': function (showWhich) {
            /**
             * Hides this page element, then shows another page element in place.
             * This is very similar to what JQM does.
             *
             * @param showWhich {jQuery}   selected page
             * @returns {jQuery}
             */
            showWhich.css('display', showWhich.data('display') || 'block');
            $(this).data('offset', $(window).scrollTop()).css('display', 'none');
            $(window).scrollTop(showWhich.data('offset') || 0);

            return $(this);
        },
        'getScripts': function (urls, callback, options) {
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
                App.vent.trigger('deferredScriptsLoaded', urls);
            });
        }
    };

    if (!$.fn.tile ) {
        extendFns['tile'] = function () {
            /**
             * Retrieve the first selected element's TileView and Tile, if applicable.
             * Applicability largely depends on whether or not you had selected a tile.
             *
             * Due to aggressive garbage collection, these two calls may not succeed.
             * If selector did not find a tile, returns an object with undefined values.
             *
             * @return {Object}
             *
             * @type {Function}
             */
            var props = {},
                cid = this.attr('id');

            if (!(this.hasClass('tile') && cid)) {
                return props;
            }

            try {
                props.view = App.discoveryArea.currentView.children
                    .findByModelCid(cid);
                // props.model = props.view.model;  // not always
            } catch (err) { }

            try {
                props.model = _.findWhere(App.discovery.collection.models,
                    {'cid': cid});

                // these can be undefined.
                props.type = props.model.get('type');
                props.template = props.model.get('template');
            } catch (err) { }

            return props;
        };
    }

    if (!$.fn.getClasses) {
        extendFns['getClasses'] = function () {
            // random helper. get an element's list of classes.
            // example output: ['facebook', 'button']
            return _.compact(_.map($(this).attr('class').split(' '), $.trim));
        };
    }

    // Extend jQuery object
    $.fn.extend(extendFns);

    $.support.cors = true;
    /**
     * Special jQuery listener for rotation events.  A rotation event occurs
     * when the orientation of the page triggers.  A rotation can also be triggered
     * by the user.
     */
    var listener,
        $window = $(window);
    // On iOS devices, orientationchange does not exist, so we have to
    // listen for resize.  Similarly, the use of orientationchange is not
    // standard.  Reference: http://stackoverflow.com/questions/1649086/
    if (_.has(window, "onorientationchange")) {
        listener = "orientationchange";
    } else {
        listener = 'resize';
    }

    $window.on(listener, function () {
        $window.trigger('rotate');
    });
};