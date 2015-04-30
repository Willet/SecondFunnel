var summaryInterval;

var getData = function () {
    var task = this.event.target.id;
    var csv = $('#pseudo-spreadsheet').val();
    var lines = csv.split('\n');
    lines = lines.filter(function(x){
        return x.trim().length > 0;
    });
    var delim = $('#delimiter').val();
    var categories = {};

    // will get some text in red letters if data doesn't validate
    var warning = $('.warning');
    warning.text('');

    for (var i=0; i < lines.length; i++) {
        line = lines[i].split(delim);

        // validation with optional priority column
        if ((line.length !== 2 && line.length !== 3 && task === 'scrape') || (line.length !== 3 && task === 'prioritize')) {
            warning.text("<- Look you fool");
            return false;
        }

        var priority,
            url = line[0].trim(),
            cat = line[1].trim();
        // assemble the CSV into a js object to pass to server side handlers
        categories[cat] = categories[cat] || {urls: [], priorities: [], name: cat};
        categories[cat].urls.push(url);

        if (line.length === 3) {
            priority = line[2].trim();
            categories[cat].priorities.push(priority);
        }
    }

    return categories;
};

var formattedSummary = function(summary) {
    summaryText = "";
    if (summary['updated items']) {
        summaryText += '\nUpdated items: \n';
        for (i = 0; i < summary['updated items'].length; i++) {
            summaryText += '   - ' + summary['updated items'][i] + '\n';
        }
    }
    if (summary['new items']) {
        summaryText += '\nNew items: \n';
        for (i = 0; i < summary['new items'].length; i++) {
            summaryText += '   - ' + summary['new items'][i] + '\n';
        }
    }
    if (summary['out of stock']) {
        summaryText += '\nOut of stock: \n';
        for (i = 0; i < summary['out of stock'].length; i++) {
            summaryText += '   - ' + summary['out of stock'][i] + '\n';
        }
    }
    if (summary['dropped items']) {
        summaryText += '\nDropped items: \n';
        for (i = 0; i < summary['dropped items'].length; i++) {
            summaryText += '   - ' + summary['dropped items'][i] + '\n';
        }
    }
    if (summary['prioritized items']) {
        summaryText += '\nPrioritized items: \n';
        for (i = 0; i < summary['prioritized items'].length; i++) {
            summaryText += '   - ' + summary['prioritized items'][i] + '\n';
        }
    }

    return summaryText;
};

var taskReq = {
    success: function(data, status) {
        var counter = 1;
        var $results = $('.results').removeClass('success').removeClass('warning');
        // polling every 30s for summary
        summaryInterval = setInterval(function() {
            console.log("Polling attempt #" + counter);
            $.ajax({
                url: 'result/' + data.id,
                type: 'GET',
                success: summaryReq.success,
                error: summaryReq.error
            });
            // stop polling after 30m
            if (counter == 60) {
                clearInterval(summaryInterval);
                $results.addClass('warning');
                $results.html('\nTask incomplete within 30m time limit, could not grab summary.');
                console.warn('Task incomplete within 30m time limit, could not grab summary.');
            } else {
                counter++;
            }
        }, 30000);
        console.log(data);
    },
    error: function(obj, status, error) {
        var $results = $('.results').removeClass('success').removeClass('warning');
        $results.addClass('warning');
        $results.html('\nTask failed with status: ' + status);
        console.warn('Task failed with status: ' + status);
        console.warn(obj);
    }
}

var summaryReq = {
    success: function(data, status) {
        var $results = $('.results').removeClass('success').removeClass('warning');
        // check if summary is empty
        if (Object.keys(data.summary).length > 0) {
            if (data.complete) {
                clearInterval(summaryInterval);
            }
            if (!$results.hasClass('warning')) {
                $results.addClass('success');
            }
            $results.html('Task succeeded!\n' + formattedSummary(data.summary));
            console.log('Task succeeded with status: ' + status);
            console.log(data);
        } else {
            console.log('Still waiting for summary...');
            console.log(data);
        }
    },
    error: function(obj, status, error) {
        var $results = $('.results').removeClass('success').removeClass('warning');
        clearInterval(summaryInterval);
        $results.addClass('warning');
        $results.html('\nFailed to grab summary with status: ' + status);
        console.warn('Failed to grab summary with status: ' + status);
        console.warn(obj);
    }
}

// callback for "run" button
var scrape = function() {
    var categories = getData();
    var skip_tiles = $('#data-only').prop('checked');
    var $results = $('.results').removeClass('success').removeClass('warning');

    // First, clear any existing interval
    clearInterval(summaryInterval);

    if (!categories) {
        $results.addClass("warning");
        $results.html("Error validating data, see warning.");
        console.log("Error validating data, see warning.");
    } else {
        $results.html("Scraping...please be patient. May take up to 30mins.");
        console.log('Scraping...');

        // run each category separately (spiders only take one set of categories at a time)
        for (cat in categories) {
            $results.html($results.html() + "\n Category: " + cat);
            console.log('Category: ' + cat);
            $.ajax({
                url: 'scrape',
                type: 'POST',
                data: {
                    'cat': encodeURIComponent(JSON.stringify(categories[cat])),
                    'page': page,
                    'tiles': !skip_tiles
                },
                success: taskReq.success,
                error: taskReq.error
            });
        }
    }
};

// callback for "prioritize" button
var prioritize = function() {
    var categories = getData();
    var $results = $('.results').removeClass('success').removeClass('warning');

    if (!categories) {
        $results.addClass("warning");
        $results.html("Error validating data, see warning.");
        console.log('Error validating data, see warning.');
    } else {
        $results.html('Prioritizing...');
        console.log('Prioritizing...');
        for (cat in categories) {
            $results.html($results.html() + "\n Category: " + cat);
            console.log('Category: ' + cat);
            $.ajax({
                url: 'prioritize',
                type: 'POST',
                data: {
                    'cat': encodeURIComponent(JSON.stringify(categories[cat])),
                    'page': page
                },
                success: taskReq.success,
                error: taskReq.error
            });
        }
    }
};
