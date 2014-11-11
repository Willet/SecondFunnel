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

    class module.GiftcardTileView extends module.ContainerTileView
        template: "#giftcard_tile_template"

        onClick: (ev) ->
            # Hard-coded URL for one-off tile rather than write new IR serializer for the DB
            window.open 'http://www.aeropostale.com/giftCards/index.jsp', "_blank"
            return
