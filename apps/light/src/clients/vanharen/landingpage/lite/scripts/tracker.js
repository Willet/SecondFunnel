'use strict';

module.exports = function (module, App, Backbone, Marionette, $, _) {
    module.customTrackerSetup = function () {
        var gaAccountNumber = App.option('store:gaAccountNumber', false) || App.option('page:gaAccountNumber', 'UA-23764505-25');
        module._addItem('create', gaAccountNumber, 'auto', {'allowLinker': true});
        module._addItem('require', 'linker');
        module._addItem('linker:autoLink', ['trends.vanharen.nl', 'www.vanharen.nl']);
    };
};
