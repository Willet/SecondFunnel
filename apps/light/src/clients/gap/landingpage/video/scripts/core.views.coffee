"use strict"

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.HeroContent.prototype.events =
        'click #more-button': ->
            numDefaultThumbnails = 1
            @$("#more-button").attr("style", "display: none;")
            table = @$(".thumbnail-table")[0]
            thumbnailTemplate = "<td><div class='thumbnail-item'>
                    <div class='thumbnail-image' style='background-image: url(\"<%= thumbnail.url %>\");'></div>
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