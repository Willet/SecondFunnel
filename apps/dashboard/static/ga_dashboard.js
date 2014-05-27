/*globals google */
/**
 * Created by tristanpotter on 2014-05-22.
 */
var table = 83581767;

$(document).ready(function () {
    "use strict";
    var console = window.console;
    var refreshRate = 100000;
    var page_options = {
        quicklook : {
            start_date : '2014-04-25',
            end_date: 'today',
            current_timeout: -1
        }
    };

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
            },
            complete: function (xhr, status) {
                console.log(status);
            }

        });
    };



    /**
     * Update the quicklook area with the most recent data from the server with the start and end dates given.
     * @param gets the dates from the page_options.quicklook object
     */
    var update_quicklook = function(){
        var startDate = page_options.quicklook.start_date;
        var endDate = page_options.quicklook.end_date;

        if(startDate === undefined){
            startDate = '2014-04-25'; //default start date in gap analytics
        }
        if(endDate === undefined){
            endDate = 'today';
        }

        var metrics = "ga:sessions,ga:bounceRate,ga:avgSessionDuration,ga:goalConversionRateAll,ga:goalCompletionsAll,ga:goal2Completions,ga:bounces"
        var dimension = 'ga:nthHour';
        if(parseFloat(endDate.replace('-', '')) - parseFloat(startDate.replace('-','')) < 15){
            dimension = 'ga:nthMinute';
        }

        var set_elements = function (response){
            console.log(response);

            var dashboard = new google.visualization.Dashboard($('#dash-quicklook')[0]);

            // the buttons
            var totalSessions = response.totalsForAllResults['ga:sessions'];
            $('#sessionCount').html(totalSessions); // TODO format this number
            var bounceRate = Math.round((parseFloat(response.totalsForAllResults['ga:bounceRate']) + 0.00001) * 100) / 100;
            $('#bounceRate').html(bounceRate + '%');
            var sessionDuration = Math.round((parseFloat(response.totalsForAllResults['ga:avgSessionDuration']) + 0.00001) * 100) / 100;
            $('#sessionDuration').html(sessionDuration);
            var conversionRate = Math.round((parseFloat(response.totalsForAllResults['ga:goalConversionRateAll']) + 0.00001) * 100) / 100;
            $('#conversionRate').html(conversionRate + '%');
            var conversions = response.totalsForAllResults['ga:goalCompletionsAll'];
            $('#conversions').html(conversions);
            var buyNowClicks = response.totalsForAllResults['ga:goal2Completions'];
            $('#buyNowClicks').html(buyNowClicks);

            var data = new google.visualization.DataTable(response.dataTable, 0.6);
            var sparkline = new google.visualization.LineChart($('#quicklook-graph')[0]);

            var sparkline_data = data.clone();
            sparkline_data.removeColumns(2, 5);

            var sparkline_options = {
                'axisTitlesPosition': 'none',
                'dataOpacity': 0,
                'hAxis.baselineColor': '#ffffff',
                'hAxis.textPosition': 'none',
                'hAxis.textStyle':{color:'#ffffff'},
                'hAxis.gridlines.color':'#ffffff',
                'lineWidth': 1,
                'vAxis.baselineColor': '#ffffff',
                'vAxis.gridlines.color': '#ffffff',
                'vAxis.textStyle':{color: '#ffffff'}

            };
            sparkline.draw(sparkline_data, sparkline_options);

            console.log(data);
            console.log(sparkline_data);


        };

        // data from april 25 2014, as that is the custom range set up for gap in analytics
        retrieveData(metrics, dimension, startDate, endDate, set_elements);
        if(page_options.quicklook.current_timeout !== -1){
            clearTimeout(page_options.quicklook.current_timeout);
        }
        page_options.quicklook.current_timeout = setTimeout(update_quicklook, refreshRate);

    };

    var drawElements = function(){
        // all graphs are drawn in here

        update_quicklook();
    };

    // TODO make a function that populates all data on load


    // Start the sessions counts
    google.load('visualization', '1.0', {'packages' : ['controls','corechart'], callback : drawElements});

    $('#quicklook-total').click(function(){
        console.log('quicklook-total was clicked');
        page_options.quicklook.start_date = '2014-04-25';
        page_options.quicklook.end_date = 'today';
        update_quicklook();
    });

    $('#quicklook-today').on('click', function(){
        console.log('quicklook-today was clicked');
        page_options.quicklook.start_date = 'yesterday';
        page_options.quicklook.end_date = 'today';
        update_quicklook();
    });

});