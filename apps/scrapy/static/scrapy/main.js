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
        $results.html("Scraping...");
        console.log('Scraping...');

        // run each category separately (spiders only take one set of categories at a time)
        for (cat in categories) {
            $results.html($results.html() + "\n Category: " + cat);
            console.log('Category: ' + cat);
            $.ajax({
                url: page + '/scrape',
                type: 'POST',
                data: {
                    'cat': encodeURIComponent(JSON.stringify(categories[cat])),
                    'page': page,
                    'tiles': create_tiles
                },
                success: function(data, status) {
                    if (!$results.hasClass('warning')) {
                        $results.addClass('success');
                    }
                    $results.html($results.html() + '\nScrape succeeded with status: ' + status);
                    console.log('Scrape succeeded with status: ' + status);
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
                url: page + '/prioritize',
                type: 'POST',
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
