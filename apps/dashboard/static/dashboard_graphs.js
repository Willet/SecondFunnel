/*globals google, dashboard, _*/
/**
 * Created by tristanpotter on 2014-05-22.
 * JavaScript that constructs and populates the dashboard with data.
 */

$(document).ready(function () {
    "use strict";
    /**
     * Object that contains the settings for the various charts on the page. Can be edited to change
     * all charts of one type, and reduces duplication of code.
     * @type {{lineChart: {axisTitlesPosition: string, dataOpacity: number, legend: {position: string}, lineWidth: number}, columnChart: {axisTitlesPosition: string, dataOpacity: number, hAxis: {baselineColor: string, textPosition: string, textStyle: {color: string}, gridlines: {color: string}}, legend: {position: string}, lineWidth: number, vAxis: {baselineColor: string, textPosition: string, textStyle: {color: string}, gridlines: {color: string}}}, pieChart: {is3D: boolean, titleTextStyle: {fontName: string, fontSize: number, bold: boolean, italic: boolean}}, table: {page: string, pageSize: number, sortAscending: boolean}}}
     */
    var CHART_OPTIONS = {
            lineChart: {
                'axisTitlesPosition': 'none',
                'dataOpacity': 0,
                'legend': {
                    'position': 'top'
                },
                'lineWidth': 1
            },
            columnChart: {
                'axisTitlesPosition': 'none',
                'dataOpacity': 1,
                'hAxis': {
                    'baselineColor': 'black',
                    'textPosition': 'out',
                    'textStyle': {color: 'black'},
                    'gridlines': {
                        color: 'white'
                    }
                },
                'legend': { 'position': 'top'},
                'lineWidth': 1,
                'vAxis': {
                    'baselineColor': 'black',
                    'textPosition': 'out',
                    'textStyle': {color: 'black'},
                    'gridlines': {
                        color: 'white'
                    }
                }
            },
            pieChart: {
                is3D: true,
                titleTextStyle: {
                    fontName: 'Helvetica Neue, Arial, san-serif',
                    fontSize: 16,
                    bold: true,
                    italic: false
                }},
            table: {
                'page': 'enable',
                'pageSize': 10,
                'sortAscending': false
            }
        },
    // The time between ajax calls to the server in milliseconds
        refreshRate = 1000 * 60 * 5, // 1 second * 60 * 5 = 5 minutes
    // used for determining campaign period
        campaign = 'all',
    // for readability in click code TODO investigate how to remove
        CHARTS = [],
    // The options for each chart
        pageOptions = {
            charts: []
        },
    // The total sessions that have come to the property
        sessions = 1;

    var addTiles = function (response, dict) {
        var data = response.result,
            tiles = {};

        $.each(data, function (idx, obj) {
            var tile = {
                    'count': obj.result,
                    'imageUrl': obj['tile.url'],
                    'product': obj['product.name'],
                    'tileId': obj['tile.id'],
                    'url': obj['page.url'] + '#' + obj['tile.id']
                },
                tileId = obj['tile.id'],
                prevTile = tiles[tileId];


            if (prevTile) { // Merge
                tile.count += prevTile.count;
            }

            tiles[tileId] = tile;
        });

        return (dict)? tiles : $.map(tiles, function(value, index){return [value];});
    };

    var sortTiles = function (tiles) {
        return _.sortBy(_.values(tiles),
            function (item) {
                return -1 * item.count;
            });
    };

    /**
     * DashboardElement is a chart on the dashboard, an entity that shows information.
     * Must be added to an analytics group to be visible.
     * @param location {jQuery} - jQuery selector containing where the element is to be placed
     * @param chartType {class} - the information on how to draw the chart
     * @param dataOperation {function} - operations to perform on the response before drawing
     * @param chartOptions {object} - the options that dictate how the chart is drawn
     * @constructor
     */
    var DashboardElement = function (location, chartType, dataOperation, chartOptions) {
        this.current_selection = 0;
        this.location = location;
        this.chartType = chartType;
        this.chartOptions = chartOptions;
        this.dataOperation = dataOperation;
        this.selections = [];
        this.addSelection = function (queryName) {
            this.selections.push({
                response: undefined,
                queryName: queryName
            });
        };
    };

    /**
     * This is a chartType, like google.visualization.LineChart
     * For this chart, location is defined as an Array
     * TODO make all charts take location as an Array, extend google objects to make this happen
     * @param location {object} - a JQuery selector of where the label should be placed
     * @returns {{location: object, draw: draw}}
     * @constructor
     */
    var QuickLabel = function (location) {
        this.location = location;
        /**
         * Draws the chart (ie labels)
         * @param data {object} - an object gotten from the response, ie response.totalsForAllResults
         * @param options - unused, used to maintain compliance with standard
         */
        this.draw = function (data, options) {
            this.location.text(data);
        };
    };

    /**
     * This is a chartType, like google.visualization.LineChart
     * For this chart, location is defined as an Array
     * TODO make all charts take location as an Array, extend google objects to make this happen
     * @param location {object} - a JQuery selector of where the label should be placed
     * @returns {{location: object, draw: draw}}
     * @constructor
     */
    var Tile = function (location) {
        this.location = location;
        /**
         * Draws the chart (ie labels)
         * @param data {object} - an object gotten from the response.
         *      MUST CONTAIN THE FOLLOWING FIELDS: (either an array of items with these fields, or
         *          one instance of these fields
         *      obj.result,
         *      obj['tile.url'],
         *      obj['product.name'],
         *      obj['tile.id'],
         *      obj['page.url']
         * @param options - unused, used to maintain compliance with standard
         */
        this.draw = function (data, options) {
            this.location.html("");
            var draw_tile = function (data) {
                return "" +
                    "<div class='tile'>" +
                    "<div class='count'>" +
                    data.count +
                    "</div>" +
                    "<img src=" + data.imageUrl + ">" +
                    "<div class='data'>" +
                    "<span class='product'>" +
                    data.product +
                    "</span>" +
                    "<span class='id'>" +
                    "(<a href='" + data.url + "'>" +
                    data.tileId +
                    "</a>) " +
                    "</span>" +
                    "</div>" +
                    "</div>";
            };

            data = data.slice(0, 10);

            for (var i = 0; i < data.length; i++) {
                if (data[i]) {
                    this.location.append(draw_tile(data[i]));
                }
            }
        };
    };

    /**
     * Creates an 'analytics group', that is a group of charts that occupy a similar space and
     *  share properties, and may be drawn/changed all at once.
     *  Elements must be a part of a group to be drawn.
     *  This adds to pageOptions.charts, giving access of the chart to all functions in this scope.
     * @param name {string} - the name of the group, used for convenience in click controls
     * @param arrayOfElements {[DashboardElement]} - the elements that are a part of this group
     * @param refreshRate {int} - the time in milliseconds between update/draw calls
     */
    var createAnalyticsGroup = function (name, arrayOfElements, refreshRate) {
        pageOptions.charts.push({
            members: arrayOfElements,
            setSelection: function (selection) {
                for (var i = 0; i < this.members.length; i++) {
                    var len = this.members[i].selections.length;
                    if (len >= selection) {
                        this.members[i].current_selection = selection;
                    }
                }
            },
            current_timeout: -1,
            refresh_rate: refreshRate
        });
        CHARTS.push(name);
    };

    /**
     * Retrieves the requested data from the server (data being determined by campaign and query)
     * @param queryName
     * @param campaign
     * @param callback
     */
    var retrieveData = function (campaign, queryName, callback) {
        $.ajax({
            url: "retrieve-data",
            data: {
                'dashboard': dashboard,
                'campaign': campaign,
                'query_name': queryName
            },
            type: "GET", // TODO GET or PUSH?
            dataType: "json",
            success: callback,
            error: function (xhr, status, errorThrown) {
                window.console.log(errorThrown);
            }
        });
    };

    /**
     * Examines a response from the server stored in pageOptions to ensure it exists.
     * @param groupNumber {int} - the reference number for the group that the chart is a part of
     * @param chartNumber {int} - the reference number for the chart within the group
     * @returns {*} - false if no response, response if if exists
     */
    var checkResponse = function (groupNumber, chartNumber) {
        var chart = pageOptions.charts[groupNumber].members[chartNumber];
        // chooses data based on the set current_selection
        var response = chart.selections[chart.current_selection].response;
        if (response === undefined) {
            return false;
        }
        return response;
    };

    /**
     * Draws a group of charts (equivalent to refreshing the chart if it is already drawn)
     * @param groupNumber {int} - the
     */
    var drawChart = function (groupNumber) {
        var charts = pageOptions.charts[groupNumber].members;
        for (var chartNumber = 0; chartNumber < charts.length; chartNumber++) {
            var response = checkResponse(groupNumber, chartNumber);
            if (!response) {
                return;
            }
            var data = charts[chartNumber].dataOperation(response),
                chart = new charts[chartNumber].chartType(charts[chartNumber].location);
            chart.draw(data, charts[chartNumber].chartOptions);
        }
    };

    /**
     * Retrieves the data for a group of charts from the server.
     * @param groupNumber {int} - the reference number of a group of elements
     */
    var datify = function (groupNumber) {
        /* Dimensions are nthHour for total, nthMinute for today*/
        var total_response = [],
            chartStorage = pageOptions.charts[groupNumber].members,
            ajax_response = function (chartNumber, numSelection, type, last) {
                return function (response) {
                    if (type === 'ratio') {
                        total_response.push(response);
                        if (last) {
                            var q0s = addTiles(total_response[0], true), // previews in campaign_stats
                                q1s = addTiles(total_response[1], true); // impressions in campaign_stats

                            // Merge two sets...
                            var keys = _.intersection(
                                _.keys(q1s),
                                _.keys(q0s)
                            );

                            var finalResponse = [];

                            $.each(keys, function (idx, key) {
                                var q0, q1, ratioTile;
                                key = parseInt(key, 10);

                                q0 = q0s[key];
                                q1 = q1s[key];

                                ratioTile = _.extend({}, q0);
                                ratioTile.count = q0.count / q1.count;

                                finalResponse.push(ratioTile);
                            });

                            //finalResponse = sortTiles(finalResponse);

                            chartStorage[chartNumber].selections[numSelection].response = finalResponse;
                            drawChart(groupNumber);
                        }
                    } else if (type === 'regular') {
                        chartStorage[chartNumber].selections[numSelection].response = response;
                        drawChart(groupNumber);
                    }
                };
            };
        for (var chartNumber = 0; chartNumber < chartStorage.length; chartNumber++) {
            // populate data
            for (var i = 0; i < chartStorage[chartNumber].selections.length; i++) {
                var query = chartStorage[chartNumber].selections[i].queryName;
                var queryArray = query.split(':');
                if (queryArray[0] === 'ratio') {
                    var queries = queryArray[1].split(',');
                    total_response = [];
                    for (var j = 0; j < queries.length; j++) {
                        retrieveData(campaign, queries[j], ajax_response(chartNumber, i, 'ratio', (j === (queries.length - 1))));
                    }
                } else {
                    retrieveData(campaign, query, ajax_response(chartNumber, i, 'regular'));
                }
            }
        }
    };

    /**
     * Updates a group of charts by retrieving data and then drawing them.
     * This function calls itself on an interval based on the refresh rate
     * set in the group.
     * @param groupNumber {int} - the reference number for a group of elements
     */
    var updateView = function (groupNumber) {
        // Get Data
        datify(groupNumber);
        var timeout = pageOptions.charts[groupNumber].current_timeout;
        if (timeout !== -1) {
            clearTimeout(timeout);
        }
        pageOptions.charts[groupNumber].current_timeout = setTimeout(function () {
            updateView(groupNumber);
        }, pageOptions.charts[groupNumber].refresh_rate);
    };

    /**
     * Calls updateView for all group numbers that are added to the page
     * (ie present in pageOptions)
     */
    var update_all = function () {
        for (var groupNumber = 0; groupNumber < pageOptions.charts.length; groupNumber++) {
            updateView(groupNumber);
        }
    };

    /**
     * Re-draws all elements on the page by calling drawChart for all group numbers added to the page
     * (id present in pageOptions)
     */
    var refresh_all = function () {
        for (var groupNumber = 0; groupNumber < pageOptions.charts.length; groupNumber++) {
            drawChart(groupNumber);
        }
    };

    /**
     * Gets called when Google Visualization library is loaded. Define all charts in here.
     */
    var drawElements = function () {
        // These allow for the formatting of an entire column in a DataTable.
        var decimalFormat = new google.visualization.NumberFormat({'fractionDigits': 2}),
            numberFormat = new google.visualization.NumberFormat({'fractionDigits': 0}),
            percentFormat = new google.visualization.NumberFormat({'fractionDigits': 2, 'suffix': '%'});

        /**
         * Converts all columns in data to floats except for the first one (which is normally labels)
         * @param data {DataTable} - the table to be parsed
         */
        var parseDataTable = function (data) {
            for (var j = 1; j < data.getNumberOfColumns(); j++) {
                for (var i = 0; i < data.getNumberOfRows(); i++) {
                    data.setValue(i, j, parseFloat(data.getValue(i, j)));
                }
            }
        };

        /**---  Dashboard elements are created below here ---*/

        // The "At a glance:" line graph
        var quickview_graph = new DashboardElement($('#quickview-graph')[0],
            google.visualization.ColumnChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6);
                for (var i = 0; i < data.getNumberOfRows(); i++) {
                    var cellNum = parseFloat(data.getValue(i, 0));
                    // if string value is actually a number
                    if (!isNaN(cellNum) && cellNum !== undefined) {
                        //it is pm if hours from 12 onwards
                        var suffix = (cellNum >= 12) ? 'PM' : 'AM';
                        //only -12 from hours if it is greater than 12 (if not back at mid night)
                        cellNum = (cellNum > 12) ? cellNum - 12 : cellNum;
                        //if 00 then it is 12 am
                        cellNum = (cellNum === 0) ? 12 : cellNum;

                        data.setFormattedValue(i, 0, cellNum + ':00' + suffix);
                    }
                }
                return data;
            }, CHART_OPTIONS.columnChart);
        quickview_graph.addSelection('GA_quickview_total');
        quickview_graph.addSelection('GA_quickview_today');
        createAnalyticsGroup('QUICKVIEW', [quickview_graph], refreshRate);

        /*---  the blue label things at the top of the page  ---*/
        var buttonSessionCount = new DashboardElement($('#sessionCount'), QuickLabel, function (response) {
            var data = response.totalsForAllResults['ga:sessions'];
            sessions = parseInt(data, 10);
            // I have a thing for complicated regex okay?
            // http://stackoverflow.com/questions/2901102/how-to-print-a-number-with-commas-as-thousands-separators-in-javascript
            return data.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }, {});
        buttonSessionCount.addSelection('GA_sessionCount');

        // TODO investigate if this needs to be filtered to only new users
        // or if there is a better metric for this
        var buttonUniqueVisitors = new DashboardElement($('#uniqueVisitors'), QuickLabel, function (response) {
            var data = response.totalsForAllResults['ga:users'];
            return data.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }, {});
        buttonUniqueVisitors.addSelection('GA_uniqueVisitors');

        var buttonBounceRate = new DashboardElement($('#bounceRate'), QuickLabel, function (response) {
            var data = response.totalsForAllResults['ga:bounceRate'];
            return (Math.round((parseFloat(data) + 0.00001) * 100) / 100) + '%';
        }, {});
        buttonBounceRate.addSelection('GA_bounceRate');

        var buttonSessionDuration = new DashboardElement($('#sessionDuration'), QuickLabel, function (response) {
            var data = parseFloat(response.totalsForAllResults['ga:avgSessionDuration']),
                minutes = Math.floor(data / 60) + 'm',
                seconds = Math.round(data % 60) + 's';

            if (minutes === '0m') {
                minutes = '';
            }
            if (seconds === '0s') {
                seconds = '';
            }
            return minutes + seconds;
        }, {});
        buttonSessionDuration.addSelection('GA_sessionDuration');

        var buttonScrollRate = new DashboardElement($('#scrollRate'), QuickLabel, function (response) {
            var data = response.totalsForAllResults['ga:goal3ConversionRate'];
            return Math.round((parseFloat(data) + 0.00001) * 100) / 100 + '%';
        }, {});
        buttonScrollRate.addSelection('GA_scrollRate');

        var buttonPreviewRate = new DashboardElement($('#previewRate'), QuickLabel, function (response) {
            var data = response.totalsForAllResults['ga:goal1ConversionRate'];
            return Math.round((parseFloat(data) + 0.00001) * 100) / 100 + '%';
        }, {});
        buttonPreviewRate.addSelection('GA_previewRate');

        var buttonBuyNowRate = new DashboardElement($('#buyNowRate'), QuickLabel, function (response) {
            var data = response.totalsForAllResults['ga:goal2ConversionRate'];
            return Math.round((parseFloat(data) + 0.00001) * 100) / 100 + '%';
        }, {});
        buttonBuyNowRate.addSelection('GA_buyNowRate');

        var buttonPurchaseRate = new DashboardElement($('#purchaseRate'), QuickLabel, function (response) {
            // query failed
            if(response['entityId'] === undefined){
                return 'N/A';
            }
            // query exists, but convertedClicks === 0 (clickmeter doesn't return no-data)
            if(response['convertedClicks'] === undefined){
                return '0%';
            } else { // there are converted clicks
                var data = parseInt(response.convertedClicks, 10);
                return Math.round((((data / sessions) * 100) + 0.00001) * 100) / 100 + '%';
            }
        }, {});
        buttonPurchaseRate.addSelection('CM_purchaseRate');

        createAnalyticsGroup('BUTTONS', [buttonSessionCount, buttonUniqueVisitors, buttonBounceRate, buttonSessionDuration,
            buttonScrollRate, buttonPreviewRate, buttonBuyNowRate, buttonPurchaseRate], refreshRate);

        /*---  The pie chart in 'Traffic Information' ---*/
        var sortview = new DashboardElement($('#sortview-graph')[0],
            google.visualization.PieChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6);
                // make numbers actual numbers instead of strings so sorting works
                parseDataTable(data);
                numberFormat.format(data, 1);
                //console.log(data);
                return data;
            }, $.extend({}, CHART_OPTIONS.pieChart, {title: 'Sessions'}));
        sortview.addSelection('GA_sortview_device');
        sortview.addSelection('GA_sortview_user');
        createAnalyticsGroup('SORTVIEW', [sortview], refreshRate);

        /*---  The three pie charts in 'Total Conversions' area  ---*/
        var totalConversionsMobile = new DashboardElement($('#total-conversions-mobile-graph')[0],
            google.visualization.PieChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6),
                    view = new google.visualization.DataView(data);
                parseDataTable(data);
                view.setRows(data.getFilteredRows([
                    {'column': 0, 'value': 'Mobile'}
                ]));

                var output = new google.visualization.DataTable();
                output.addColumn('string', 'Goal');
                output.addColumn('number', 'Completions');
                var rows = [];
                for (var i = 1; i < view.getNumberOfColumns(); i++) {
                    rows.push([view.getColumnLabel(i), view.getValue(0, i)]);
                }
                output.addRows(rows);
                numberFormat.format(output, 1);
                return output;
            }, $.extend({}, CHART_OPTIONS.pieChart, {title: 'Mobile', legend: 'none'}));
        totalConversionsMobile.addSelection('GA_totalConversions');
        createAnalyticsGroup('CONVERSIONS', [totalConversionsMobile], refreshRate);

        var totalConversionsTablet = new DashboardElement($('#total-conversions-tablet-graph')[0],
            google.visualization.PieChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6),
                    view = new google.visualization.DataView(data);
                parseDataTable(data);
                view.setRows(data.getFilteredRows([
                    {'column': 0, 'value': 'Tablet'}
                ]));

                var output = new google.visualization.DataTable();
                output.addColumn('string', 'Goal');
                output.addColumn('number', 'Completions');
                var rows = [];
                for (var i = 1; i < view.getNumberOfColumns(); i++) {
                    rows.push([view.getColumnLabel(i), view.getValue(0, i)]);
                }
                output.addRows(rows);
                numberFormat.format(output, 1);
                return output;
            }, $.extend({}, CHART_OPTIONS.pieChart, {title: 'Tablet', legend: 'none'}));
        totalConversionsTablet.addSelection('GA_totalConversions');
        createAnalyticsGroup('CONVERSIONS', [totalConversionsTablet], refreshRate);

        var totalConversionsDesktop = new DashboardElement($('#total-conversions-desktop-graph')[0],
            google.visualization.PieChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6),
                    view = new google.visualization.DataView(data);
                parseDataTable(data);
                view.setRows(data.getFilteredRows([
                    {'column': 0, 'value': 'Desktop'}
                ]));


                var output = new google.visualization.DataTable();
                output.addColumn('string', 'Goal');
                output.addColumn('number', 'Completions');
                var rows = [];
                for (var i = 1; i < view.getNumberOfColumns(); i++) {
                    rows.push([view.getColumnLabel(i), view.getValue(0, i)]);
                }
                output.addRows(rows);
                numberFormat.format(output, 1);
                return output;
            }, $.extend({}, CHART_OPTIONS.pieChart, {title: 'Desktop', legend: 'none'}));
        totalConversionsDesktop.addSelection('GA_totalConversions');
        createAnalyticsGroup('CONVERSIONS', [totalConversionsDesktop], refreshRate);

        /*---  The two tables on the page  ---*/

        // the 'Traffic by Source' table
        var sourceTableTraffic = new DashboardElement($('#source-table-traffic')[0],
            google.visualization.Table, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6),
                    view = new google.visualization.DataView(data);

                // make numbers actual numbers instead of strings so sorting works
                parseDataTable(data);

                // format time
                var column = 3;
                for (var i = 0; i < data.getNumberOfRows(); i++) {
                    var minutes = Math.floor(data.getValue(i, column) / 60) + 'm',
                        seconds = Math.round(data.getValue(i, column) % 60) + 's';

                    if (minutes === '0m') {
                        minutes = '';
                    }
                    if (seconds === '0s') {
                        seconds = '';
                    }
                    data.setFormattedValue(i, column, minutes + ' ' + seconds);
                }
                view.hideColumns([4, 5, 6, 7, 8, 9, 10]);
                return view;
            }, $.extend({}, CHART_OPTIONS.table, {sortColumn: 1}));
        sourceTableTraffic.addSelection('GA_table_total');
        sourceTableTraffic.addSelection('GA_table_today');
        createAnalyticsGroup('TRAFFICTABLE', [sourceTableTraffic], refreshRate);

        // the 'Goals by Source' table
        var sourceTableGoals = new DashboardElement($('#source-table-goals')[0],
            google.visualization.Table, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6),
                    view = new google.visualization.DataView(data);

                // make numbers actual numbers instead of strings so sorting works
                parseDataTable(data);

                percentFormat.format(data, 5);
                percentFormat.format(data, 7);
                percentFormat.format(data, 9);

                view.hideColumns([1, 2, 3]);
                return view;
            }, $.extend({}, CHART_OPTIONS.table, {sortColumn: 2}));
        sourceTableGoals.addSelection('GA_table_total');
        sourceTableGoals.addSelection('GA_table_today');
        createAnalyticsGroup('GOALTABLE', [sourceTableGoals], refreshRate);

        /*---  'Metrics over time' graph at bottom of page  ---*/
        var metricsview = new DashboardElement($('#metrics-graph')[0],
            google.visualization.ColumnChart, function (response) {
                // TODO when data manipulation is completed on server side format this
                //  avg session time needs to be by #m#s and sessions/bounces formated
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.columnChart);
        metricsview.addSelection('GA_metricsview_traffic');
        metricsview.addSelection('GA_metricsview_sessionDuration');
        createAnalyticsGroup('METRICS', [metricsview], refreshRate);

        /*--- The three 'Goal over time' graphs ---*/
        var goal1 = new DashboardElement($('#productPreview-graph')[0],
            google.visualization.ColumnChart, function (response) {
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.columnChart);
        goal1.addSelection('GA_goals_previewRate');
        var goal2 = new DashboardElement($('#buyNow-graph')[0],
            google.visualization.ColumnChart, function (response) {
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.columnChart);
        goal2.addSelection('GA_goals_buyNowRate');
        var goal3 = new DashboardElement($('#scrollRate-graph')[0],
            google.visualization.ColumnChart, function (response) {
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.columnChart);
        goal3.addSelection('GA_goals_scrollRate');
        createAnalyticsGroup('GOALS', [goal1, goal2, goal3], refreshRate);

        var tileStatistics = new DashboardElement($('#tile-statistics'),
            Tile, function (response) {
                if (response['result'] === undefined) {
                    return sortTiles(response);
                } else {
                    return sortTiles(addTiles(response, false));
                }
            }, {});
        tileStatistics.addSelection('ratio:KN_tilePreview,KN_tileImpression');
        tileStatistics.addSelection('KN_tilePreview');
        tileStatistics.addSelection('KN_tileImpression');
        createAnalyticsGroup('TILESTATS', [tileStatistics], refreshRate);

        // Get the data and draw all these graphs
        update_all();
    };

    // TODO make a function that populates all data on load


    // Start everything up
    google.load('visualization', '1.0', {'packages': ['table', 'corechart'], callback: drawElements});

    $('#campaign').change(function () {
        campaign = $(this).val();
        update_all();
    }).change();

    // Buttons that change selection
    // TODO looking for a way to get rid of these
    $('#quickview-total').on('click', function () {
        // number referencing the quickview grouping of charts
        var QUICKVIEW = CHARTS.indexOf('QUICKVIEW');
        pageOptions.charts[QUICKVIEW].setSelection(0); // 0 represents the quickview total chart
        drawChart(QUICKVIEW);
    });
    $('#quickview-today').on('click', function () {
        // number referencing the quickview grouping of charts
        var QUICKVIEW = CHARTS.indexOf('QUICKVIEW');
        pageOptions.charts[QUICKVIEW].setSelection(1); // 1 represents the quickview today chart
        drawChart(QUICKVIEW);
    });

    $('#sortview-device').on('click', function () {
        // integer that references the sortview grouping of charts
        var SORTVIEW = CHARTS.indexOf('SORTVIEW');
        pageOptions.charts[SORTVIEW].setSelection(0); // 0 represents the sortview by device chart
        drawChart(SORTVIEW);
    });
    $('#sortview-source').on('click', function () {
        // integer that references the sortview grouping of charts
        var SORTVIEW = CHARTS.indexOf('SORTVIEW');
        pageOptions.charts[SORTVIEW].setSelection(1); // 1 represents the sortview by source chart
        drawChart(SORTVIEW);
    });

    $('#metrics-sessions').on('click', function () {
        // integer that references the metrics grouping of charts
        var METRICS = CHARTS.indexOf('METRICS');
        pageOptions.charts[METRICS].setSelection(0); // 0 represents the session metrics graph
        drawChart(METRICS);
    });
    $('#metrics-duration').on('click', function () {
        // integer that references the metrics grouping of charts
        var METRICS = CHARTS.indexOf('METRICS');
        pageOptions.charts[METRICS].setSelection(1); // 1 represents the avgSessionDuration metrics graph
        drawChart(METRICS);
    });

    $('#table-traffic-total').on('click', function () {
        // integer that references the table-traffic grouping of charts
        var TABLE = CHARTS.indexOf('TRAFFICTABLE');
        pageOptions.charts[TABLE].setSelection(0); // 0 represents the table that shows data for a month
        drawChart(TABLE);
    });
    $('#table-traffic-today').on('click', function () {
        // integer that references the table-traffic grouping of charts
        var TABLE = CHARTS.indexOf('TRAFFICTABLE');
        pageOptions.charts[TABLE].setSelection(1); // 1 represents the table that shows data for a day
        drawChart(TABLE);
    });

    $('#table-goals-total').on('click', function () {
        // integer that references the table-goal grouping of charts
        var TABLE = CHARTS.indexOf('GOALTABLE');
        pageOptions.charts[TABLE].setSelection(0); // 0 represents the table that shows data for a month
        drawChart(TABLE);
    });
    $('#table-goals-today').on('click', function () {
        // integer that references the table-goal grouping of charts
        var TABLE = CHARTS.indexOf('GOALTABLE');
        pageOptions.charts[TABLE].setSelection(1); // 1 represents the table that shows data for a day
        drawChart(TABLE);
    });

    $('#tiles-rate').on('click', function () {
        // integer that references the tile grouping of charts
        var TABLE = CHARTS.indexOf('TILESTATS');
        pageOptions.charts[TABLE].setSelection(0); // 0 represents the table that shows data for a month
        drawChart(TABLE);
    });
    $('#tiles-preview').on('click', function () {
        // integer that references the tile grouping of charts
        var TABLE = CHARTS.indexOf('TILESTATS');
        pageOptions.charts[TABLE].setSelection(1); // 0 represents the table that shows data for a month
        drawChart(TABLE);
    });
    $('#tiles-impression').on('click', function () {
        // integer that references the tile grouping of charts
        var TABLE = CHARTS.indexOf('TILESTATS');
        pageOptions.charts[TABLE].setSelection(2); // 0 represents the table that shows data for a month
        drawChart(TABLE);
    });

    // on resize, redraw all the charts
    $(window).resize(function () {
        refresh_all();
    });
});
