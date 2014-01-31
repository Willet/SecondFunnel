/*global $, _, App, sizeImage*/

// Gallery widget. loads inside a .gallery container.
// TODO: lazy load widgets
App.utils.registerWidget(
    'gallery',  // name (must be unique)
    '.gallery',  // selector (scoped!)
    function (view, $el, option) {
        var images, startX,
            threshold = $(this).width() / 5, // displacement needed to be considered a swipe
            changeImage = function ($el, url) {
                $el.attr('src', url);
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
                    'src': image.wide
                    // 'src': image.width(300)  // 300 = max logical width of the image
                })
                .click(function (ev) {
                    // show a larger image on the left when a thumbnail is clicked.
                    var $ev = $(ev.currentTarget),
                        newURL = $ev.attr('src'),
                        selector = $ev.parents('.previewContainer').find('.main-image').length ?
                          '.main-image' : '.image img',
                        $focusImg = $ev.parents('.previewContainer')
                            .find(selector);

                    $ev
                        .parents('.previewContainer')
                        .find('.gallery img')
                        .removeClass('selected');
                    $ev.addClass('selected');
                    changeImage($focusImg, newURL);
                });
            $el.append($img);  // add each image into the carousel
        });

        $.event.special.swipe.handleSwipe = $.noop; // JQuery's default swipes fire on fixed start/stop
        view.$('.gallery img').eq(0).click(); // ensure first image selected

        // swipeleft is "from right to left"
        view.$el
            .on('swipeleft swiperight', '.image', function (ev) {
                // select an image one to the left or right and select it
                var type = ev.type,  // swipeleft or swiperight
                    sel = view.$('.gallery .selected'),
                    selIdx = sel.index(),
                    images = $('.gallery img');

                if (type === 'swipeleft') {
                    selIdx++; // advance to next image in gallery
                    if (selIdx >= images.length) {
                        selIdx--;
                    }
                } else {  // can only be swiperight, based on available events
                    selIdx--; // retreat
                    if (selIdx < 0) {
                        selIdx++;
                    }
                }
                images.eq(selIdx).click();
            })
            .on('click', '.image', function (ev) {
                var $pseudo = $(ev.target);
                startX = ev.offsetX;
                if (ev.offsetX >= -15 && ev.offsetX <= 100) {   // left (which is swiping right)
                    $pseudo.swiperight();
                } else if (ev.offsetX >= $pseudo.width() - 100 &&  // right
                           ev.offsetY > 150) {  // prevent interference with close button
                    $pseudo.swipeleft();
                }
            });


        if (App.support.mobile()) { // enable continous swipe on mobile
            view.$el.on('touchmove', '.image', function (ev) {
                ev = ev.originalEvent;
                var newX = ev.touches[ev.touches.length - 1].clientX;
                startX = startX? startX : newX;
                var dist = newX - startX,
                    $pseudo = $(ev.target);
                if (Math.abs(dist) >= threshold) { // swipe only if passes certain threshold
                    startX = newX;
                    if (dist < 0) {
                        $pseudo.swipeleft();
                    } else {
                        $pseudo.swiperight();
                    }
                }
            });
        }
    }
);
