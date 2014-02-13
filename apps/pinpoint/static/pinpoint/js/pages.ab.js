/*global App, $, Backbone, Marionette, console, _, GA_CUSTOMVAR_SCOPE.VISITOR  */
var ALPHANUMERIC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
/**
 * @module ab
 */
App.module("ab", function (ab, App) {
    "use strict";
    var pageId = App.option('page:id'),
        pageName = App.option('url', pageId),
        tracker = App.module.tracker,
        setCustomVar = function (index, test) {
            window.ga('set', 'dimension' + index, test);
        },
        is = function (device) {
            if (device === 'mobile') {
                return App.support.mobile();
            } else if (device && device.length) {
                return (new RegExp(device, 'i')).test(window.navigator.userAgent);
            }
            return true;
        };

    /**
     * Registers a new tests, tests registered should be of the form
     *     (method, device, index, arguments ....)
     * where index specifies the dimension where the result should be stored.
     *
     * @returns this
     */
    this.registerTest = function (method, device, index) {
        var result,
            args = Array.prototype.slice.call(arguments);
        args = args.slice(3);

        if (is(device)) {
            if (this.hasOwnProperty(method)) {
                result = this[method].apply(this,  args);
            } else if (_.isFunction(method)) {
                result = method.apply(this, args);
            }
        }
        // If given a variant, store it
        if (result) {
            setCustomVar(index, result);
        }
        return this;
    };

    /**
     * Specifies a style (styles) to apply to the specified selector
     * When registered, should be of form
     *    ...selector, styles, multivariates)
     * where styles is either an array or individual tile and multivariates is
     * an array of probabilities (optional, uniform if omitted)
     *
     * @returns string
     */
    this.style = function (selector, style, multivariate) {
        var s = $('<style type="text/css"></style>');
        style = this.multivariate(style, multivariate);
        if (style) {
            s.text(selector + " { " + style + " } ");
            $('head').append(s);
        }
        // TODO: Should not be storing the style in the analytics
        return style;
    };

    /**
     * Specifies template(s) to select from to replace the source template
     * When registered, should be of form
     *     ...sourceTemplate, replacement(s), multivariate)
     * where sourceTemplate and replacement templates are selectors; replacement
     * can be an array, multivariate is probabilities (uniform if omitted)
     *
     * @returns string
     */
    this.template = function (source, replacement, multivariate) {
        var tmp, templates;

        // Collect an array of the available templates
        if (_.isArray(replacement)) {
            templates = _.clone(replacement);
            templates.unshift(source);
        } else {
            templates = [source, replacement];
        }
        replacement = this.multivariate(templates, multivariate);

        tmp = replacement && $(replacement).length ? replacement : source;
        $(source).contents().replaceWith($(tmp).contents().clone());
        return ALPHANUMERIC[templates.indexOf(tmp)];
    };

    /**
     * Selects from an array if options is an array given probabilities,
     * otherwise uniform.  If options is not an array, selects with a
     * probability of 50%.
     *
     * @returns object
     */
    this.multivariate = function (options, probability) {
        var index = 0,
            ratio = Math.random();
        // Multivariate selection of option to return
        if (!(probability && probability.length)) {
            // Assume uniform
            if (_.isArray(options)) {
                return _.shuffle(options)[0];
            } else if (ratio < 0.5) {
                return options;
            }
        } else {
            // Assume multivariate in range 0 to 1
            if (_.isArray(options)) {
                for (index = 0; ratio < probability[index]; ++index);
                return options[index - 1];
            } else if (ratio < probability[0]) {
                return options;
            }
        }
        return undefined;
    };
});
