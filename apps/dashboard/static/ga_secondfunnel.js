var API_KEY = 'AIzaSyD8o-ZFDEP9jobWeKrwcTEliMoocskY7nY';
var CLIENT_ID = '231833496051-odkvfaplgj3ibonsvkn2ud2kjc5dlmtq.apps.googleusercontent.com';
var TABLE_ID = 'ga:83581767';
// Format of table ID is ga:xxx where xxx is the profile ID.

gadash.configKeys({
    'apiKey': API_KEY,
    'clientId': CLIENT_ID
});

// session-graph
// sessions on the page for the last 60 days
var chart1 = new gadash.Chart({
    'type': 'LineChart',
    'divContainer': 'session-graph',
    'last-n-days': 60,
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
    },
    'onSuccess': function (response) {
        console.log(response.result.columnHeaders)
        this.defaultOnSuccess(response);
    }
}).render();

// bounce-rate
var chart2 = new gadash.Chart({
    'divContainer': 'bounce-rate',
    'last-n-days': 1,
    'query': {
        'ids': TABLE_ID,
        'metrics': 'ga:bounceRate',
        'dimensions': 'ga:date'
    },
    'onSuccess': function (response) {
        console.log(response);
        var totalVisits = response.totalsForAllResults['ga:bounceRate'];

        // Update UI.
        $('#bounce-rate').html(totalVisits);

        // Continue rendering the chart as normal.
        // Note: this points to the instance of the Chart object from which the
        //       onSuccess function is called.
    }
}).render();