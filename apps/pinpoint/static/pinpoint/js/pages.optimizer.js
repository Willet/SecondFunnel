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
        setDimension = function (index, val) {
            var dim = 'dimension' + index;
            if (window.ga) {
                window.ga('set', dim, val);
            }
        },
        getPos = function (ch) {
            return UPPERCASE_LETTERS.indexOf(ch);
        },
        getTestIndex = function (item, list) {
            return UPPERCASE_LETTERS.charAt(list.indexOf(item));
        };

    
    /**
     * Sets the value and expiration date for a cookie specified by
     * cname.
     *
     * @returns none
     **/
    this.setCookieValue = function (cname, value, days) {
        var expires, ms, d = new Date();
        ms = days ? days * MILLISECONDS_PER_DAY : 30 * 6000; // Defaults to 30 minutes, convert to milliseconds
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
            c = cookies[i].trim();
            if (c.indexOf(cname) == 0)
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
    this.addTest = function (index, test, args) {
        var result,
            pos,
            selector = args.selector,
            options = args.options,
            probabilities = args.probabilities,
            cookie = OPTIMIZER_COOKIE + index;

        if ((args.disabled || App.option('debug', App.QUIET) > App.QUIET) &&
            (ENABLED_TESTS.indexOf(index.toString()) == -1)) {
            return;
        }

        result = this.getCookieValue(cookie);
        if (result && result.length && options) {
            pos = getPos(result);
            probabilities = Array.apply(null, new Array(options.length)).map(Number.prototype.valueOf, 0);
            probabilities[pos] = 1;
        }

        switch(test) {
            case 'template':
                result = this.testTemplate(selector, options, probabilities);
                break;
            default:
                result = args.custom(result);
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
        var test, index, self;
        ENABLED_TESTS = App.utils.getQuery('activate-test').split(',');
        window.OPTIMIZER_TESTS = window.OPTIMIZER_TESTS || [];
        self = this;

        _.each(window.OPTIMIZER_TESTS, function (t) {
            index = t.index || t.slot;
            // Don't run all A/B Tests in quiet mode
            if (t.device && !is(t.device)) {
                return;
            }
            test = t.test;
            self.addTest(index, test, t);
        });
    };

    // Force start, as run independentally of when the App begins
    this.initialize();
});
