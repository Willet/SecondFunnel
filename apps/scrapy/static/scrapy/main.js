var a = 1;

var run = function() {
	var csv = $('#pseudo-spreadsheet').val();
	var lines = csv.split('\n');
	lines = lines.filter(function(x){
		return x.trim().length > 0;
	});
	var delim = $('#delimiter').val();

	var categories = {}

	var warning = $(".warning");
	warning.text("");

	for (var i=0; i<lines.length; i++) {
		line = lines[i].split(delim);

		// validation
		if (line.length != 3) {
			warning.text("<- Look you fool");
			return;
		}

		var url = line[0].trim(),
		    cat = line[1].trim(),
		    priority = line[2].trim();

		categories[cat] = categories[cat] || []
		categories[cat].push(url);
	}
 	console.log(encodeURIComponent(JSON.stringify(categories[cat])));
	for (cat in categories) {
		console.warn(1);
		$.ajax({
			url: "scrape",
			type: "GET",
			data: {
				'category': cat,
				'urls': encodeURIComponent(JSON.stringify(categories[cat]))
			},
			//dataType: "json",  // expected RETURN TYPE! (not type of "data" param)
			success: function(data, status) {
				console.warn(2);
				console.warn(status);
				console.warn(data);
				a = JSON.parse(data);
			},
			error: function(obj, status, error) {
				console.warn(obj);
				console.warn(status);
				console.warn(error);
			}
		})
	}
}
