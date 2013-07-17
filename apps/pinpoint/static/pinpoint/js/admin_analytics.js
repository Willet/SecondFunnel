Willet.analytics = (function ($) {
    "use strict";
    var init, settings, setUpListeners, injectAnalyticsData, loadAnalytics;

    loadAnalytics = function (obj) {
        var request = {
            "range": $(".range option:selected").val()
        };

        obj = obj || {};
        // request (function scope) vs settings (module scope)
        request.campaign_id = obj.campaign_id || settings.campaign_id;
        request.store_id = obj.store_id || settings.store_id;
        settings.campaign_id = request.campaign_id;
        settings.store_id = request.store_id;

        // pass only one of the values down the wire
        if (request.campaign_id) {
            delete request.store_id;
        }

        if (request.store_id) {
            delete request.campaign_id;
        }

        $.ajax({
            url: settings.ajaxURL,
            dataType: "json",
            data: request,
            success: function (data) {
                injectAnalyticsData(data);
            }
        });
    };

    injectAnalyticsData = function (data) {
        if (data.error) {
            $(".ajax.error").slideDown();
            $(".progressbar").slideUp();
            return;
        }
        var sortables = {
                'engaged_products': [],
                'engaged_content': [],
                'engaged_videos': [],
                'sharing_products': [],
                'sharing_source': [],
                'sharing_sources_of': [],
                'visitor_source': [],
                'interaction_source': [],
                'visitor_locations': [],
                'visitor_dates': []
            },

            merge_totals = function (t1, t2) {
                var res = $.extend(true, {}, t1),
                    type,
                    key;

                for (type in t2) {
                    for (key in t2[type]) {
                        res[type][key] = (res[type][key] || 0) + t2[type][key];
                    }
                }

                return res;
            },

            totals = {
                interactions: {
                    all: data.engagement['total-interactions'].totals.date.all,
                    product: data.engagement['product-interactions'].totals.date.all,
                    content: data.engagement['content-interactions'].totals.date.all,
                },
                shares: data.sharing['total-shares'].totals.date.all,
                visitors: data.awareness['awareness-visitors'].totals.date.all,
                pageviews: data.awareness['awareness-pageviews'].totals.date.all,
                notbounces: data.engagement['total-no-bounces'].totals.date.all
            },

            bounce_rate = (1 - totals.notbounces / totals.visitors) * 100,

            not_bounced_visitors,

            cat_slug, metric_slug,

            merged = {}, to_merge = {
                "sharing": [
                    data.sharing['share-clicked'].totals,
                    data.sharing['share-liked'].totals
                ],

                "product_interactions": [
                    data.engagement['inpage-openpopup'].totals,
                    data.engagement['inpage-hover'].totals
                ],

                "content_interactions": [
                    data.engagement['content-openpopup'].totals,
                    data.engagement['content-hover'].totals
                ],

                "sources": [
                    data.engagement['content-openpopup-source'].totals,
                    data.engagement['content-hover-source'].totals,
                    data.engagement['inpage-hover-source'].totals,
                    data.engagement['inpage-openpopup-source'].totals
                ],

                "sharing_sources": [
                    data.sharing['share-clicked-source'].totals,
                    data.sharing['share-liked-source'].totals
                ]
            },

            top_lists,

            postprocess_sections;

        _.each(to_merge, function (list, key) {
            var result, reduce_start = merge_totals(list[0], list[1]);

            merged[key] = _.reduce(list.slice(2), function (memo, item) {
                return merge_totals(memo, item);
            }, reduce_start);
        });

        if (isNaN(bounce_rate)) {
            bounce_rate = 0;
        }

        not_bounced_visitors = totals.visitors - totals.visitors * bounce_rate / 100;

        var insertAnalytics = function (o) {
            var params = o.params,
                pair = o.pair,
                all_data = o.data,

                actions = {
                    "common": function (api_type, template, params, pair, data_selector) {
                        if (pair === undefined) {
                            return;
                        }

                        Willet.mediaAPI.getObject(api_type, pair[0], function (data) {
                            var box_t = _.template($(template).html()),
                                caption_t = _.template($("#count_with_percentage").html());

                            $(params.selector).append(box_t({
                                data: data_selector(data),
                                name: data.name,
                                caption: caption_t({
                                    verb: params.verb,
                                    count: pair[1],
                                    total: params.total
                                })
                            }));
                        });
                    },

                    "content": function (params, pair) {
                        actions.common("generic_image", "#top_list_item", params, pair, function (data) {
                            var image = data.hosted || data.remote;
                            return image.slice(0, image.indexOf("?Sig"));
                        });
                    },

                    "product": function (params, pair) {
                        actions.common("product", "#top_list_item", params, pair, function (data) {
                            return (data.media.hosted || data.media.remote).replace("master.jpg", "thumb.jpg");
                        });
                    },

                    "video": function (params, pair) {
                        actions.common("video", "#video_item", params, pair, function (data) {
                            return data.video_id;
                        });
                    },

                    "bar_chart": function (params, pair, all_data) {
                        var chart = new BarChart({
                            selector: params.selector,
                            data: all_data,

                            total: params.total,

                            width: params.width,
                            row_height: params.row_height
                        });
                    },

                    "column_chart": function (params, pair, all_data) {
                        // sort by date
                        all_data.sort(function (a, b) {
                            return new Date(a[0]) - new Date(b[0]);
                        });

                        var chart = new ColumnChart({
                            selector: params.selector,
                            data: all_data,

                            min_width: params.min_width,
                            height: params.height,
                            col_width: params.col_width
                        });
                    },

                    "single_value": function (params, pair, all_data) {
                        var t = _.template($("#single_value_t").html());
                        $(params.selector).html(t({
                            value: all_data
                        }));
                    }
                },

                adjust_width = function (section_selector) {
                    var $s = $(section_selector);

                    // 20px accounts for margins
                    $s.css("width", $s.children().length * ($s.children().width() + 20) + "px");
                };

            actions[params.type](params, pair, all_data);
        };

        top_lists = {
            'engaged_products': merged.product_interactions.target_id,
            'engaged_content': merged.content_interactions.target_id,
            'engaged_videos': data.engagement['content-video'].totals.target_id,
            'visitor_locations': data.awareness['awareness-location'].totals.meta,
            'visitor_dates': data.awareness['awareness-visitors'].totals.date,

            'sharing_products': merged.sharing.target_id,
            'sharing_source': merged.sharing.meta,
            'sharing_sources_of': merged.sharing_sources.meta,

            'interaction_source': merged.sources.meta,

            'visitor_source': data.awareness['awareness-visitors'].totals.meta,

            'interaction_sections': merged.product_interactions.meta,

            'interaction_types': {
                "Hovers": data.engagement['inpage-hover'].totals.date.all + data.engagement['content-hover'].totals.date.all,
                "Clicks": data.engagement['inpage-openpopup'].totals.date.all + data.engagement['content-openpopup'].totals.date.all,
                "Videos": data.engagement['content-video'].totals.date.all
            }
        };

        // insert totals for metrics into the sidebar
        for (cat_slug in data) {
            for (metric_slug in data[cat_slug]) {
                // display totals in the sidebar on in the content section
                $(".metric_overview[data-metric='" + metric_slug + "']").html(
                    data[cat_slug][metric_slug].totals.date.all.toFixed(0)
                );
            }
        }

        // These metrics aren't calculated by the backend atm, hence the ugly implementation
        $(".per-visitor").remove();

        $(".section_overview_block:nth-child(2) .section_overview_metrics ul").append(
            "<li class='per-visitor'><span class='metric_overview' data-metric='interactions-per-visitor'>" + (totals.interactions.all / not_bounced_visitors || 0).toFixed(2) + "</span> Interactions per engaged visitor</li>");

        $(".section_overview_block:nth-child(3) .section_overview_metrics ul").append(
            "<li class='per-visitor'><span class='metric_overview' data-metric='shares-per-visitor'>" + (totals.shares / not_bounced_visitors || 0).toFixed(2) + "</span> Shares per visit</li>");

        $(".section_overview_block:nth-child(1) .section_overview_metrics ul").append(
            "<li class='per-visitor'><span class='metric_overview' data-metric='bounce-rate'>" + bounce_rate.toFixed(2) + "%</span> Bounce Rate</li>");

        // construct lists of sorted (desc) (pid, count) pairs
        _.each(top_lists, function (list, key) {
            sortables[key] = _.map(list, function (count, pid) {
                if (pid !== "all" && pid !== "null" && pid !== "meta_metric") {
                    return [pid, count];
                }
            });

            sortables[key].sort(function (a, b) {
                return a[1] - b[1];
            });

            sortables[key].reverse();
        });

        // remove undefined items from the sorted lists
        _.each(sortables, function (list, key) {
            sortables[key] = _.reject(list, function (thing) {
                return thing === undefined;
            });
        });

        // clear out charts
        // TODO: use d3 transitions
        $(["share_destinations", "interaction_types", "interaction_sources",
            "visitors_over_time", "sources_of_shares", "visitor_sources",
            "visitor_locations"]).each(function (i, val) {
                d3.select("#" + val + " svg").remove();
            });

        // clean out top lists
        $(["top_engaging_products", "top_shared_products",
            "top_videos", "top_engaged_content"]).each(function (i, val) {
                $("#" + val).html("");
            });

        var pids = _.pluck(sortables.engaged_products, 0);

        Willet.mediaAPI.getObjects("product", pids, function (current, total) {
            $(".progressbar").progressbar("value", Math.round(current / total * 100));
        }, function () {
            // hide progress bar and show data
            $(".section_metrics").slideDown();
            $(".progressbar").slideUp();
            $(".error").slideUp();

            var to_inject_lists = [
                {
                    params: {
                        type: "product",
                        selector: "#top_engaging_products",
                        verb: "interaction",
                        total: totals.interactions.product
                    },
                    data: sortables.engaged_products.slice(0, 4)
                },

                {
                    params: {
                        type: "content",
                        selector: "#top_engaged_content",
                        verb: "interaction",
                        total: totals.interactions.content
                    },
                    data: sortables.engaged_content.slice(0, 4)
                },

                {
                    params: {
                        type: "product",
                        selector: "#top_shared_products",
                        verb: "share",
                        total: totals.shares
                    },
                    data: sortables.sharing_products.slice(0, 4)
                },

                {
                    params: {
                        type: "video",
                        selector: "#top_videos",
                        verb: "play",
                        total: data.engagement['content-video'].totals.date.all
                    },
                    data: sortables.engaged_videos.slice(0, 3)
                },

                {
                    params: {
                        type: "bar_chart",
                        selector: "#share_destinations",
                        total: totals.shares,
                        row_height: 20,
                        width: 300
                    },
                    data: sortables.sharing_source
                },

                {
                    params: {
                        type: "bar_chart",
                        selector: "#interaction_types",
                        total: totals.interactions.all,
                        row_height: 20,
                        width: 220
                    },
                    data: sortables.interaction_types
                },

                {
                    params: {
                        type: "bar_chart",
                        selector: "#visitor_sources",
                        total: totals.visitors,
                        row_height: 20,
                        width: 620
                    },
                    data: sortables.visitor_source
                },

                {
                    params: {
                        type: "bar_chart",
                        selector: "#visitor_locations",
                        total: totals.visitors,
                        row_height: 20,
                        width: 620
                    },
                    data: sortables.visitor_locations.slice(0, 10)
                },

                {
                    params: {
                        type: "bar_chart",
                        selector: "#interaction_sources",
                        total: totals.interactions.all,
                        row_height: 20,
                        width: 220
                    },
                    data: sortables.interaction_source
                },

                {
                    params: {
                        type: "bar_chart",
                        selector: "#sources_of_shares",
                        total: totals.shares,
                        row_height: 20,
                        width: 300
                    },
                    data: sortables.sharing_sources_of
                },

                {
                    params: {
                        type: "column_chart",
                        selector: "#visitors_over_time",
                        min_width: 540,
                        col_width: 20,
                        height: 200
                    },
                    data: sortables.visitor_dates
                },

                {
                    params: {
                        type: "single_value",
                        selector: "#total_visitors"
                    },
                    data: totals.visitors
                },

                {
                    params: {
                        type: "single_value",
                        selector: "#total_pageviews"
                    },
                    data: totals.pageviews
                },

                {
                    params: {
                        type: "single_value",
                        selector: "#bounce_rate"
                    },
                    data: bounce_rate.toFixed(2) + "%"
                }
            ];

            _.each(to_inject_lists, function (inject) {
                if (typeof inject.data === 'object' && inject.data.length == 0 || inject.data === undefined) {
                    $("[data-metric='" + inject.params.selector.slice(1) + "']").show();
                } else {
                    $("[data-metric='" + inject.params.selector.slice(1) + "']").hide();
                }

                // if we're injecting a chart or a single value
                if (inject.params.type.indexOf("_chart") != -1 || inject.params.type === "single_value") {
                    insertAnalytics({
                        params: inject.params,
                        data: inject.data
                    });

                } else {
                    // if we're injecting a list
                    _.each(inject.data, function (pair) {
                        insertAnalytics({
                            params: inject.params,
                            pair: pair,
                            data: inject.data
                        });
                    });
                }
            });
        });
    };

    setUpListeners = function () {
        // ajax loading indicator
        $(".progressbar").progressbar({
            value: false,
            change: function () {
                $(".progress-label").text($(".progressbar").progressbar("value") + "%");
            },
            complete: function () {
                $(".progress-label").text("Loaded.");
            }
        });

        // select analytics category ui
        $(".section_overview_block").click(function () {
            $(".data_category").hide();
            $("div[data-cid='" + $(this).data("cid") + "']").show();

            $(".section_overview_block").removeClass("selected");
            $(this).addClass("selected");
        });

        // change date range
        $(".range").change(function () {
            loadAnalytics();
        });

        // change campaign from the top menu
        $("#campaign_list").change(function () {
            loadAnalytics({
                'campaign_id': $(this).find("option:selected").attr("value")
            });
        });
    };

    init = function (newSettings) {
        settings = newSettings;
        // create UI and event listeners
        setUpListeners();

        // load and inject data
        loadAnalytics();
    };

    return {
        "init": init
    };
}(jQuery));