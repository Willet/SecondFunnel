'use strict';

/**
 * @module utils
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {

    module.addUrlTrackingParameters = function (url) {
        var trackingCode = {
            'for-her':                 'for_her',
            'for-him':                 'for_him',
            'under-$10':               'under_10',
            'under-$10|girls':         'under_10_for_her',
            'under-$10|guys':          'under_10_for_him',
            'under-$20':               'under_20',
            'under-$20|girls':         'under_20_for_her',
            'under-$20|guys':          'under_20_for_him',
            'stocking-stuffers':       'stocking_stuffers',
            'stocking-stuffers|girls': 'stocking_stuffers_for_her',
            'stocking-stuffers|guys':  'stocking_stuffers_for_him'
        };
        var params = { 
            'utm_source': 'giftguide',
            'utm_medium': 'site',
            'utm_campaign': trackingCode[ App.intentRank.options.category ] || 'for_her'
        };

        return module.urlAddParams(url, params);
    };
};