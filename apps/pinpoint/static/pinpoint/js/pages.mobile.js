var PAGES = PAGES || {};

PAGES.mobile = (function (me) {
    "use strict";

    var local_data = {};

    function renderToView(view_selector, template_name, context, append) {
        var template = $("[data-template-id='" + template_name + "']").html(),
            rendered_block;

        // template does not exist
        if (template === undefined) {
            return;
        }

        rendered_block = _.template(template, context);

        if (append) {
            $(view_selector).append(rendered_block);
        } else {
            $(view_selector).html(rendered_block);
        }
    }

    me = {
        'layoutFunc': function (jsonData, belowFold, related) {
            _.each(jsonData, function (data, index, list) {

                var object_id = data.id || data['original-id'];

                var templateName = PAGES.getModifiedTemplateName(data.template);

                // Old themes used 'instagram',
                // need to verify template exists
                if (templateName === 'image' &&
                    !$("[data-template-id='" + templateName + "']").html()) {
                    templateName = 'instagram';
                }

                // cache content's data for future rendering
                local_data[templateName + object_id] = data;

                // render object if possible
                renderToView(".content_list", templateName, {
                    data: data
                }, true);

                // just rendered last element
                if (index == (list.length - 1)) {
                    PAGES.setLoadingBlocks(false);
                }
            });
        },
        'readyFunc': function () {

            MBP.hideUrlBarOnLoad();
            MBP.preventZoom();

            $(window).scroll(PAGES.pageScroll);
            $(window).resize(PAGES.pageScroll);

            PAGES.loadInitialResults();
        }
    };

    return me;
})();