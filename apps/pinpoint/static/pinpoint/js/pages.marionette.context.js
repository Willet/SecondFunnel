(function (app, Geppetto, undefined) {
    "use strict";

    var command = function () { };

    command.prototype.execute = function () {
        _.bindAll(this);
        var that = this;

        var apikey = "78ejsdd76tc6jsffmrxjddxu";
        var baseUrl = "http://api.rottentomatoes.com/api/public/v1.0";
        var moviesSearchUrl = baseUrl + '/movies.json?apikey=' + apikey;
        //get the movie title
        var query = this.eventData.data.get("title");
        var pageLimit = "&page_limit=1";

        //make an plain jquery ajax call to fetch the movie details using the
        //rotten tomatoes public api's

        $.ajax({
            url: moviesSearchUrl + '&q=' + encodeURI(query) + pageLimit,
            dataType: "jsonp",
            success: function (data) {
                that.handleDataLoadSuccess(data);
            },
            statusCode: {
                503: function () {
                    that.handleDataLoadError("page not found");
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                that.handleDataLoadError(errorThrown);
            }
        });

    };

    command.prototype.handleDataLoadSuccess = function (data) {
        var movies = data.movies;

        if (!data || !data.movies || data.movies.length <= 0) {
            //when there are no movies dispatch an error event
            this.context.dispatch("loadResultsErrorEvent"/*event name*/);
        } else {
            //when we get the movies results
            //construct an object with movie details
            var resultObj = {};
            resultObj.rated = movies[0].mpaa_rating;
            resultObj.title = movies[0].title;
            resultObj.rating = movies[0].ratings.audience_score;
            resultObj.year = movies[0].year;
            resultObj.poster = movies[0].posters.original;
            //dispatch an event on the context with movie details as payload
            this.context.dispatch("loadResultsSuccessEvent"/*event name*/,
                resultObj);
        }

    };

    command.prototype.handleDataLoadError = function (e) {
        //when there are no movies dispatch an error event
        this.context.dispatch("loadResultsErrorEvent"/*event name*/);
    };

    app.command = command;
}(SecondFunnel, Backbone.Geppetto));