var Willet = Willet || {};

// requires d3, $, _
Willet.charting = (function () {
    "use strict";
    var BarChart = function (options) {
        var i, presentTotal = 0;

        // inject "Other" bar if necessary
        for (i = options.data.length - 1; i >= 0; i--) {
            if (options.data[i] === undefined) {
                options.data.splice(i, 1);
            } else {
                presentTotal += options.data[i][1];
            }
        }

        if (presentTotal < options.total) {
            options.data.push(["Other", options.total - presentTotal]);
        }

        var max_length = d3.max(options.data, function(val, i) {
            var label = val[0] + ": " + val[1];
            return label.length;
        });

        var w = options.width,
            h = options.row_height * options.data.length,
            label_width = max_length * 7;

        var x = d3.scale.linear()
            .domain([0, 100]);

        var chart = d3.select(options.selector).append("svg")
            .attr("class", "chart")
            .attr("width", w)
            .attr("height", h);

        chart.selectAll("rect")
            .data(options.data)
            .enter().append("rect")
                .attr("class", options.selector)
                .attr("x", label_width)
                .attr("y", function (d, i) { return i * options.row_height; })
                .attr("width", function (d) {
                    var len = (d[1] / options.total) * (w - label_width);
                    if (len < 5) {
                        len = 5;
                    }
                    return len;
                })
                .attr("height", options.row_height)
                .on("mouseover", function() {d3.select(this).transition().style("fill", "black")})
                .on("mouseout", function() {d3.select(this).transition().style("fill", "steelblue")});

        chart.selectAll("text")
            .data(options.data)
            .enter().append("text")
                .attr("x", 0)
                .attr("y", function (d, i) { return i * options.row_height + 15; })
                .text(function (d) { return d[0] + ": " + d[1]; });

        $("rect[class='" + options.selector + "']").tipsy({
            gravity: 'w',
            html: true,
            title: function() {
                var d = this.__data__;
                return (d[1] / options.total * 100).toFixed(0) + "%";
            }
          });
    };

    var ColumnChart = function (options) {
        var maxDomain = d3.max(options.data, function(val, i) {
                return val[1];
            }),
            dateParser = d3.time.format("%Y-%m-%d"),
            dateFormatter = d3.time.format("%B %e");

        var w = options.col_width,
            h = options.height,
            calculatedWidth = w * options.data.length - 1,
            chartWidth = (calculatedWidth < options.min_width) ? options.min_width : calculatedWidth;

        var x = d3.scale.linear()
            .domain([0, 1])
            .range([0, w]);

        var y = d3.scale.linear()
            .domain([0, maxDomain])
            .rangeRound([5, h - 17]);

        var chart = d3.select(options.selector).append("svg")
            .attr("class", "chart")
            .attr("width", chartWidth)
            .attr("height", h);

        chart.selectAll("rect")
            .data(options.data)
            .enter().append("rect")
                .attr("class", options.selector)
                .attr("x", function(d, i) { return x(i) - .5; })
                .attr("y", function(d) { return h - y(d[1]) - .5; })
                .attr("width", w)
                .attr("height", function(d) { return y(d[1]); })
                .on("mouseover", function() {d3.select(this).transition().style("fill", "black")})
                .on("mouseout", function() {d3.select(this).transition().style("fill", "steelblue")});

        chart.selectAll("text")
            .data(options.data)
            .enter().append("text")
                .attr("x", function(d, i) { return x(i) + 1; })
                .attr("y", function(d) { return h - y(d[1]) - 2; })
                .text(function (d) { return d[1]});


        chart.append("line")
            .attr("x1", 0)
            .attr("x2", chartWidth)
            .attr("y1", h - .5)
            .attr("y2", h - .5)
            .style("stroke", "#000");

        chart.selectAll("line")
            .data(y.ticks(5))
            .enter().append("line")
                .attr("y1", y)
                .attr("y2", y)
                .attr("x1", 0)
                .attr("x2", chartWidth)
                .style("stroke", "#333")
                .style("stroke-width", 0.1);

        $("rect[class='" + options.selector + "']").tipsy({
            gravity: 'w',
            html: true,
            title: function () {
                var d = this.__data__;
                return dateFormatter(new Date(d[0]));
            }
          });
    };

    return {
        "BarChart": BarChart,
        "ColumnChart": ColumnChart
    };
}());
