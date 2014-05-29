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
            'dataOpacity': 0,
            'hAxis': {
                'baselineColor': 'black',
                'textPosition': 'none',
                'textStyle': {color: 'black'},
                'gridlines': {
                    color: 'black'
                }
            },
            'lineWidth': 1,
            'vAxis': {
                'baselineColor': '#black',
                'textPosition': 'none',
                'textStyle': {color: '#black'},
                'gridlines': {
                    color: '#black'
                }
            }
        }
    };
    var refreshRate = 30000;
    var CHARTS = {
        QUICKVIEW: 0,
        SORTVIEW: 1
    };
    var pageOptions = {
        charts: [
            {// 0: quicklook
                current_selection: 0,
                current_timeout: -1,
                refresh_rate: refreshRate, // not used
                location: $('#quicklook-graph')[0],
                selections: [
                    { // today
                        response: undefined,
                        metrics: ['ga:sessions',
                            'ga:bounceRate',
                            'ga:avgSessionDuration',
                            'ga:goalConversionRateAll',
                            'ga:goalCompletionsAll',
                            'ga:goal2Completions',
                            'ga:bounces'],
                        dimensions: ['ga:nthMinute'],
                        start_date: 'today',
                        end_date: 'today'
                    },
                    { // total
                        response: undefined,
                        metrics: ['ga:sessions',
                            'ga:bounceRate',
                            'ga:avgSessionDuration',
                            'ga:goalConversionRateAll',
                            'ga:goalCompletionsAll',
                            'ga:goal2Completions',
                            'ga:bounces'],
                        dimensions: ['ga:dateHour'],
                        start_date: '2014-04-25',
                        end_date: 'today'
                    }
                ]
            },
            { // 1: sortview
                current_selection: 0,
                current_timeout: -1,
                refresh_rate: refreshRate, //not currently used
                location: $('#sortview-graph')[0],
                selections: [
                    { // device
                        response: undefined,
                        metrics: ['ga:sessions', 'ga:bounces'],
                        dimensions: ['ga:deviceCategory'],
                        start_date: '2014-04-25',
                        end_date: 'today'
                    },
                    { // medium/source
                        response: undefined,
                        metrics: ['ga:sessions', 'ga:bounces'],
                        dimensions: ['ga:medium'],
                        start_date: '2014-04-25',
                        end_date: 'today'
                    }
                ]
            }
        ]
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

    var drawChart = function (chartNumber, chartType, chartOptions, dataOperations) {
        var response = checkResponse(chartNumber);
        if (!response) {
            return;
        }
        var data = new google.visualization.DataTable(response.dataTable, 0.6);
        data = dataOperations(data);
        var chart = new chartType(pageOptions.charts[chartNumber].location);
        chart.draw(data, chartOptions);
    };

    /**
     * Refreshes the quicklook area with appropriate information
     * @param {optional object} response - the response to use to update the quicklook.
     */
    var refresh_quicklook = function () {
        var response = checkResponse(CHARTS.QUICKVIEW);
        if (!response) {
            return;
        }

        drawChart(CHARTS.QUICKVIEW, google.visualization.LineChart,
            CHART_OPTIONS.sparkline, function (data) {
                var nd = data.clone();
                nd.removeColumns(2, 5);
                return nd;
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

    /**
     * Gets the data for the quicklook, and stores it in pageOptions_quicklook
     */
    var datify = function (chartNumber) {
        /* Dimensions are nthHour for total, nthMinute for today*/

        var ajax_response = function (i) {
            return function (response) {
                pageOptions.charts[chartNumber].selections[i].response = response;
            };
        };
        // populate data
        for (var i = 0; i < 2; i++) {
            retrieveData(
                pageOptions.charts[chartNumber].selections[i].metrics.join(','),
                pageOptions.charts[chartNumber].selections[i].dimensions.join(','),
                pageOptions.charts[chartNumber].selections[i].start_date,
                pageOptions.charts[chartNumber].selections[i].end_date,
                ajax_response(i));
        }
    };

    /**
     * Update the quicklook area with the most recent data from the server with the start and end dates given.
     * This function is on a timer, and will be called periodically
     */
    var update_quicklook = function () {
        // Get data
        datify(CHARTS.QUICKVIEW);

        // Update the elements
        refresh_quicklook();

        if (pageOptions.charts[CHARTS.QUICKVIEW].current_timeout !== -1) {
            clearTimeout(pageOptions.charts[CHARTS.QUICKVIEW].current_timeout);
        }
        pageOptions.charts[CHARTS.QUICKVIEW].current_timeout = setTimeout(update_quicklook, refreshRate);
    };

    var refresh_sortview = function () {
        drawChart(CHARTS.SORTVIEW, google.visualization.ColumnChart,
            CHART_OPTIONS.columnChart, function(data){
            return data;
        });
    };

    var update_sortview = function () {
        // Get Data
        datify(CHARTS.SORTVIEW);
        // update elements
        refresh_sortview();

        if (pageOptions.charts[CHARTS.SORTVIEW].current_timeout !== -1) {
            clearTimeout(pageOptions.charts[CHARTS.SORTVIEW].current_timeout);
        }
        pageOptions.charts[CHARTS.SORTVIEW].current_timeout = setTimeout(update_sortview, refreshRate);
    };

    var refresh_all = function () {
        refresh_quicklook();
        refresh_sortview();
    };

    var drawElements = function () {
        // all graphs are drawn in here
        update_quicklook();
        update_sortview();
        refresh_all();

    };

    // TODO make a function that populates all data on load


    // Start the sessions counts
    google.load('visualization', '1.0', {'packages': ['controls', 'corechart'], callback: drawElements});

    $('#quicklook-total').on('click', function () {
        pageOptions.charts[CHARTS.QUICKVIEW].current_selection = 1;
        refresh_quicklook();
    });

    $('#quicklook-today').on('click', function () {
        pageOptions.charts[CHARTS.QUICKVIEW].current_selection = 0;
        refresh_quicklook();
    });

    $('#sortview-device').on('click', function () {
        pageOptions.charts[CHARTS.SORTVIEW].current_selection = 0;
        refresh_sortview();
    });

    $('#sortview-source').on('click', function () {
        pageOptions.charts[CHARTS.SORTVIEW].current_selection = 1;
        refresh_sortview();
    });

    $(window).resize(function () {
        refresh_all();
    });
});