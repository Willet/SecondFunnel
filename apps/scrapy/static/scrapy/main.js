var prioritize = function(cat) {
    console.log('prioritizing: ' + cat.name);
    $.ajax({
        url: 'prioritize',
        type: 'GET',
        data: {
            cat: encodeURIComponent(JSON.stringify(cat))
        },
        success: function(data, status) {
            console.log('prioritize succeeded with status: ' + status);
        },
        error: function(obj, status, error) {
            console.warn('prioritize failed with status: ' + status);
            console.warn(obj);
        }
    });
};

var run = function() {
    var csv = $('#pseudo-spreadsheet').val();
    var lines = csv.split('\n');
    lines = lines.filter(function(x){
        return x.trim().length > 0;
    });
    var delim = $('#delimiter').val();
    var create_tiles = $('#create-tiles').prop('checked');
    var categories = {};

    var warning = $('.warning');
    warning.text('');

    for (var i=0; i < lines.length; i++) {
        line = lines[i].split(delim);

        // validation
        if (line.length != 3) {
            warning.text("<- Look you fool");
            return;
        }

        var url = line[0].trim(),
            cat = line[1].trim(),
            priority = line[2].trim();

        categories[cat] = categories[cat] || {urls: [], priorities: [], name: cat};
        categories[cat].urls.push(url);
        categories[cat].priorities.push(priority);
    }
    console.log('running');
    for (cat in categories) {
        console.log('category: ' + cat);
        $.ajax({
            url: 'scrape',
            type: 'GET',
            data: {
                'category': cat,
                'urls': encodeURIComponent(JSON.stringify(categories[cat].urls)),
                'page': page,
                'tiles': create_tiles
            },
            success: function(data, status) {
                console.log('scrape succeeded with status: ' + status);
                prioritize(categories[cat]);
            },
            error: function(obj, status, error) {
                console.warn('scrape failed with status: ' + status);
                console.warn(obj);
            }
        });
    }
};
