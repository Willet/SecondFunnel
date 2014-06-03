/*globals google */
/**
 * Created by tristanpotter on 2014-05-22.
 */

$(document).ready(function () {
    "use strict";
    // TODO move this to server
    var table = 83581767; //gap table id. for google analytics.
    var console = window.console;
    var CHART_OPTIONS = {
        sparkline: {
            'axisTitlesPosition': 'none',
            'dataOpacity': 0,
            'hAxis': {
                'baselineColor': '#ffffff',
                'textPosition': 'none',
                'textStyle': {color: '#ffffff'},
                'gridlines': {
                    color: '#ffffff'
                }
            },
            'legend': {
                'position': 'top'
            },
            'lineWidth': 1,
            'vAxis': {
                'baselineColor': '#ffffff',
                'textPosition': 'none',
                'textStyle': {color: '#ffffff'},
                'gridlines': {
                    color: '#ffffff'
                }
            }
        },
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
                    color: 'black'
                }
            },
            'legend': { 'position': 'top'},
            'lineWidth': 1,
            'vAxis': {
                'baselineColor': 'black',
                'textPosition': 'out',
                'textStyle': {color: 'black'},
                'gridlines': {
                    color: 'black'
                }
            }
        },
        columnChartStacked: {
            'axisTitlesPosition': 'none',
            'dataOpacity': 1,
            'hAxis': {
                'baselineColor': 'black',
                'textPosition': 'out',
                'textStyle': {color: 'black'},
                'gridlines': {
                    color: 'black'
                }
            },
            'legend': { 'position': 'top'},
            'lineWidth': 1,
            'vAxis': {
                'baselineColor': 'black',
                'textPosition': 'out',
                'textStyle': {color: 'black'},
                'gridlines': {
                    color: 'black'
                }
            },
            'isStacked' : true
        }
    };
    // The time between ajax calls to the server in milliseconds
    var refreshRate = 100000;
    var analyticsStart = '2014-05-02';
    var CHARTS = [];
    var pageOptions = {
        charts: []
    };


    /**
     * DashboardElement is a chart on the dashboard, an entity that shows information.
     * Must be added to an analytics group to be visible.
     * @param location
     * @param chartType
     * @param dataOperation
     * @param chartOptions
     * @param refreshRate
     * @returns {{current_selection: number, location: *, chartType: *, chartOptions: *, dataOperation: *, selections: Array, addSelection: addSelection}}
     * @constructor
     */
    var DashboardElement = function (location, chartType, dataOperation, chartOptions) {
        return {
            current_selection: 0,
            location: location,
            chartType: chartType,
            chartOptions: chartOptions,
            dataOperation: dataOperation,
            selections: [],
            addSelection: function (metrics, dimensions, start_date, end_date) {
                this.selections.push({
                    response: undefined,
                    metrics: metrics,
                    dimensions: dimensions,
                    start_date: start_date,
                    end_date: end_date
                });
            }
        };
    };

    /**
     * This is a chartType, like google.visualization.LineChart
     * For this chart, location is defined as an Array
     * TODO make all charts take location as an Array, extend google objects to make this happen
     * @param locations {Array of DOM elements} - an ordered set of the locations to place data
     * @returns {{location: *, draw: draw}}
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
            this.location.text(Math.round((parseFloat(data) + 0.00001) * 100) / 100);
        };
    };

    /**
     * Creates an analytics element. Must be added to an analytics group to be visible on the page.
     * TODO get rid of this eventually
     * @param name {String}
     * @param location {DOM element}
     * @param chartType {chartType object}
     * @param chartOptions {object}
     * @param refreshRate {integer}
     * @returns {}
     */
    var createAnalyticsElement = function (location, chartType, dataOperation, chartOptions) {
        var chart = DashboardElement(location, chartType, dataOperation, chartOptions);
        return chart;
    };

    var createAnalyticsGroup = function (name, arrayOfElements, refreshRate) {
        pageOptions.charts.push({
            members: arrayOfElements,
            setSelection : function(selection){
                for(var i = 0; i < this.members.length; i++){
                    var len = this.members[i].selections.length;
                    if(len >= selection){
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
     * Retrieves data from the server using AJAX. A JSON object is returned and passed to callback. See
     *  the Google Analytics documentation on the formatting of query values.
     * @param {string} metrics - the data that should be retrieved from the server ie. 'ga:sessions,ga:bounceRate'
     * @param {string} dimmension - the categories data should be divided into ie. 'ga:date,ga:source'
     * @param {string} start_date - the date when data should start ie analyticsStart or 'yesterday'
     * @param {string} end_date - the date when data should end ie '2014-05-25' or 'today'
     * @param {function} callback - function that gets called when the request is successful
     */
    var retrieveData = function (metrics, dimmension, start_date, end_date, queryName, callback) {
        $.ajax({
            url: "retrieve-data",
            data: {
                'table': table, //TODO add actual table values, move to server
                'metrics': metrics,
                'dimension': dimmension,
                'start-date': start_date,
                'end-date': end_date,
                'queryName': queryName
            },
            type: "GET", // TODO GET or PUSH?
            cache: false, // TODO if PUSH, is this necessary
            dataType: "json",
            success: callback,
            error: function (xhr, status, errorThrown) {
                console.log(errorThrown);
            }
        });
    };

    var checkResponse = function (groupNumber, chartNumber) {
        var chart = pageOptions.charts[groupNumber].members[chartNumber];
        // chooses data based on the set current_selection
        var response = chart.selections[chart.current_selection].response;
        if (response === undefined) {
            return false;
        }
        return response;
    };

    var drawChart = function (groupNumber) {
        var charts = pageOptions.charts[groupNumber].members;
        for (var chartNumber = 0; chartNumber < charts.length; chartNumber++) {
            var response = checkResponse(groupNumber, chartNumber);
            if (!response) {
                return;
            }
            var data = charts[chartNumber].dataOperation(response);
            var chart = new charts[chartNumber].chartType(charts[chartNumber].location);
            chart.draw(data, charts[chartNumber].chartOptions);
        }
    };

    /**
     * Gets the data for the quickview, and stores it in pageOptions_quickview
     */
    var datify = function (groupNumber) {
        /* Dimensions are nthHour for total, nthMinute for today*/
        var chartStorage = pageOptions.charts[groupNumber].members;
        var ajax_response = function (chartNumber, numSelection) {
            return function (response) {
                chartStorage[chartNumber].selections[numSelection].response = response;
            };
        };
        for (var chartNumber = 0; chartNumber < chartStorage.length; chartNumber++) {
            // populate data
            for (var i = 0; i < chartStorage[chartNumber].selections.length; i++) {
                retrieveData(
                    chartStorage[chartNumber].selections[i].metrics.join(','),
                    chartStorage[chartNumber].selections[i].dimensions.join(','),
                    chartStorage[chartNumber].selections[i].start_date,
                    chartStorage[chartNumber].selections[i].end_date,
                    'SomeQuerry', //TODO make actual value based on group
                    ajax_response(chartNumber, i));
            }
        }
    };

    var updateView = function (groupNumber) {
        // Get Data
        datify(groupNumber);
        // update elements
        drawChart(groupNumber);
        var timeout = pageOptions.charts[groupNumber].current_timeout;
        if (timeout !== -1) {
            clearTimeout(timeout);
        }
        pageOptions.charts[groupNumber].current_timeout = setTimeout(function () {
            updateView(groupNumber);
        }, pageOptions.charts[groupNumber].refresh_rate);
    };

    var update_all = function () {
        for (var groupNumber = 0; groupNumber < pageOptions.charts.length; groupNumber++) {
            updateView(groupNumber);
        }
    };

    var refresh_all = function () {
        for (var groupNumber = 0; groupNumber < pageOptions.charts.length; groupNumber++) {
            drawChart(groupNumber);
        }
    };

    var drawElements = function () {
        // all graphs are drawn in here
        var quickviewMetrics = [ //TODO remove this
            'ga:sessions', //metrics
            'ga:bounceRate',
            'ga:avgSessionDuration',
            'ga:goalConversionRateAll',
            'ga:goalCompletionsAll',
            'ga:goal2Completions',
            'ga:bounces'];
        var quickview_graph = createAnalyticsElement($('#quickview-graph')[0],
            google.visualization.LineChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6);
                return data;
            }, CHART_OPTIONS.sparkline, refreshRate);
        quickview_graph.addSelection(
            ['ga:sessions','ga:bounces'],
            ['ga:nthMinute'], // dimensions
            'today', 'today'); //start date, end date
        quickview_graph.addSelection(
            ['ga:sessions','ga:bounces'],
            ['ga:dateHour'], // dimensions
            analyticsStart, 'today'); //start date, end date

        var buttonSessionCount = createAnalyticsElement($('#sessionCount'), QuickLabel, function (response) {
            return response.totalsForAllResults['ga:sessions'];
        }, {});
        buttonSessionCount.addSelection(quickviewMetrics, ['ga:userType'], 'today', 'today');
        buttonSessionCount.addSelection(quickviewMetrics, ['ga:userType'], analyticsStart, 'today');

        var buttonBounceRate = createAnalyticsElement($('#bounceRate'), QuickLabel, function (response) {
            return response.totalsForAllResults['ga:bounceRate'];
        }, {});
        buttonBounceRate.addSelection(quickviewMetrics, ['ga:userType'], 'today', 'today');
        buttonBounceRate.addSelection(quickviewMetrics, ['ga:userType'], analyticsStart, 'today');

        var buttonConversionRate = createAnalyticsElement($('#conversionRate'), QuickLabel, function (response) {
            return response.totalsForAllResults['ga:goalConversionRateAll'];
        }, {});
        buttonConversionRate.addSelection(quickviewMetrics, ['ga:userType'], 'today', 'today');
        buttonConversionRate.addSelection(quickviewMetrics, ['ga:userType'], analyticsStart, 'today');

        var buttonSessionDuration = createAnalyticsElement($('#sessionDuration'), QuickLabel, function (response) {
            return response.totalsForAllResults['ga:avgSessionDuration'];
        }, {});
        buttonSessionDuration.addSelection(quickviewMetrics, ['ga:userType'], 'today', 'today');
        buttonSessionDuration.addSelection(quickviewMetrics, ['ga:userType'], analyticsStart, 'today');

        var buttonConversions = createAnalyticsElement($('#conversions'), QuickLabel, function (response) {
            return response.totalsForAllResults['ga:goalCompletionsAll'];
        }, {});
        buttonConversions.addSelection(quickviewMetrics, ['ga:userType'], 'today', 'today');
        buttonConversions.addSelection(quickviewMetrics, ['ga:userType'], analyticsStart, 'today');

        var buttonBuyNowClicks = createAnalyticsElement($('#buyNowClicks'), QuickLabel, function (response) {
            return response.totalsForAllResults['ga:goal2Completions'];
        }, {});
        buttonBuyNowClicks.addSelection(quickviewMetrics, ['ga:userType'], 'today', 'today');
        buttonBuyNowClicks.addSelection(quickviewMetrics, ['ga:userType'], analyticsStart, 'today');
        createAnalyticsGroup('QUICKVIEW', [quickview_graph, buttonBounceRate, buttonBuyNowClicks, buttonConversionRate,
            buttonConversions, buttonSessionCount, buttonSessionDuration], refreshRate);

        var sortview = createAnalyticsElement($('#sortview-graph')[0],
            google.visualization.ColumnChart, function (response) {
                var data = new google.visualization.DataTable(response.dataTable, 0.6);
                return data;
            }, CHART_OPTIONS.columnChart);
        sortview.addSelection(['ga:sessions', 'ga:bounces'], ['ga:deviceCategory'], analyticsStart, 'today');
        sortview.addSelection(['ga:sessions', 'ga:bounces'], ['ga:medium'], analyticsStart, 'today');
        createAnalyticsGroup('SORTVIEW', [sortview], refreshRate);

        var totalConversions = createAnalyticsElement($('#total-conversions-graph')[0],
        google.visualization.ColumnChart, function(response){
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.columnChartStacked);
        totalConversions.addSelection(['ga:goal1Completions','ga:goal2Completions', 'ga:goal3Completions'], ['ga:deviceCategory'], analyticsStart, 'today');
        totalConversions.addSelection(['ga:goal1Completions','ga:goal2Completions', 'ga:goal3Completions'], ['ga:source'], analyticsStart, 'today');
        createAnalyticsGroup('CONVERSIONS', [totalConversions], refreshRate);

        var metricsview = createAnalyticsElement($('#metrics-graph')[0],
        google.visualization.LineChart, function(response){
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.lineChart);
        metricsview.addSelection(['ga:sessions', 'ga:bounces'], ['ga:dateHour'], analyticsStart, 'today');
        metricsview.addSelection(['ga:avgSessionDuration'], ['ga:dateHour'], analyticsStart, 'today');
        metricsview.addSelection(['ga:goalCompletionsAll'], ['ga:dateHour'], analyticsStart, 'today');
        metricsview.addSelection(['ga:goal1Completions','ga:goal2Completions', 'ga:goal3Completions'], ['ga:dateHour'], analyticsStart, 'today');
        createAnalyticsGroup('METRICS', [metricsview], refreshRate);

        var goal1 = createAnalyticsElement($('#productPreview-graph')[0],
        google.visualization.LineChart, function(response){
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.lineChart);
        goal1.addSelection(['ga:goal1ConversionRate'], ['ga:dateHour'], analyticsStart, 'today');
        var goal2 = createAnalyticsElement($('#buyNow-graph')[0],
        google.visualization.LineChart, function(response){
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.lineChart);
        goal2.addSelection(['ga:goal2ConversionRate'], ['ga:dateHour'], analyticsStart, 'today');
        var goal3 = createAnalyticsElement($('#scrollRate-graph')[0],
        google.visualization.LineChart, function(response){
                return new google.visualization.DataTable(response.dataTable, 0.6);
            }, CHART_OPTIONS.lineChart);
        goal3.addSelection(['ga:goal3ConversionRate'], ['ga:dateHour'], analyticsStart, 'today');
        createAnalyticsGroup('GOALS', [goal1, goal2, goal3], refreshRate);

        update_all();
    };

    // TODO make a function that populates all data on load


    // Start the sessions counts
    google.load('visualization', '1.0', {'packages': ['controls', 'corechart'], callback: drawElements});

    // Buttons that change selection
    $('#quickview-total').on('click', function () {
        // number referencing the quickview grouping of charts
        var QUICKVIEW = CHARTS.indexOf('QUICKVIEW');
        pageOptions.charts[QUICKVIEW].setSelection(1); // 1 represents the quickview today chart
        drawChart(QUICKVIEW);
    });

    $('#quickview-today').on('click', function () {
        // number referencing the quickview grouping of charts
        var QUICKVIEW = CHARTS.indexOf('QUICKVIEW');
        pageOptions.charts[QUICKVIEW].setSelection(0); // 0 represents the quickview total chart
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

    $('#conversions-source').on('click', function(){
        // integer that references the conversions grouping of charts
        var CONVERSIONS = CHARTS.indexOf('CONVERSIONS');
        pageOptions.charts[CONVERSIONS].setSelection(1); // 1 represents the conversions by source graph
        drawChart(CONVERSIONS);
    });

    $('#conversions-device').on('click', function(){
        // integer that references the conversions grouping of charts
        var CONVERSIONS = CHARTS.indexOf('CONVERSIONS');
        pageOptions.charts[CONVERSIONS].setSelection(0); // 0 represents the conversions by device graph
        drawChart(CONVERSIONS);
    });

    $('#metrics-sessions').on('click', function(){
        // integer that references the metrics grouping of charts
        var METRICS = CHARTS.indexOf('METRICS');
        pageOptions.charts[METRICS].setSelection(0); // 0 represents the session metrics graph
        drawChart(METRICS);
    });
    $('#metrics-duration').on('click', function(){
        // integer that references the metrics grouping of charts
        var METRICS = CHARTS.indexOf('METRICS');
        pageOptions.charts[METRICS].setSelection(1); // 1 represents the avgSessionDuration metrics graph
        drawChart(METRICS);
    });
    $('#metrics-conversions').on('click', function(){
        // integer that references the metrics grouping of charts
        var METRICS = CHARTS.indexOf('METRICS');
        pageOptions.charts[METRICS].setSelection(2); // 2 represents the total conversions metrics graph
        drawChart(METRICS);
    });
    $('#metrics-goals').on('click', function(){
        // integer that references the metrics grouping of charts
        var METRICS = CHARTS.indexOf('METRICS');
        pageOptions.charts[METRICS].setSelection(3); // 3 represents the goals metrics graph
        drawChart(METRICS);
    });

    $(window).resize(function () {
        refresh_all();
    });
});