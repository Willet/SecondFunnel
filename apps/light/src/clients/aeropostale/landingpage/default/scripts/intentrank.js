'use strict';

/**
 * @module intentRank
 */
module.exports = function (module, App, Backbone, Marionette, $, _) {
    // ### Aero mobile nav ###
    // requires a new change category function because sub-categories
    // are categories, not filters on categories
    module.changeMobileCategory = function (category) {

        if ($('.category-area span').length < 1) {
            return module;
        }
        if (category === '') {
            if (App.option("categoryHome") && App.option("categoryHome").length ) {
                category = App.option("categoryHome");
            } else {
                category = $('.category-area span:first').attr('data-name');
            }
        }

        if (module.options.category === category) {
            return module;
        }

        // Change the category, category is a string passed to data
        module.options.category = category;
        module.options.IRReset = true;
        App.tracker.changeCategory(category);

        App.vent.trigger('change:category', category, category);

        App.discovery = new App.feed.MasonryFeedView({
            options: App.options
        });
        $(".loading").show();
        App.discoveryArea.show(App.discovery);

        var categorySpan = $('.category-area span[data-name="' + category + '"]');
        categorySpan.trigger("click");

        return module;
    };
};
