"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.HeroContent.prototype.events =
        'click #more-button': ->
            numDefaultThumbnails = 1
            @$("#more-button").attr("style", "display: none;")
            table = @$(".thumbnail-table>tbody")[0]
            thumbnailTemplate = "<td><div class='thumbnail-item' data-index='<%- i %>'>
                    <div class='thumbnail-image<% if (thumbnail.youtubeId) { %> playing<% } %>' style='background-image: url(\"<%= thumbnail.url %>\");'></div>
                    <p>Episode <%= i + 1 %> <br><%= thumbnail.date %></p>
                </div></td>"
            if table
                for thumbnail, i in @model.get('thumbnails') when i >= numDefaultThumbnails
                    thumbnailElem = _.template(thumbnailTemplate, { "thumbnail" : thumbnail, "i" : i })
                    table.insertRow(-1).innerHTML = thumbnailElem
            return

        'click .thumbnail-item': (ev) ->
            $ev = $(ev.target)
            if not $ev.hasClass('thumbnail-item')
                $ev = $ev.parent('.thumbnail-item')
            i = $ev.data('index')
            thumbnails = @model.get('thumbnails')
            if i? and thumbnails? and _.isObject(thumbnails[i])
                youtubeId = thumbnails[i]['youtubeId']
                if youtubeId
                    @video?.currentView?.player?.cueVideoById(String(youtubeId))?.playVideo()

    App.vent.once('tracking:videoFinish', (videoId, event) ->
        event.target.cuePlaylist(
            "listType": "list"
            "list": "PLGlQfj8yOxeh5TYm3LbIkSwUh9RMxJFwi"
        )
    )

    _.extend(module.ExpandedContent.prototype.events,
        'click .stl-swipe-down, .stl-swipe-up': (ev) ->
            stlItems = @$el.find(".stl-item")
            stlContainer = @$el.find(".stl-look-container")
            containerHeight = stlContainer.offset().top + stlContainer.height()
            index = undefined
            margin = 0
            for item, i in stlItems
                itemHeight = $(item).offset().top + $(item).height()
                ## Find first visible item ##
                if itemHeight < containerHeight
                    index = i
                    if ev.target.className is "stl-swipe-up"
                        margin = 30 unless index is 0 ## 30px padding ##
                    else
                        margin = stlContainer.height()*(-1)
                    break
            unless index is undefined
                upArrow = @$el.find(".stl-swipe-up")
                downArrow = @$el.find(".stl-swipe-down")
                upArrow.hide()
                downArrow.hide()
                $(stlItems[index]).animate({"marginTop": margin}, 250, "swing", =>
                    ## TODO: May want to turn this into a private method? ##
                    lastItemHeight = stlItems.last().offset().top + stlItems.last().height()
                    firstItemHeight = stlItems.first().offset().top + stlItems.first().height()
                    if firstItemHeight > stlContainer.offset().top then upArrow.hide() else upArrow.show()
                    if lastItemHeight < stlContainer.offset().top + stlContainer.height() then downArrow.hide() else downArrow.show()
                )
            return

        'click .stl-swipe-left, .stl-swipe-right': (ev) ->
            stlItems = @$el.find(".stl-item")
            stlContainer = @$el.find(".stl-look-container")
            containerWidth = stlContainer.offset().left + stlContainer.width()
            index = undefined
            margin = 0
            for item, i in stlItems
                itemWidth = $(item).offset().left + $(item).width()
                if itemWidth < containerWidth
                    index = i
                    if ev.target.className is "stl-swipe-left"
                        margin = 15 unless index is 0 ## 30px padding ##
                    else
                        margin = stlContainer.width()*(-1)
                    break
            unless index is undefined
                leftArrow = @$el.find(".stl-swipe-left")
                rightArrow = @$el.find(".stl-swipe-right")
                leftArrow.hide()
                rightArrow.hide()
                $(stlItems[index]).animate({"marginLeft": margin}, 250, "swing", =>
                    lastItemWidth = stlItems.last().offset().left + stlItems.last().width()
                    firstItemWidth = stlItems.first().offset().left + stlItems.first().width()
                    if firstItemWidth > stlContainer.offset().left then leftArrow.hide() else leftArrow.show()
                    if lastItemWidth < stlContainer.offset().left + stlContainer.width() then rightArrow.hide() else rightArrow.show()
                )
            return
    )

    module.ExpandedContent::arrangeStlItemsVertical = (element) ->
        upArrow = element.find(".stl-swipe-up")
        downArrow = element.find(".stl-swipe-down")
        stlItems = element.find(".stl-item")
        stlContainer = element.find(".stl-look-container")
        containerHeight = stlContainer.offset().top + stlContainer.height()
        for item, i in stlItems
            itemHeight = $(item).offset().top + $(item).height()
            if itemHeight > containerHeight - 20 ## position of down arrow at 20px ##
                unless $(item).offset().top is stlContainer.offset().top + stlContainer.height() + 20
                    $(item).css
                        ## position of arrow + padding ##
                        "margin-top": stlContainer.offset().top + stlContainer.height() - $(item).offset().top + 50 
                containerHeight += stlContainer.height()    
        lastItemHeight = stlItems.last().offset().top + stlItems.last().height()
        firstItemHeight = stlItems.first().offset().top + stlItems.first().height()
        if firstItemHeight > stlContainer.offset().top then upArrow.hide() else upArrow.show()
        if lastItemHeight < stlContainer.offset().top + stlContainer.height() then downArrow.hide() else downArrow.show()
        return

    module.ExpandedContent::arrangeStlItemsHorizontal = (element) ->
        leftArrow = element.find(".stl-swipe-left")
        rightArrow = element.find(".stl-swipe-right")
        stlItems = element.find(".stl-item")
        stlContainer = element.find(".stl-look")
        containerWidth = stlContainer.offset().left + stlContainer.width()
        for item, i in stlItems
            itemWidth = $(item).offset().left + $(item).width()
            if itemWidth > containerWidth - 15
                unless $(item).offset().left is stlContainer.offset().left + stlContainer.width() + 15
                    $(item).css
                        "margin-left": stlContainer.offset().left + stlContainer.width() - $(item).offset().left + 35
                stlContainer.css
                    "text-align": "left"
                containerWidth += stlContainer.width()
        lastItemWidth = stlItems.last().offset().left + stlItems.last().width()
        firstItemWidth = stlItems.first().offset().left + stlItems.first().width()
        if firstItemWidth > stlContainer.offset().left then leftArrow.hide() else leftArrow.show()
        if lastItemWidth < stlContainer.offset().left + stlContainer.width() then rightArrow.hide() else rightArrow.show()
        return

    module.ExpandedContent::resizeContainer = ->
        shrinkContainer = (element) ->
            ->
                unless App.support.mobile()
                    table = element.find(".table")
                    container = element.closest(".fullscreen")
                    containedItem = element.closest(".content")
                    if --imageCount isnt 0
                        return

                    # no container to shrink
                    unless container and container.length
                        return
                    container.css
                        top: "0"
                        bottom: "0"
                        left: "0"
                        right: "0"

                    tableHeight = undefined
                    numImages = element.find("img.image").length
                    unless tileType == "product"
                        if (orientation == "landscape" and numImages > 1) or orientation == "portrait"
                            tableHeight = container.height()
                        else
                            tableHeight = container.width()*0.496
                        table.css
                            height: tableHeight

                    heightReduction = $(window).height()
                    widthReduction = $(window).width()
                    heightReduction -= containedItem.outerHeight()
                    heightReduction /= 2 # Split over top and bottom
                    if heightReduction <= 0 or App.support.mobile() # String because jQuery checks for falsey values
                        heightReduction = "0"
                    widthReduction -= containedItem.outerWidth()
                    widthReduction /= 2
                    if widthReduction <= 0 or App.support.mobile() # String because jQuery checks for falsey values
                        widthReduction = "0"
                    container.css
                        top: heightReduction
                        bottom: heightReduction
                        left: widthReduction
                        right: widthReduction
                    if orientation == "landscape"
                        _this.arrangeStlItemsHorizontal(element)
                    else
                        _this.arrangeStlItemsVertical(element)
                return

        imageCount = $("img.main-image, img.image", @$el).length
        tileType = @model.get("template")
        orientation = @model.get("orientation")
        _this = @
        if @model.get("sizes")?.master
            width = @model.get("sizes").master.width
            height = @model.get("sizes").master.height
            if width > height
                orientation = "landscape"
            else if width == height
                orientation = "square"

        # http://stackoverflow.com/questions/3877027/jquery-callback-on-image-load-even-when-the-image-is-cached
        $("img.main-image, img.image", @$el).one("load", shrinkContainer(@$el)).each ->
            if @complete
                # Without the timeout the box may not be rendered. This lets the onShow method return
                setTimeout (=>
                    $(@).load()
                    return
                ), 1
            return

        return
