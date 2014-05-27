var API_KEY = 'AIzaSyD8o-ZFDEP9jobWeKrwcTEliMoocskY7nY';
var CLIENT_ID = '231833496051-odkvfaplgj3ibonsvkn2ud2kjc5dlmtq.apps.googleusercontent.com';
var TABLE_ID = 'ga:83581767';
// Format of table ID is ga:xxx where xxx is the profile ID.

gadash.configKeys({
    'apiKey': API_KEY,
    'clientId': CLIENT_ID
});

// Get first query from google analytics
// Load the Visualization API and the piechart package.
google.load('visualization', '1.0', {'packages': ['corechart', 'controls'], callback: drawCharts});

// Set a callback to run when the Google Visualization API is loaded.
//google.setOnLoadCallback(drawCharts);


function drawCharts() {
    // session-graph
    // sessions on the page for the last 60 days
    new gadash.Chart({
        'type': 'LineChart',
        'divContainer': 'session-graph',
        'last-n-days': 1,
        'query': {
            'ids': TABLE_ID,
            'metrics': 'ga:sessions,ga:visitors',
            'dimensions': 'ga:date'
        },
        'chartOptions': {
            height: 600,
            title: 'Sessions in last 60 days',
            hAxis: {title: 'Date'},
            vAxis: {title: 'Sessions'}
        }
    }).render();

    // bounce-rate (uses google visualizations to draw chart, but gadash to make query
    new gadash.Chart({
        'type': 'LineChart',
        'divContainer': 'bounce-rate',
        'last-n-days': 1,
        'query': {
            'ids': TABLE_ID,
            'metrics': 'ga:bounceRate',
            'dimensions': 'ga:deviceCategory,ga:source',
            'output': 'dataTable'
        },
        'chartOptions': {
            height: 600,
            title: 'Sessions in last 60 days',
            hAxis: {title: 'Date'},
            vAxis: {title: 'Sessions'}

        },
        'view': {'columns' : [0,3]},

        'onSuccess': function (response) {
            var totalVisits = response.totalsForAllResults['ga:bounceRate'];

            // Update UI.
            document.getElementById('session_count').innerHTML = totalVisits;
            //console.log(totalVisits);
            line_chart(response.dataTable, "stag", 500, 500);
            // Continue rendering the chart as normal.
            // Note: this points to the instance of the Chart object from which the
            //       onSuccess function is called.
            //this.defaultOnSuccess(response);
        }
    }).render();

    // pizza
    drawChartDemo();

    //get data
    gapi.client.load('analytics', 'v3', function(){ console.log('loaded');});
    var request = gapi.client.analytics.get({
        'ids' : TABLE_ID,
        'start-date': '2014-03-01',
        'end-date' : 'today',
        'metrics': 'ga:sessions,ga:pageviews',
        'dimensions': 'ga:deviceCategory,ga:campaign',
        //'filters':''
        'fields': 'dataTable'
    });
    request.execute(function(response){ console.log(response);});
    //create dashboard
    //create control
    //create chart
    //bind control to chart
    //draw the dashboard
}


// Callback that creates and populates a data table,
// instantiates the pie chart, passes in the data and
// draws it.
function drawChartDemo() {

    // Create the data table.
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Topping');
    data.addColumn('number', 'Slices');
    data.addColumn('number', 'pieces')
    data.addRows([
        ['Mushrooms', 3,4],
        ['Onions', 1,6],
        ['Olives', 1,3],
        ['Zucchini', 1,1],
        ['Pepperoni', 2,9]
    ]);
    //console.log(data);
    // Set chart options
    var options = {'title': 'How Much Pizza I Ate Last Night',
        'width': 400,
        'height': 300};

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}

function line_chart(table, title, width, height) {

    var data = new google.visualization.DataTable(table, 0.6);

    // Set chart options
    var options = {'title': title,
        'width': width,
        'height': height};

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.ColumnChart(document.getElementById('bounce-rate'));
    chart.draw(data, options);
}
// Callback that creates and populates a data table,
// instantiates the pie chart, passes in the data and
// draws it.
