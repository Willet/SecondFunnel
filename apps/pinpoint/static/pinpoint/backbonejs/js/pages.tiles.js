(function (Willet, pages, undefined) {
    "use strict";

    // youtube model
    pages.addTileClass('YoutubeTileModel', pages.classes.TileModel.extend({
        // static props e.g. YoutubeTile.something
    }, {
        // object props e.g. aTile.something()
        'thumbnail': function () {
            return 'http://i.ytimg.com/vi/' + this['original-id'] +
                   '/hqdefault.jpg';
        },
        'propBag': function () {
            // add more properties to this tile for rendering.
            return {'thumbnail': this.thumbnail()};
        }
    }));

    // youtube view
    pages.addTileClass('YoutubeTileView', pages.classes.TileView.extend({
        // static props e.g. YoutubeTile.something
    }, {
        // object props e.g. aTile.something()
        'click': function ($el) {
            // $el.remove();  // testing
            console.log(this);
            this.play();
        },
        'play': function () {
            return 1;
        },
        'wide': function () {
            return true;
        }
    }));
}(window.Willet, window.Willet.pages));