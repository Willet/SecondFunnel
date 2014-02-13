/*global App, $, Backbone, Marionette, console, _, GA_CUSTOMVAR_SCOPE.VISITOR  */
var ALPHANUMERIC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

/**
 * @module ab
 */
App.module("ab", function (ab, App) {
    "use strict";
    var pageId = App.option('page:id'),
        pageName = App.option('url', pageId),
        tracker = App.module.tracker;

    this.setCustomVar = function (index, test) {
        window.ga('set', 'dimension' + index, test);
    };

    this.is = function (device) {
        if (device === 'mobile') {
            return App.support.mobile();
        } else if (device && device.length) {
            return (new RegExp(device, 'i')).test(window.navigator.userAgent);
        }
        return true;
    };

    this.registerTest = function (method, device) {
        var index, result,
            args = Array.prototype.slice.call(arguments);
        args = args.slice(2);
        index = args.shift();

        if (this.is(device)) {
            if (this.hasOwnProperty(method)) {
                result = this[method].apply(this,  args);
            } else if (_.isFunction(method)) {
                result = method.apply(this, args);
            }
        }

        if (result) {
            this.setCustomVar(index, result);
        }
        return this;
    };

    // TODO: Style should support multivariate
    this.style = function (selector, style, multivariate) {
        var s = $('<style type="text/css"></style>');
        style = this.multivariate(style, multivariate);
        if (style) {
            s.text(selector + " { " + style + " } ");
            $('head').append(s);
        }
        return style;
    };

    this.template = function (source, replacement, multivariate) {
        var tmp, templates;

        // Collect an array of the available templates
        templates = _.isArray(replacement) ?
            replacement.unshift(source) : [source, replacement];
        replacement = this.multivariate(templates, multivariate);

        tmp = replacement && $(replacement).length ? replacement : source;
        $(source).contents().replaceWith($(tmp).contents().clone());

        return ALPHANUMERIC[templates.indexOf(tmp)];
    };

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
