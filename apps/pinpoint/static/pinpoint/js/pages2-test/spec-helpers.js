beforeEach(function() {
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

        return {
            "description": "",
            "tags": {},
            "url": "http://shop.nativeshoes.com/jimmy-jiffy-black.html",
            "price": "$90.00",
            "title": "Jimmy - Jiffy Black",
            "lifestyle-image": "http://images.secondfunnel.com/store/generic/generic/d7278173d66e6b3dce27c6c1f5f0798d/master.jpg",
            "id": "5383",
            "template": "combobox",
            "images": [
                "http://images.secondfunnel.com/store/nativeshoes/product/5383/image/c64b054e88cc4a7a2d2f0a27c8e57cdf/master.jpg",
                "http://images.secondfunnel.com/store/nativeshoes/product/5383/image/f772f1fc737b684106ef8036da67cccf/master.jpg",
                "http://images.secondfunnel.com/store/nativeshoes/product/5383/image/44cb14a6ee4eaf9f9e7c53fdc2e5c22b/master.jpg"
            ],
            "image": "http://images.secondfunnel.com/store/nativeshoes/product/5383/image/c64b054e88cc4a7a2d2f0a27c8e57cdf/master.jpg",
            "content-id": 5383,
            "name": "Jimmy - Jiffy Black"
        }
    };
});