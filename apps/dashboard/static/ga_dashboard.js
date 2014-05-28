/*globals google */
/**
 * Created by tristanpotter on 2014-05-22.
 */
var table = 83581767; //gap table id. for google analytics.

$(document).ready(function () {
    "use strict";
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
        }
    };
    var refreshRate = 50000;
    var pageOptions = {
        quicklook: {
            current_selection: 'total',
            current_timeout: -1,
            refresh_rate: refreshRate, // not used
            today: {
                response: undefined,
                start_date: 'yesterday',
                end_date: 'today',
                current_timeout: -1, // if decide to make this on a graph basis
                refresh_rate: refreshRate // not used
            },
            total: {
                response: undefined,
                start_date: '2014-04-25',
                end_date: 'today',
                current_timeout: -1,
                refresh_rate: refreshRate
            }
        },
        sortview: {
            current_selection: 'device',
            current_timeout: -1,
            refresh_rate: refreshRate, //not currently used
            device: {
                response: undefined,
                start_date: '2014-04-25',
                end_date: 'today'
            },
            source: {
                response: undefined,
                start_date: '2014-04-25',
                end_date: 'today'
            }
        }
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


    /**
     * Refreshes the quicklook area with appropriate information
     * @param {optional object} response - the response to use to update the quicklook.
     */
    var refresh_quicklook = function (response) {
        if (response === undefined) {
            response = pageOptions.quicklook.current_selection === 'today' ?
                pageOptions.quicklook.today.response :
                pageOptions.quicklook.total.response;
        }
        // if response is still undefined, abort
        if (response === undefined) {
            return;
        }

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

        var data = new google.visualization.DataTable(response.dataTable, 0.6);
        var sparkline = new google.visualization.LineChart($('#quicklook-graph')[0]);

        var sparkline_data = data.clone();
        sparkline_data.removeColumns(2, 5);

        sparkline.draw(sparkline_data, CHART_OPTIONS.sparkline);
    };

    /**
     * Gets the data for the quicklook, and stores it in pageOptions_quicklook
     */
    var datify_quicklook = function () {
        var metrics = "ga:sessions,ga:bounceRate,ga:avgSessionDuration,ga:goalConversionRateAll,ga:goalCompletionsAll,ga:goal2Completions,ga:bounces";
        /* Dimensions are nthHour for total, nthMinute for today*/

        // populate data
        retrieveData(metrics, 'ga:nthMinute',
            pageOptions.quicklook.today.start_date,
            pageOptions.quicklook.today.end_date,
            function (response) {
                // save the response in the correct variable
                pageOptions.quicklook.today.response = response;
            });

        retrieveData(metrics, 'ga:dateHour',
            pageOptions.quicklook.total.start_date,
            pageOptions.quicklook.total.end_date,
            function (response) {
                // save the response in the correct variable
                pageOptions.quicklook.total.response = response;
            });
    };

    /**
     * Update the quicklook area with the most recent data from the server with the start and end dates given.
     * This function is on a timer, and will be called periodically
     */
    var update_quicklook = function () {
        // Get data
        datify_quicklook();

        // Update the elements
        refresh_quicklook();

        if (pageOptions.quicklook.current_timeout !== -1) {
            clearTimeout(pageOptions.quicklook.current_timeout);
        }
        pageOptions.quicklook.current_timeout = setTimeout(update_quicklook, refreshRate);
    };

    var refresh_sortview = function (response) {
        if (response === undefined) {
            response = pageOptions.sortview.current_selection === 'source' ?
                pageOptions.sortview.source.response :
                pageOptions.sortview.device.response;
        }
        // if response is still undefined, abort
        if (response === undefined) {
            return;
        }


        var data = new google.visualization.DataTable(response.dataTable, 0.6);
        var columnChart = new google.visualization.ColumnChart($('#sortview-graph')[0]);

        columnChart.draw(data); //add CHART_OPTIONS.columnchart at some point
    };

    var datify_sortview = function () {
        var metrics = ['ga:sessions', '' +
            'ga:bounceRate',
            'ga:avgSessionDuration',
            'ga:goalConversionRateAll',
            'ga:goalCompletionsAll',
            'ga:goal2Completions',
            'ga:bounces'];
        metrics = "ga:sessions,ga:bounces";
        /*Dimensions are modified by user*/

        // populate data
        retrieveData(metrics.join(','), 'ga:deviceCategory',
            pageOptions.sortview.device.start_date,
            pageOptions.sortview.device.end_date,
            function (response) {
                // save the response in the correct variable
                pageOptions.sortview.device.response = response;
            });

        retrieveData(metrics, 'ga:medium',
            pageOptions.sortview.source.start_date,
            pageOptions.sortview.source.end_date,
            function (response) {
                // save the response in the correct variable
                pageOptions.sortview.source.response = response;
            });
    };

    var update_sortview = function () {
        // Get Data
        datify_sortview();
        // update elements
        refresh_sortview();

        if (pageOptions.sortview.current_timeout !== -1) {
            clearTimeout(pageOptions.sortview.current_timeout);
        }
        pageOptions.sortview.current_timeout = setTimeout(update_sortview, refreshRate);
    };

    var refresh_all = function () {
        refresh_quicklook();
        refresh_sortview();
    };

    var drawElements = function () {
        // all graphs are drawn in here
        //update_all_data();
        update_quicklook();
        update_sortview();
        refresh_all();

    };

    /**
     * Update the session graph area
     */

        // TODO make a function that populates all data on load


        // Start the sessions counts
    google.load('visualization', '1.0', {'packages': ['controls', 'corechart'], callback: drawElements});

    $('#quicklook-total').on('click', function () {
        pageOptions.quicklook.current_selection = 'total';
        refresh_quicklook();
    });

    $('#quicklook-today').on('click', function () {
        pageOptions.quicklook.current_selection = 'today';
        refresh_quicklook();
    });

    $('#sortview-device').on('click', function () {
        pageOptions.sortview.current_selection = 'device';
        refresh_sortview();
    });

    $('#sortview-source').on('click', function () {
        pageOptions.sortview.current_selection = 'source';
        refresh_sortview();
    });

});