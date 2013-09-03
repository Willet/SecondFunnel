// Example: adding custom behaviour to supported layouts
// TODO: lazy load widgets
SecondFunnel.utils.addWidget(
    'gallery',  // name (must be unique)
    '.gallery',  // selector (scoped!)
    function (view, $el, option) {
        var images,
            changeImage = function ($el, url) {
                $el.attr('src', sizeImage(url, 300));
            };

        // get list of images.
        try {
            images = view.model.attributes['related-products'][0].images;
        } catch (err) {
            images = view.model.get('images');
        }

        _.each(images, function (image) {
            var $img = $('<img />')
                .attr({
                    'src': sizeImage(image, 100)
                })
                .click(function (ev) {
                    // show a larger image on the left when a thumbnail is clicked.
                    var $ev = $(ev.currentTarget),
                        newURL = $ev.attr('src'),
                        $focusImg = $ev.parents('.previewContainer')
                            .find('.image img');

                    $ev
                        .parents('.previewContainer')
                        .find('.gallery img')
                        .removeClass('selected');
                    $ev.addClass('selected');
                    changeImage($focusImg, newURL);
                });
            $el.append($img);  // add each image into the carousel
        });

        // swipeleft is "from right to left"
        view.$el.on('swipeleft swiperight', '.image, .image img',
            function (ev) {
                // select an image one to the left or right and select it
                var type = ev.type,  // swipeleft or swiperight
                    sel = view.$('.gallery .selected'),
                    selIdx = sel.index(),
                    images = $('.gallery img');
                images.removeClass('selected');

                if (type === 'swipeleft') {
                    selIdx++;  // advance
                    if (selIdx >= images.length) {
                        selIdx = images.length - 1;
                    }
                } else {
                    selIdx--;  // not retreat
                    if (selIdx < 0) {
                        selIdx = 0;
                    }
                }
                images.eq(selIdx).addClass('selected').click();
            });
    }
);