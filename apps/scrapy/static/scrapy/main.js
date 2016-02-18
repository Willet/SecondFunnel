"use strict";

var get_data = function () {
    var line, lines, url, cat, priority,
        categories = {},
        warning = $('.warning'),
        delim = $('#delimiter').val(),
        csv = $('#pseudo-spreadsheet').val();
    
    lines = csv.split('\n').filter(function(x) {
        return x.trim().length > 0;
    });

    // will get some text in red letters if data doesn't validate
    warning.text('');

    for (var i=0; i < lines.length; i++) {
        line = lines[i].split(delim);
        console.log(line);
        // validation
        if (line.length != 3) {
            warning.text("<- Look you fool");
            return false;
        }

        url = line[0].trim();
        cat = line[1].trim(); // "" is valid
        priority = line[2].trim();

        // assemble the CSV into a js object to pass to server side handlers
        categories[cat] = categories[cat] || {urls: [], priorities: [], name: cat};
        categories[cat].urls.push(url);
        categories[cat].priorities.push(priority);
    }

    return categories;
};

// callback for "run" button
var scrape = function(create_tiles) {
    var cat,
        categories = get_data(),
        refresh_images = $('#refresh-images').prop('checked'),
        $results = $('.results').removeClass('success').removeClass('warning');

    if (!categories) {
        $results.addClass("warning");
        $results.html("Error validating data, see warning.");
        console.log("Error validating data, see warning.");
    } else {
        $results.html("Scraping...");
        console.log('Scraping...');

        // run each category separately
        for (cat in categories) {
            $results.html($results.html() + "\n Category: " + cat);
            console.log('Category: ' + cat);
            console.log(JSON.stringify(categories[cat]));
            $.ajax({
                url: urlAddPath('scrape'),
                type: 'POST',
                data: {
                    'cat': encodeURIComponent(JSON.stringify(categories[cat])),
                    'page': page,
                    'tiles': create_tiles,
                    'refresh_images': refresh_images
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
                    $results.html('\nScrape failed with status: ' + error);
                    console.warn('Scrape failed with status: ' + error);
                    console.warn(obj);
                }
            });
        }
    }
};

// callback for "prioritize" button
var prioritize = function() {
    var cat,
        categories = get_data(),
        $results = $('.results').removeClass('success').removeClass('warning');

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
                url: urlAddPath('prioritize'),
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
                    $results.html('\nPrioritize failed with status: ' + error);
                    console.warn('Prioritize failed with status: ' + error);
                    console.warn(obj);
                }
            });
        }
    }
};

var urlAddPath = function (path) {
    var url = urlParse(window.location.href).pathname;
    return url + ((url.slice(-1) !== '/') ? '/' + path : path);
};

var urlParse = function (url) {
    // Trick to parse url is to use location object of a-tag
    var path, port, a = document.createElement('a');
    a.href = url;
    path = a.pathname;

    // IE excludes the leading /
    if (path.length && path.charAt(0) !== '/') {
        path = '/' + path;
    }

    // Check if port is in url, because:
    // - Safari reports "0" when no port is in the href
    // - IE reports "80" when no port is in the href
    port = (url.indexOf(":" + a.port) > -1) ? a.port : "";

    // <protocol>//<hostname>:<port><pathname><search><hash>
    // hreft - complete url
    // host - <hostname>:<port>
    // origin - <protocal>//<hostname>:<port>
    return {
        'href':     a.href,
        'host':     a.host,
        'origin':   a.origin,
        'protocol': a.protocol,
        'hostname': a.hostname,
        'port':     port,
        'pathname': path, // if path, includes leading '/'
        'search':   a.search, // if search, includes leading '?'
        'hash':     a.hash // if hash, includes leading '#'
    };
};
