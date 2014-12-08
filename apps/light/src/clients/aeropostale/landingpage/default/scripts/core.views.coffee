'use strict';

module.exports = (module, App, Backbone, Marionette, $, _) ->
    ###
    A container tile that has no onclick or onhover

    @constructor
    @type {Layout}
    ###
    class module.ContainerTileView extends module.TileView
        onHover: (ev) ->
            return

        onClick: (ev) ->
            return

    class module.GroovesharkTileView extends module.ContainerTileView
        template: "#grooveshark_tile_template"

        onShow: (ev) ->
            App.vent.once 'layoutCompleted', ->
                # Move Grooveshark overlay onto the tile position
                position = $('.grooveshark-placeholder').offset()
                if position?
                    $('.grooveshark-tile-overlay').css(
                        'top': position.top
                        'left': position.left
                    )

        onClose: (ev) ->
            # Move Grooveshark overlay off of the screen
            $('.grooveshark-tile-overlay').css('left', '-10000px')

    class module.GiftcardTileView extends module.ContainerTileView
        template: "#giftcard_tile_template"

        onClick: (ev) ->
            url = App.utils.addUrlTrackingParameters( @model.get("redirect-url") )
            window.open url, "_self"
            return

    class module.BannerTileView extends module.TileView
        template: "#banner_tile_template"

        onClick: (ev) ->
            url = App.utils.addUrlTrackingParameters( @model.get("redirect-url") )
            window.open url, "_self"
            return
