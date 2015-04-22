var get_data = function () {
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

        // validation
        if (line.length != 3) {
            warning.text("<- Look you fool");
            return false;
        }

        var url = line[0].trim(),
            cat = line[1].trim(),
            priority = line[2].trim();

        // assemble the CSV into a js object to pass to server side handlers
        categories[cat] = categories[cat] || {urls: [], priorities: [], name: cat};
        categories[cat].urls.push(url);
        categories[cat].priorities.push(priority);
    }

    return categories;
};

// callback for "run" button
var scrape = function() {
    var categories = get_data();
    var create_tiles = $('#create-tiles').prop('checked');
    var $results = $('.results').removeClass('success').removeClass('warning');

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
                type: 'GET',
                data: {
                    'cat': encodeURIComponent(JSON.stringify(categories[cat])),
                    'page': page,
                    'tiles': create_tiles
                },
                success: function(data, status) {
                    var counter = 1;
                    // polling every 30s for summary
                    var summaryInterval = setInterval(function() {
                        console.log("Polling attempt #" + counter);
                        $.ajax({
                            url: 'summary/' + data.id,
                            type: 'GET',
                            data: {
                                'job_id': data.id,
                                'page': page
                            },
                            success: function(data, status) {
                                if (data.summary.length > 0) {
                                    clearInterval(summaryInterval);
                                    if (!$results.hasClass('warning')) {
                                        $results.addClass('success');
                                    }
                                    $results.html($results.html() + '\nSuccess! Summary: \n' + data.summary);
                                    console.log('Scrape succeeded with status: ' + status);
                                } else {
                                    console.log('Still waiting for summary...');
                                }
                            },
                            error: function(obj, status, error) {
                                clearInterval(summaryInterval);
                                $results.addClass('warning');
                                $results.html('\nFailed to grab summary with status: ' + status);
                                console.warn('Failed to grab summary with status: ' + status);
                                console.warn(obj);
                            }
                        });
                        // stop polling after 30m
                        if (counter == 60) {
                            clearInterval(summaryInterval);
                            $results.addClass('warning');
                            $results.html('\nScrape task incomplete within 30m time limit, could not grab summary.');
                            console.warn('Scrape task incomplete within 30m time limit, could not grab summary.');
                        } else {
                            counter++;
                        }
                    }, 30000);
                    console.log(data);
                },
                error: function(obj, status, error) {
                    $results.addClass('warning');
                    $results.html('\nScrape failed with status: ' + status);
                    console.warn('Scrape failed with status: ' + status);
                    console.warn(obj);
                }
            });
        }
    }
};

// callback for "prioritize" button
var prioritize = function() {
    var categories = get_data();
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
                type: 'GET',
                data: {
                    'cat': encodeURIComponent(JSON.stringify(categories[cat])),
                    'page': page
                },
                success: function(data, status) {
                    if (!$results.hasClass('warning')) {
                        $results.addClass('success');
                    }
                    $results.html($results.html() + '\nPrioritize succeeded with status:' + status);
                    console.log('Prioritize succeeded with status: ' + status);
                },
                error: function(obj, status, error) {
                    $results.addClass('warning');
                    $results.html('\nPrioritize failed with status: ' + status);
                    console.warn('Prioritize failed with status: ' + status);
                    console.warn(obj);
                }
            });
        }
    }
};
