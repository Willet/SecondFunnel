beforeEach(function() {
    /**
     * include teardown code here
     * @param app
     */
    this.resetApp = function (app) {
        _.each(app.submodules, function(module) {
            module.stop();
        });
        Backbone.History.stop();
        app._initCallbacks.reset();
    };

    this.response = function(responseText, options) {
        var response;

        options = options || {};
        options.status = options.status || 200;
        options.headers = options.headers || {
           "Content-Type": "application/json"
        };
        options.callback = options.callback || 'fn';
        options.jsonp = options.jsonp || false;

        if (options.jsonp) {
           response = options.callback + '(' + JSON.stringify(responseText) + ')';
        } else {
           response = JSON.stringify(responseText);
        }

        return [
           options.status,
           options.headers,
           response
        ];
    };

    this.generateTile = function(options) {
        // TODO: generate random tiles
        options = options || {};

        return {
            "default-image": "156",
            "url": "http://www.gap.com/products/P631642.jsp",
            "price": "$59.95",
            "description": "Lightweight, fluid weave. Long sleeves with single-button cuffs. Collar with a clean finish. Henley button placket. Patch pockets on chest with button-flap closures. Rear shoulder yoke with single pleat.\nStraight silhouette with drapey, easy fit. Curved shirttail hits at mid-thigh.",
            "name": "Camp dress",
            "images": [{
                "format": "jpg",
                "type": "image",
                "dominant-colour": "#303d2c",
                "url": "http://images.secondfunnel.com/store/gap/product/48/image/37331fac5b60c7c665783d1328a766ce/master.jpg",
                "id": "156",
                "sizes": {
                    "grande": {
                        "width": 450,
                        "height": 600
                    },
                    "icon": {
                        "width": 24,
                        "height": 32
                    },
                    "compact": {
                        "width": 120,
                        "height": 160
                    },
                    "1024x1024": {
                        "width": 768,
                        "height": 1024
                    },
                    "small": {
                        "width": 75,
                        "height": 100
                    },
                    "thumb": {
                        "width": 37,
                        "height": 50
                    },
                    "large": {
                        "width": 360,
                        "height": 480
                    },
                    "medium": {
                        "width": 180,
                        "height": 240
                    },
                    "pico": {
                        "width": 12,
                        "height": 16
                    }
                }
            }, {
                "format": "jpg",
                "type": "image",
                "dominant-colour": "#4f274e",
                "url": "http://images.secondfunnel.com/store/gap/product/48/image/bb9954242a85eebb6be5a7ae9e6324c8/master.jpg",
                "id": "157",
                "sizes": {
                    "grande": {
                        "width": 450,
                        "height": 600
                    },
                    "icon": {
                        "width": 24,
                        "height": 32
                    },
                    "compact": {
                        "width": 120,
                        "height": 160
                    },
                    "1024x1024": {
                        "width": 768,
                        "height": 1024
                    },
                    "small": {
                        "width": 75,
                        "height": 100
                    },
                    "thumb": {
                        "width": 37,
                        "height": 50
                    },
                    "large": {
                        "width": 360,
                        "height": 480
                    },
                    "medium": {
                        "width": 180,
                        "height": 240
                    },
                    "pico": {
                        "width": 12,
                        "height": 16
                    }
                }
            }],
            "tile-id": 53,
            "template": options.type || 'product'
        };
    };
});

afterEach(function() {
    //Clear the template cache!
    Backbone.Marionette.TemplateCache.clear();
});