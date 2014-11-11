'use strict';

$ = require('jquery')
_ = require('underscore')
Backbone = require('backbone')
Marionette = require('backbone.marionette')

module.exports = (module, App) ->
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
            window.App.layoutEngine.masonry.once('layoutComplete', ->
                # Move Grooveshark overlay onto the tile position
                position = $('.grooveshark-placeholder').offset()
                if position?
                    $('.grooveshark-tile-overlay').css(
                        'top': position.top
                        'left': position.left
                    )
            )

        onClose: (ev) ->
            # Move Grooveshark overlay off of the screen
            $('.grooveshark-tile-overlay').css('left', '-10000px')


    class module.GiftcardTileView extends module.ContainerTileView
        template: "#giftcard_tile_template"

        onClick: (ev) ->
            tile = @model
            window.open tile.get("redirect-url"), "_blank"
            return
