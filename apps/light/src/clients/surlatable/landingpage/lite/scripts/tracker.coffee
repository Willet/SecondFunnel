'use strict';

#  @module tracker

module.exports = (module, App, Backbone, Marionette, $, _) ->
    module.customTrackerSetup = ->
        gaAccountNumber = App.option('store:gaAccountNumber', false) or \
                          App.option('page:gaAccountNumber', 'UA-23764505-25');
        module._addItem('create', gaAccountNumber, 'auto', 'allowLinker': true)
        module._addItem('require', 'linker')
        module._addItem('linker:autoLink', ['www.surlatable.com'])
