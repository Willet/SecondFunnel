/*globals google */
/**
 * Created by tristanpotter on 2014-05-22.
 */

$(document).ready(function () {
    "use strict";
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
        }
    };
    var refreshRate = 30000;
    var CHARTS = [];
    var pageOptions = {
        charts: []
    };


    var DashboardChart = function (location, chartType, chartOptions, refreshRate) {
        return {
            current_selection: 0,
            current_timeout: -1,
            refresh_rate: refreshRate,
            location: location,
            chartType: chartType,
            chartOptions: chartOptions,
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
    var addChart = function (name, location, chartType, chartOptions, refreshRate) {
        var chart = DashboardChart(location, chartType, chartOptions, refreshRate);
        pageOptions.charts.push(chart); // push returns new length of array
        CHARTS.push(name);
        return chart;
    };

    /**
     * Retrieves data from the server using AJAX. A JSON object is returned and passed to callback. See
     *  the Google Analytics documentation on the formatting of query values.
     * @param {string} metrics - the data that should be retrieved from the server ie. 'ga:sessions,ga:bounceRate'
     * @param {string} dimmension - the categories data should be divided into ie. 'ga:date,ga:source'
     * @param {string} start_date - the date when data should start ie '2014-04-25' or 'yesterday'
     * @param {string} end_date - the date when data should end ie '2014-05-25' or 'today'
     * @param {function} callback - function that gets called when the request is successful
     */
    var retrieveData = function (metrics, dimmension, start_date, end_date, callback) {
        $.ajax({
            url: "retrieve-data",
            data: {
                'table': table, //TODO add actual table values, move to server
                'metrics': metrics,
                'dimension': dimmension,
                'start-date': start_date,
                'end-date': end_date
                // TODO add way for server to know which querry is being made
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

    var checkResponse = function (chartNumber) {
        var chart = pageOptions.charts[chartNumber];
        var response = chart.selections[chart.current_selection].response;
        if (response === undefined) {
            return false;
        }
        return response;
    };

    var drawChart = function (chartNumber, dataOperations) {
        var response = checkResponse(chartNumber);
        if (!response) {
            return;
        }
        var data = dataOperations(response);
        console.log(data);
        var chart = new pageOptions.charts[chartNumber].chartType(pageOptions.charts[chartNumber].location);
        chart.draw(data, pageOptions.charts[chartNumber].chartOptions);
    };

    /**
     * Gets the data for the quickview, and stores it in pageOptions_quickview
     */
    var datify = function (chartNumber) {
        /* Dimensions are nthHour for total, nthMinute for today*/
        var chartStorage = pageOptions.charts[chartNumber];
        var ajax_response = function (i) {
            return function (response) {
                chartStorage.selections[i].response = response;
            };
        };
        // populate data
        for (var i = 0; i < 2; i++) {
            retrieveData(
                chartStorage.selections[i].metrics.join(','),
                chartStorage.selections[i].dimensions.join(','),
                chartStorage.selections[i].start_date,
                chartStorage.selections[i].end_date,
                ajax_response(i));
        }
    };

    /**
     * Refreshes the quickview area with appropriate information
     * @param {optional object} response - the response to use to update the quickview.
     */
    var refresh_quickview = function () {
        var response = checkResponse(CHARTS.indexOf('QUICKVIEW'));
        if (!response) {
            return;
        }

        drawChart(CHARTS.indexOf('QUICKVIEW'), function (response) {
            var data = new google.visualization.DataTable(response.dataTable, 0.6);
            data.removeColumns(2, 5);
            return data;
        });

        // the buttons
        var totalSessions = response.totalsForAllResults['ga:sessions'];
        $('#sessionCount').text(totalSessions); // TODO format this number
        var bounceRate = Math.round((parseFloat(response.totalsForAllResults['ga:bounceRate']) + 0.00001) * 100) / 100;
        $('#bounceRate').text(bounceRate + '%');
        var sessionDuration = Math.round((parseFloat(response.totalsForAllResults['ga:avgSessionDuration']) + 0.00001) * 100) / 100;
        $('#sessionDuration').text(sessionDuration);
        var conversionRate = Math.round((parseFloat(response.totalsForAllResults['ga:goalConversionRateAll']) + 0.00001) * 100) / 100;
        $('#conversionRate').text(conversionRate + '%');
        var conversions = response.totalsForAllResults['ga:goalCompletionsAll'];
        $('#conversions').text(conversions);
        var buyNowClicks = response.totalsForAllResults['ga:goal2Completions'];
        $('#buyNowClicks').text(buyNowClicks);
    };

    var refresh_sortview = function () {
        drawChart(CHARTS.indexOf('SORTVIEW'), function (response) {
            var data = new google.visualization.DataTable(response.dataTable, 0.6);
            return data;
        });
    };

    var updateView = function (chartNumber, refreshFunction) {
        // Get Data
        datify(chartNumber);
        // update elements
        refreshFunction();
        var timeout = pageOptions.charts[chartNumber].current_timeout;
        if (timeout !== -1) {
            clearTimeout(timeout);
        }
        pageOptions.charts[chartNumber].current_timeout = setTimeout(function(){updateView(chartNumber,refreshFunction);}, refreshRate);
    };

    var refresh_all = function () {
        refresh_quickview();
        refresh_sortview();
    };

    var drawElements = function () {
        // all graphs are drawn in here
        var quickviewMetrics = [
            'ga:sessions', //metrics
            'ga:bounceRate',
            'ga:avgSessionDuration',
            'ga:goalConversionRateAll',
            'ga:goalCompletionsAll',
            'ga:goal2Completions',
            'ga:bounces'];
        var quickview = addChart('QUICKVIEW', $('#quickview-graph')[0],
            google.visualization.LineChart, CHART_OPTIONS.sparkline, refreshRate);
        quickview.addSelection(
            quickviewMetrics,
            ['ga:nthMinute'], // dimensions
            'today', 'today'); //start date, end date
        quickview.addSelection(
            quickviewMetrics,
            ['ga:dateHour'], // dimensions
            '2014-04-25', 'today'); //start date, end date

        var sortview = addChart("SORTVIEW", $('#sortview-graph')[0],
            google.visualization.ColumnChart, CHART_OPTIONS.columnChart, refreshRate);
        sortview.addSelection(['ga:sessions', 'ga:bounces'], ['ga:deviceCategory'], '2014-04-25', 'today');
        sortview.addSelection(['ga:sessions', 'ga:bounces'], ['ga:medium'], '2014-04-25', 'today');

        updateView(0, refresh_quickview);
        updateView(1, refresh_sortview);
        refresh_all();

    };

    // TODO make a function that populates all data on load


    // Start the sessions counts
    google.load('visualization', '1.0', {'packages': ['controls', 'corechart'], callback: drawElements});

    $('#quickview-total').on('click', function () {
        pageOptions.charts[CHARTS.indexOf('QUICKVIEW')].current_selection = 1;
        refresh_quickview();
    });

    $('#quickview-today').on('click', function () {
        pageOptions.charts[CHARTS.indexOf('QUICKVIEW')].current_selection = 0;
        refresh_quickview();
    });

    $('#sortview-device').on('click', function () {
        pageOptions.charts[CHARTS.indexOf('SORTVIEW')].current_selection = 0;
        refresh_sortview();
    });

    $('#sortview-source').on('click', function () {
        pageOptions.charts[CHARTS.indexOf('SORTVIEW')].current_selection = 1;
        refresh_sortview();
    });

    $(window).resize(function () {
        refresh_all();
    });
});