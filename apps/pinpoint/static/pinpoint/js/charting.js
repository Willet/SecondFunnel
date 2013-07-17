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

        var maxLength = d3.max(options.data, function (val, i) {
            var label = val[0] + ": " + val[1];
            return label.length;
        });

        var width = options.width,
            height = options.rowHeight * options.data.length,
            label_width = maxLength * 7;

        var x = d3.scale.linear()
            .domain([0, 100]);

        var chart = d3.select(options.selector).append("svg")
            .attr("class", "chart")
            .attr("width", width)
            .attr("height", height);

        chart.selectAll("rect")
            .data(options.data)
            .enter().append("rect")
            .attr("class", options.selector)
            .attr("x", label_width)
            .attr("y", function (d, i) {
                return i * options.rowHeight;
            })
            .attr("width", function (d) {
                var len = (d[1] / options.total) * (width - label_width);
                if (len < 5) {
                    len = 5;
                }
                return len;
            })
            .attr("height", options.rowHeight)
            .on("mouseover", function () {
                d3.select(this).transition().style("fill", "black")
            })
            .on("mouseout", function () {
                d3.select(this).transition().style("fill", "steelblue")
            });

        chart.selectAll("text")
            .data(options.data)
            .enter().append("text")
            .attr("x", 0)
            .attr("y", function (d, i) {
                return i * options.rowHeight + 15;
            })
            .text(function (d) {
                return d[0] + ": " + d[1];
            });

        $("rect[class='" + options.selector + "']").tipsy({
            gravity: 'w',
            html: true,
            title: function () {
                var d = this.__data__;
                return (d[1] / options.total * 100).toFixed(0) + "%";
            }
        });
    };

    var ColumnChart = function (options) {
        var maxDomain = d3.max(options.data, function (val, i) {
                return val[1];
            }),
            dateFormatter = d3.time.format("%B %e"),
            width = options.colWidth,
            height = options.height,
            calculatedWidth = width * options.data.length - 1,
            chartWidth = (calculatedWidth < options.minWidth) ? options.minWidth : calculatedWidth,
            x = d3.scale.linear()
                .domain([0, 1])
                .range([0, width]),
            y = d3.scale.linear()
                .domain([0, maxDomain])
                .rangeRound([5, height - 17]),
            chart = d3.select(options.selector).append("svg")
                .attr("class", "chart")
                .attr("width", chartWidth)
                .attr("height", height);

        chart.selectAll("rect")
            .data(options.data)
            .enter().append("rect")
            .attr("class", options.selector)
            .attr("x", function (d, i) {
                return x(i) - 0.5;
            })
            .attr("y", function (d) {
                return height - y(d[1]) - 0.5;
            })
            .attr("width", width)
            .attr("height", function (d) {
                return y(d[1]);
            })
            .on("mouseover", function () {
                d3.select(this).transition().style("fill", "black")
            })
            .on("mouseout", function () {
                d3.select(this).transition().style("fill", "steelblue")
            });

        chart.selectAll("text")
            .data(options.data)
            .enter().append("text")
            .attr("x", function (d, i) {
                return x(i) + 1;
            })
            .attr("y", function (d) {
                return height - y(d[1]) - 2;
            })
            .text(function (d) {
                return d[1];
            });


        chart.append("line")
            .attr("x1", 0)
            .attr("x2", chartWidth)
            .attr("y1", height - 0.5)
            .attr("y2", height - 0.5)
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
            'gravity': 'w',
            'html': true,
            'title': function () {
                var d = this.__data__;  // TODO: wat
                return dateFormatter(new Date(d[0]));
            }
        });
    };

    return {
        "BarChart": BarChart,
        "ColumnChart": ColumnChart
    };
}());