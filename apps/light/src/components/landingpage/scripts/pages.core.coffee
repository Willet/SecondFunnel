"use strict"

json = require("json3")

module.exports = (module, App, Backbone, Marionette, $, _) ->

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
        return !!@templateCaches[templateId]

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
        unless data.template
            data.template = ""

        # model did not need to specify a template.
        i = 0
        while i < templateIDs.length
            compiledTemp = _.template(templateIDs[i])
            temp = compiledTemp(
                data: data
                options: App.options
            )
            templateExists = Marionette.TemplateCache._exists(temp)
            if templateExists

                # replace this thing's desired template ID to the
                # highest-order template found
                template = temp
                break
            i++
        if App.option('debug', false)
            console.warn("Retrieved template: #{temp}")
        return template

    ###
    Using templateId, checks if the template exists in the cache and creates a
    new one if not found. Returns the template string.

    @method getSubtemplate
    @param templateId
    @returns {string} template
    ###
    Marionette.TemplateCache.getSubtemplate = (templateId) ->
        cachedTemplate = @templateCaches[templateId]
        if not cachedTemplate
            cachedTemplate = new Marionette.TemplateCache(templateId)
            @templateCaches[templateId] = cachedTemplate

        return cachedTemplate.loadSubtemplate()

    ###
    Replaces default load method. Stores template string in "template" property.
    ###
    Marionette.TemplateCache::load = ->
        if @compiledTemplate is undefined
            @rawTemplate = @loadTemplate(@templateId)
            @compiledTemplate = @compileTemplate(@rawTemplate)
        
        return @compiledTemplate


    ###
    Returns partially compiled template string.

    @method loadSubtemplate
    @returns {string} template
    ###
    Marionette.TemplateCache::loadSubtemplate = ->
        if @rawTemplate is undefined
            templateStr = @loadTemplate(@templateId)
            @rawTemplate = @compileSubtemplate(templateStr)
        
        return @rawTemplate

    ###
    Replaces default compileTempalte method. Removes include tags before
    compiling the template.
    ###
    Marionette.TemplateCache::compileTemplate = (rawTemplate) ->
        rawTemplate = @compileSubtemplate(rawTemplate)
        
        return _.template(rawTemplate)

    ###
    Replaces all include tags within a given template with cached templates.
    Returns the resulting partially-compiled template.

    @method compileSubtemplate
    @param str
    @returns {string} template
    ###
    Marionette.TemplateCache::compileSubtemplate = (str) ->
        includeRegex = /<%\sinclude(\("(.*?)"\)|\s"(.*?)");?\s%>/g
        str = str.replace(
            includeRegex,
            (match, result, javascriptId, coffeescriptId) ->
                templateId = "##{javascriptId or coffeescriptId}"

                return Marionette.TemplateCache.getSubtemplate(templateId)
            )
        
        return str

    ###
    Wraps Marionette.Renderer to catch and report templating errors

    @method 
    @returns
    ###
    baseRenderer = Marionette.Renderer.render
    Marionette.Renderer.    render = (template, data) ->
        try
            return baseRenderer(template, data)
        catch e
            if App.option('debug', false)
                try
                    rawTemplate = Marionette.TemplateCache::loadTemplate(template)
                    expandedTemplate = Marionette.TemplateCache::compileSubtemplate(rawTemplate)
                catch e
                    # template error
                    expandedTemplate = ''
                console.warn(
                    """Template error: %s: %s
                    %s: %s
                    data: %O
                    """,
                    e.name, e.message, template, $.trim(expandedTemplate), data
                )
            return ''
        
