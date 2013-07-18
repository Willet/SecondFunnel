Willet.analytics = (function ($) {
    "use strict";
    var settings, loadAnalytics, clearOutCharts,
        injectAnalyticsData, setUpListeners, init;

    loadAnalytics = function (obj) {
        // accepts an... object?
        obj = obj || {};

        var request = {
            "range": $(".range option:selected").val()
        };
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

    clearOutCharts = function () {
        // clear out charts
        // TODO: use d3 transitions
        _.each(["#share_destinations",
            "#interaction_types",
            "#interaction_sources",
            "#visitors_over_time",
            "#sources_of_shares",
            "#visitor_sources",
            "#visitor_locations"],
            function (elemId) {
                d3.select(elemId + " svg").remove();
            });

        // clean out top lists
        _.each(["#top_engaging_products",
            "#top_shared_products",
            "#top_videos",
            "#top_engaged_content"],
            function (elemId) {
                $(elemId).html("");
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

            mergeTotals = function (t1, t2) {
                var res = $.extend(true, {}, t1);

                // for (type in t2) {
                _.each(t2, function (typeVal, type) {
                    // for (key in t2[type]) {
                    _.each(typeVal, function (keyVal, key) {
                        res[type][key] = (res[type][key] || 0) + keyVal;
                    });
                });

                return res;
            },

            totals = {
                interactions: {
                    all: data.engagement['total-interactions'].totals.date.all,
                    product: data.engagement['product-interactions'].totals.date.all,
                    content: data.engagement['content-interactions'].totals.date.all
                },
                shares: data.sharing['total-shares'].totals.date.all,
                visitors: data.awareness['awareness-visitors'].totals.date.all,
                pageviews: data.awareness['awareness-pageviews'].totals.date.all,
                notbounces: data.engagement['total-no-bounces'].totals.date.all
            },

            bounceRate = (1 - totals.notbounces / totals.visitors) * 100,
            notBouncedVisitors,
            merged = {},
            pids,
            toMerge = {
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

            topLists;

        _.each(toMerge, function (list, key) {
            var reduce_start = mergeTotals(list[0], list[1]);

            merged[key] = _.reduce(list.slice(2), function (memo, item) {
                return mergeTotals(memo, item);
            }, reduce_start);
        });

        if (isNaN(bounceRate)) {
            bounceRate = 0;
        }

        notBouncedVisitors = totals.visitors - totals.visitors * bounceRate / 100;

        var getAnalyticsHandler = function (type) {
            var actions = {
                "common": function (apiType, template, params, pair, data_selector) {
                    if (pair === undefined) {
                        return;
                    }

                    Willet.mediaAPI.getObject(apiType, pair[0], function (data) {
                        var boxTemplate = _.template($(template).html()),
                            captionTemplate = _.template($("#count_with_percentage").html());

                        $(params.selector).append(boxTemplate({
                            data: data_selector(data),
                            name: data.name,
                            caption: captionTemplate({
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
                        if (image.indexOf("?Sig") !== -1) {
                            // remove amazon parameters
                            return image.slice(0, image.indexOf("?Sig"));
                        } else {
                            return image;
                        }
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

                "barChart": function (params, pair, allData) {
                    var chart = new Willet.charting.BarChart({
                        selector: params.selector,
                        data: allData,

                        total: params.total,

                        width: params.width,
                        rowHeight: params.rowHeight
                    });
                },

                "columnChart": function (params, pair, allData) {
                    // sort by date
                    allData.sort(function (a, b) {
                        return new Date(a[0]) - new Date(b[0]);
                    });

                    var chart = new Willet.charting.ColumnChart({
                        selector: params.selector,
                        data: allData,

                        minWidth: params.minWidth,
                        height: params.height,
                        colWidth: params.colWidth
                    });
                },

                "singleValue": function (params, pair, allData) {
                    var t = _.template($("#single_value_t").html());
                    $(params.selector).html(t({
                        value: allData
                    }));
                }
            };
            return actions[type];
        };

        var insertAnalytics = function (options) {
            // insert a piece of information on the page.
            // options includes "type"; allowed typesa are defined in
            // the actions variable.
            var params = options.params,
                pair = options.pair,
                allData = options.data,
                actions;

            if (!params.type) {
                Willet.mediator.fire('error', ['a data type must be specified']);
            } else {
                getAnalyticsHandler(params.type)(params, pair, allData);
            }
        };

        topLists = {
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
        // for (cat_slug in data) {
        _.each(data, function (category, cat_slug) {
            // for (metric_slug in data[cat_slug]) {
            _.each(category, function (metric, metric_slug) {
                // display totals in the sidebar on in the content section
                $(".metric_overview[data-metric='" + metric_slug + "']").html(
                    data[cat_slug][metric_slug].totals.date.all.toFixed(0)
                );
            });
        });

        // These metrics aren't calculated by the backend atm, hence the ugly implementation
        $(".per-visitor").remove();

        $(".section_overview_block:nth-child(2) .section_overview_metrics ul").append(
            "<li class='per-visitor'><span class='metric_overview' data-metric='interactions-per-visitor'>" + (totals.interactions.all / notBouncedVisitors || 0).toFixed(2) + "</span> Interactions per engaged visitor</li>");

        $(".section_overview_block:nth-child(3) .section_overview_metrics ul").append(
            "<li class='per-visitor'><span class='metric_overview' data-metric='shares-per-visitor'>" + (totals.shares / notBouncedVisitors || 0).toFixed(2) + "</span> Shares per visit</li>");

        $(".section_overview_block:nth-child(1) .section_overview_metrics ul").append(
            "<li class='per-visitor'><span class='metric_overview' data-metric='bounce-rate'>" + bounceRate.toFixed(2) + "%</span> Bounce Rate</li>");

        // construct lists of sorted (desc) (pid, count) pairs
        _.each(topLists, function (list, key) {
            sortables[key] = _.map(list, function (count, pid) {
                // meta metric would be what shows on the left hand side
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

        clearOutCharts();

        pids = _.pluck(sortables.engaged_products, 0);

        Willet.mediaAPI.getObjects("product", pids, function (current, total) {
            $(".progressbar").progressbar("value", Math.round(current / total * 100));
        }, function () {
            // hide progress bar and show data
            $(".section_metrics").slideDown();
            $(".progressbar").slideUp();
            $(".error").slideUp();

            var itemsToPopulate = [
                {
                    params: {
                        type: "product",
                        selector: "#top_engaging_products",
                        verb: "interaction",
                        total: totals.interactions.product
                    },
                    data: sortables.engaged_products.slice(0, 4)
                }, {
                    params: {
                        type: "content",
                        selector: "#top_engaged_content",
                        verb: "interaction",
                        total: totals.interactions.content
                    },
                    data: sortables.engaged_content.slice(0, 4)
                }, {
                    params: {
                        type: "product",
                        selector: "#top_shared_products",
                        verb: "share",
                        total: totals.shares
                    },
                    data: sortables.sharing_products.slice(0, 4)
                }, {
                    params: {
                        type: "video",
                        selector: "#top_videos",
                        verb: "play",
                        total: data.engagement['content-video'].totals.date.all
                    },
                    data: sortables.engaged_videos.slice(0, 3)
                }, {
                    params: {
                        type: "barChart",
                        selector: "#share_destinations",
                        total: totals.shares,
                        rowHeight: 20,
                        width: 300
                    },
                    data: sortables.sharing_source
                }, {
                    params: {
                        type: "barChart",
                        selector: "#interaction_types",
                        total: totals.interactions.all,
                        rowHeight: 20,
                        width: 220
                    },
                    data: sortables.interaction_types
                }, {
                    params: {
                        type: "barChart",
                        selector: "#visitor_sources",
                        total: totals.visitors,
                        rowHeight: 20,
                        width: 620
                    },
                    data: sortables.visitor_source
                }, {
                    params: {
                        type: "barChart",
                        selector: "#visitor_locations",
                        total: totals.visitors,
                        rowHeight: 20,
                        width: 620
                    },
                    data: sortables.visitor_locations.slice(0, 10)
                }, {
                    params: {
                        type: "barChart",
                        selector: "#interaction_sources",
                        total: totals.interactions.all,
                        rowHeight: 20,
                        width: 220
                    },
                    data: sortables.interaction_source
                }, {
                    params: {
                        type: "barChart",
                        selector: "#sources_of_shares",
                        total: totals.shares,
                        rowHeight: 20,
                        width: 300
                    },
                    data: sortables.sharing_sources_of
                }, {
                    params: {
                        type: "columnChart",
                        selector: "#visitors_over_time",
                        minWidth: 540,
                        colWidth: 20,
                        height: 200
                    },
                    data: sortables.visitor_dates
                }, {
                    params: {
                        type: "singleValue",
                        selector: "#total_visitors"
                    },
                    data: totals.visitors
                }, {
                    params: {
                        type: "singleValue",
                        selector: "#total_pageviews"
                    },
                    data: totals.pageviews
                }, {
                    params: {
                        type: "singleValue",
                        selector: "#bounce_rate"
                    },
                    data: bounceRate.toFixed(2) + "%"
                }
            ];

            // populate the page with actions required]
            _.each(itemsToPopulate, function (inject) {
                if (typeof inject.data === 'object' && inject.data.length == 0 || inject.data === undefined) {
                    $("[data-metric='" + inject.params.selector.slice(1) + "']").show();
                } else {
                    $("[data-metric='" + inject.params.selector.slice(1) + "']").hide();
                }

                // if we're injecting a chart or a single value
                if (inject.params.type.indexOf("Chart") !== -1 ||
                        inject.params.type === "singleValue") {
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