"use strict"

module.exports = (module, App, Backhone, Marionette, $, _) ->

    ###
    convenience method for accessing PAGES_INFO or TEST_*.

    To access deep options (e.g. PAGES_INFO.store.name), use the key
    "store.name" or "store:name" (preferred).

    @method option
    @param {string} name
    @param {*} defaultValue
    @returns {*}
    ###
    App.option = (name, defaultValue) ->
        opt = Marionette.getOption(App, name)
        keyNest = _.compact(name.split(/[:.]/))
        keyName = undefined
        cursor = App.options
        i = undefined
        depth = undefined

        # getOption() returns a blank object when it thinks it is accessing
        # a nested option so we have to patch that up
        if opt isnt undefined and keyNest.length is 1 and not _.isEmpty(opt)
            return opt

        # marionette sucks, so we'll do extra traversing to get stuff out of
        # our nested objects ourselves
        try
            i = 0
            depth = keyNest.length

            while i < depth
                keyName = keyNest[i]
                cursor = cursor[keyName]
                i++
            if cursor isnt undefined
                return cursor
        catch KeyError

            # requested traversal path does not exist. do the next line
            console.warn "Missing option: " + name
        defaultValue # ...and defaultValue defaults to undefined


    ###
    Marionette TemplateCache extension to allow checking cache for template
    Checks if the Template exists in the cache, if not found
    updates the cache with the template (if it exists), otherwise fail
    returns true if exists otherwise false.

    @method _exists
    @param templateId
    @returns {boolean}
    @private
    ###
    Marionette.TemplateCache._exists = (templateId) ->
        cached = @templateCaches[templateId]
        cachedTemplate = undefined
        if cached
            return true

        # template exists but was not cached
        cachedTemplate = new Marionette.TemplateCache(templateId)
        try
            cachedTemplate.load()

            # Only cache on success
            @templateCaches[templateId] = cachedTemplate
        catch err
            unless err.name and err.name is "NoTemplateError"
                throw err
        !!@templateCaches[templateId]


    ###
    Accept an arbitrary number of template selectors instead of just one.
    Function will return in a short-circuit manner once a template is found.

    @arguments {*} at least one jquery selector.
    @returns {*}
    ###
    Marionette.View::getTemplate = ->
        templateIDs = _.result(this, "templates")
        template = @template

        # the custom 'templates' variable is not there
        unless templateIDs
            return template

        # compose 'data' variable for rendering a tile priority list.
        # needs to be deep copy (for store info)
        data = $.extend({}, @model.attributes)
        try
            data.template = module.getModifiedTemplateName(data.template)
        catch err
            data.template = ""

        # model did not need to specify a template.
        i = 0
        while i < templateIDs.length
            temp = _.template(templateIDs[i],
                options: App.options
                data: data
            )
            templateExists = Marionette.TemplateCache._exists(temp)
            if templateExists

                # replace this thing's desired template ID to the
                # highest-order template found
                template = temp
                break
            i++
        template

    ###
    Reduces all image-type names to 'image'.
    If this logic gets any more complex, it should be moved into
    Tile or TileView.

    @param name {String} the current template name
    @returns {String} the correct template name
    ###
    @getModifiedTemplateName = (name) ->
        name?.replace /(styld[\.\-]by|tumblr|pinterest|facebook|instagram)/i, "image"

