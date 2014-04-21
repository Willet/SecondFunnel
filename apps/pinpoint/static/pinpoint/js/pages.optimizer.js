/*global App, $, Backbone, Marionette, console, _, setInterval, clearInterval */
/**
 * @module optimizer
 * @description A/B, split, and multivariate testing tool
*/
App.module('optimizer', function (optimizer, App) {
    "use strict";
    var GA_CUSTOMVAR_SCOPE = {
            'PAGE': 3,
            'EVENT': 3,
            'SESSION': 2,
            'VISITOR': 1
        },
        CUSTOM_DIMENSIONS = [],
        ENABLED_TESTS = [],
        UPPERCASE_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        OPTIMIZER_COOKIE = '__sotm',
        MILLISECONDS_PER_DAY = 1000 * 60 * 60 * 24,
        is = function (device) {
            if (device === 'mobile') {
                return $(window).width() <= 768;
            } else if (device && device.length) {
                return (new RegExp(device, 'i')).test(window.navigator.userAgent);
            }
            return true;
        },
        lt = function (resolution) {
            var width = $(window).width(),
                height = $(window).height();
            if (resolution.width && width > resolution.width) {
                return false;
            } else if (resolution.height && height > resolution.height) {
                return false;
            }
            return true;
        },
        gt = function (resolution) {
            return !lt(resolution);
        },
        setDimension = function (index, val) {
            var dim = 'dimension' + index;

            if (window.ga) {
                window.ga('set', dim, val);
            }

            CUSTOM_DIMENSIONS.push({
                'index': index,
                'type': 'dimension',
                'value': val
            });
        },
        getPos = function (ch) {
            return UPPERCASE_LETTERS.indexOf(ch);
        },
        getTestIndex = function (item, list) {
            return UPPERCASE_LETTERS.charAt(list.indexOf(item));
        };

    /**
     * Returns the custom dimensions.
     *
     * @returns object
     **/
    this.dimensions = function () {
        return _.clone(CUSTOM_DIMENSIONS);
    };

    /**
     * Sets the value and expiration date for a cookie specified by
     * cname.
     *
     * @returns none
     **/
    this.setCookieValue = function (cname, value, days) {
        var expires, ms, d = new Date();
        ms = days ? days * MILLISECONDS_PER_DAY : 30 * 60 * 1000; // Defaults to 30 minutes, convert to milliseconds
        d.setTime(d.getTime() + ms);
        expires = "expires=" + d.toGMTString();
        console.debug(cname + "=" + value + "; " + expires);
        document.cookie = cname + "=" + value + "; " + expires;
    };

    /**
     * Clears the cookie with the specified cname.
     *
     * @returns none
     **/
    this.clearCookie = function (cname) {
        var expires = new Date();
        expires.setTime(0);
        expires = "expires=" + expires.toGMTString();
        console.debug("Clearing cookie ", cname);
        document.cookie = cname + "=dummy; " + expires;
    };

    /**
     * Gets the value for a cookie specified by cname
     *
     * @returns string
     **/
    this.getCookieValue = function (cname) {
        var cookies = document.cookie.split(';'),
            c;
        cname += "=";
        for (var i = 0; i < cookies.length; ++i) {
            c = $.trim(cookies[i]);
            if (c.indexOf(cname) === 0)
                return c.substring(cname.length, c.length);
        }
        return "";
    };

    /**
     * Uses multivariate probabilities and randomness to select an option
     * from a list of passed options.
     *
     * @returns Object
     **/
    this.multivariate = function (options, probabilities) {
        var p,
            temp = [],
            rand = Math.random();

        if (probabilities) {
            // Add each item to list based on probability
            for (var i = 0; i < options.length; ++i) {
                // Assume round down
                p = Math.floor(probabilities[i] * 10);
                while (p > 0) {
                    temp.push(options[i]);
                    p--;
                }
            }
            rand = Math.floor(rand * temp.length);
            return temp[rand];
        }
        // Otherwise uniform, so sample
        return _.sample(options);
    };

    /**
     * Adds a test to the optimizer module.
     *
     * @returns none
     **/
    this.addTest = function (index, test, kwargs) {
        var result,
            pos,
            selector = kwargs.selector,
            options = kwargs.options,
            probabilities = kwargs.probabilities,
            cookie = OPTIMIZER_COOKIE + index;

        if ((kwargs.disabled || App.option('debug', App.QUIET) > App.QUIET) &&
            !ENABLED_TESTS.hasOwnProperty(index)) {
            return;
        }

        result = ENABLED_TESTS[index] || this.getCookieValue(cookie);
        if (result && result.length && options) {
            pos = getPos(result);
            probabilities = Array.apply(null, new Array(options.length)).map(Number.prototype.valueOf, 0);
            probabilities[pos] = 1;
        }

        switch(test) {
            case 'template':
                result = this.testTemplate(selector, options, probabilities);
                break;
            case 'style':
                result = this.testStyle(selector, probabilities);
                break;
            default:
                result = kwargs.custom(result);
        }

        console.debug(index + '.' + test + ': ' + result);
        if (result && result.length) {
            setDimension(index, result);
            this.setCookieValue(cookie, result);
        } else {
            this.clearCookie(cookie);
        }
    };

    /**
     * Runs a styling test that renders either a style tag or adds a style
     * to the page.
     *
     * @returns string
     **/
    this.testStyle = function (styles, probabilities) {
        var style,
            $style,
            pathname;
        if (styles.length < probabilities.length) {
            styles.unshift("");
        }

        style = this.multivariate(styles, probabilities);
        pathname = style.match(/(https?|www)/);
        if (pathname && style.indexOf(pathname[0]) == 0) {
            $style = $('<link></link>');
            $style.attr('rel', "stylesheet")
                  .attr('href', style);
            $('head').append($style);
        } else if (style.length > 0) {
            $style = $('<style></style>');
            $style.attr('type', "text/css")
                  .text(style);
            $('head').append($style);
        }
        return getTestIndex(styles, style);
    };

    /**
     * Runs a template test.
     *
     * @returns string
     **/
    this.testTemplate = function (selector, templates, probabilities) {
        var $selector,
            $template,
            template = this.multivariate(templates, probabilities),
            exists = setInterval(function () {
                $selector = $(selector);
                $template = $(template);
                if ($selector.length && $template.length) {
                    clearInterval(exists);
                    $selector.contents().replaceWith($template.contents());
                }
            }, 100);
        return getTestIndex(template, templates);
    };

    /**
     * Initializes the optimizer testing module.
     *
     * @returns none
     **/
    this.initialize = function () {
        var test,
            index,
            tests = {},
            self = this;

        window.OPTIMIZER_TESTS = window.OPTIMIZER_TESTS || [];
        ENABLED_TESTS = App.utils.getQuery('activate-test').split(',');
        _.each(ENABLED_TESTS, function (t) {
            t = t.split('.');
            if (t[1]) {
                tests[t[0]] = t[1].toUpperCase();
            } else {
                tests[t[0]] = t[1];
            }
        });
        ENABLED_TESTS = tests;

        _.each(window.OPTIMIZER_TESTS, function (t) {
            index = t.index || t.slot;
            // Don't run all A/B Tests in quiet mode
            if (t.device && !is(t.device)) {
                return;
            } else if (t['min-resolution'] && !gt(t['min-resolution'])) {
                return;
            } else if (t['max-resolution'] && !lt(t['max-resolution'])) {
                return;
            }
            test = t.test;
            self.addTest(index, test, t);
        });
    };
});
