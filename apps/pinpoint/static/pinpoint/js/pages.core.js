/*global Image, Marionette, setTimeout, Backbone, jQuery, $, _, console, App */
/**
 * @module core
 */
App.module('core', function (module, App) {
    // other args: https://github.com/marionettejs/Marionette/blob/master/docs/marionette.application.module.md#custom-arguments
    "use strict";
    var $window = $(window),
        $document = $(document);

    /**
     * convenience method for accessing PAGES_INFO or TEST_*.
     *
     * To access deep options (e.g. PAGES_INFO.store.name), use the key
     * "store.name" or "store:name" (preferred).
     *
     * @method option
     * @param {string} name
     * @param {*} defaultValue
     * @returns {*}
     */
    App.option = function (name, defaultValue) {
        var opt = Marionette.getOption(App, name),
            keyNest = _.compact(name.split(/[:.]/)),
            keyName,
            cursor = App.options,
            i,
            depth;

        if (opt !== undefined && keyNest.length === 1 && !_.isEmpty(opt)) {
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
            console.warn('Missing option: ' + name);
        }
        return defaultValue;  // ...and defaultValue defaults to undefined
    };

    /**
     * Marionette TemplateCache extension to allow checking cache for template
     * Checks if the Template exists in the cache, if not found
     * updates the cache with the template (if it exists), otherwise fail
     * returns true if exists otherwise false.
     *
     * @method _exists
     * @param templateId
     * @returns {boolean}
     * @private
     */
    Marionette.TemplateCache._exists = function (templateId) {
        var cached = this.templateCaches[templateId],
            cachedTemplate;

        if (cached) {
            return true;
        }

        // template exists but was not cached
        cachedTemplate = new Marionette.TemplateCache(templateId);
        try {
            cachedTemplate.load();
            // Only cache on success
            this.templateCaches[templateId] = cachedTemplate;
        } catch (err) {
            if (!(err.name && err.name === 'NoTemplateError')) {
                throw err;
            }
        }
        return !!this.templateCaches[templateId];
    };

    /**
     * Accept an arbitrary number of template selectors instead of just one.
     * Function will return in a short-circuit manner once a template is found.
     *
     * @arguments {*}    at least one jquery selector.
     * @returns {*}
     */
    Marionette.View.prototype.getTemplate = function () {
        var i, templateIDs = _.result(this, 'templates'),
            template = this.template,
            temp, templateExists, data;

        if (!templateIDs) {
            // the custom 'templates' variable is not there
            return template;
        }

        // compose 'data' variable for rendering a tile priority list.
        // needs to be deep copy (for store info)
        data = $.extend({}, this.model.attributes);

        try {
            data.template = module.getModifiedTemplateName(data.template);
        } catch (err) {
            data.template = '';
            // model did not need to specify a template.
        }

        for (i = 0; i < templateIDs.length; i++) {

            temp = _.template(templateIDs[i], {
                'options': App.options,
                'data': data
            });
            templateExists = Marionette.TemplateCache._exists(temp);

            if (templateExists) {
                // replace this thing's desired template ID to the
                // highest-order template found
                template = temp;
                break;
            }
        }
        return template;
    };

    // Default on missing template event
    Marionette.ItemView.prototype.onMissingTemplate = function () {
        console.warn('onMissingTemplate removing this: %o', this);
        this.remove();
    };

    /**
     * Reduces all image-type names to 'image'.
     * If this logic gets any more complex, it should be moved into
     * Tile or TileView.
     *
     * @param name {String}     the current template name
     * @returns {String}        the correct template name
     */
    this.getModifiedTemplateName = function (name) {
        return name.replace(/(styld[\.\-]by|tumblr|pinterest|facebook|instagram)/i,
            'image');
    };
});
