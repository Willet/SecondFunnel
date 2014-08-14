/*global $, _, App, sizeImage, setTimeout, clearTimeout*/
/**
 * Defines the gallery widget.  The gallery widget displays several products in
 * a carousel that is swipe-able on mobile and click-able on non-mobile devices.
 * Using the gallery widget:
 *     $el is always the gallery element, where the selectors/small images will
 *     appear.  The area in which the larger image is displayed (the selected one) must
 *     have either a '.image' or '.main-image' class.
 *
 * @param view {Object}    The Marionette view object
 * @param $el {Object}     The object to attach the gallery to
 * @param options {Object}  Specific options
 * @return this
 */
App.utils.registerWidget('gallery', '.gallery, .gallery-dots', function (view, $el, options) {
    var images,
        focusWidth,
        arrows,
        windowWidth = $(window).width(),
        focusCurrent = 0,
        speed = 250, // transition speed for mobile
        $gallery = view.$('.gallery, .gallery-dots'), // reference to gallery
        self = this, // self is widget gallery
        focus = view.$(view.$('.main-image').length ? '.main-image' : '.image img'),
        defaults = {
            leftArrow: '.gallery-swipe-left',
            rightArrow: '.gallery-swipe-right',
            disabledClass: 'grey',
            selectedClass: 'selected'
        };

    /**
     * Updates the focusCurrent
     *
     * @param newCurrent  The new focusCurrent
     * @return this
     */
    this.updateFocusCurrent = function (newCurrent) {
        focusCurrent = newCurrent;

        if (self.$el.parents('#hero-area').length) {
            App.options.heroGalleryIndexPage = focusCurrent;
        } else {
            App.options.galleryIndexPage = focusCurrent;
        }

        return this;
    };

    /**
     * Manually updates the position of images in the gallery.
     *
     * @param distance    Distance to scroll horizontally
     * @param duration    Time it takes for the transition
     * @return this
     */
    this.scrollImages = function (distance, duration) {
        if (duration === undefined) {
            duration = speed;
        }

        distance = distance * -1;

        if (App.support.isLessThanIe9()) {
            focus.css({
                'position': 'relative',
                'left': distance + 'px'
            });
        } else {
            focus.css({
                '-webkit-transition-duration': (duration / 1000).toFixed(1) + 's',
                'transition-duration': (duration / 1000).toFixed(1) + 's',
                '-webkit-transform': 'translate3d(' + distance + 'px, 0px, 0px)',
                '-ms-transform': 'translateX(' + distance + 'px)',
                'transform': 'translate3d(' + distance + 'px, 0px, 0px)'
            });
        }

        return this;
    };

    /**
     * Catches the phase of the swipe and performs the appropriate action;
     * switching to the next image, transitioning between images and snapping
     * back.
     *
     * @param event {Object}      The touch event
     * @param phase {String}      The event name
     * @param direction {String}  The direction if it is a move/end event
     * @param distance {Float}    The distance if it is a move event
     * @param fingers {Object}    Finger events such as pinch, tap
     * @return this
     */
    this.swipeStatus = function (event, phase, direction, distance, fingers, duration) {
        var offset;
        focusWidth = focus.children().eq(0).outerWidth();
        offset = focusWidth * focusCurrent;

        /* Determine the event from the phase and the direction
           of the touch event that took place */
        if (phase === 'move') {
            // div is being dragged, determine direction
            if (direction === 'left') {
                this.scrollImages(distance + offset, duration);
            } else if (direction === 'right') {
                this.scrollImages(offset - distance, duration);
            }
        } else if (phase === 'end') {
            // animate to the next image based on direction
            if (direction === 'right') {
                this.updateFocusCurrent(Math.max(focusCurrent - 1, 0));
            } else if (direction === 'left') {
                this.updateFocusCurrent(Math.min(focusCurrent + 1, focus.children().length - 1));
            }
            this.scrollImages(focusCurrent * focusWidth, duration);
            this.selectImage(); // mark selected
        } else if (phase === 'cancel') {
            // animate back as dragging has been cancelled
            this.scrollImages(focusWidth * focusCurrent, duration);
        }
        return this;
    };

    /**
     * Switches the selected gallery image and updates any relevant arrows
     * in addition to tracking the switch.
     *
     * @return this
     */
    this.selectImage = function () {
        var hash, arrows,
            len = focus.children().length - 1;

        // Determine the selected image
        $('.item', $gallery)
            .removeClass(options.selectedClass)
            .eq(focusCurrent)
            .addClass(options.selectedClass);

        // Un-disable by default
        arrows = $()
            .add(options.leftArrow)
            .add(options.rightArrow)
            .removeClass(options.disabledClass)
            .eq(focusCurrent / len);

        if (!! arrows[0]) {
            arrows.addClass(options.disabledClass);
        }

        return this;
    };


    /**
     * Updates the gallery to select the image in the
     * specified index.
     *
     * @param index       The index of the image
     * @param duration    The duration of the transition
     * @return this
     */
    this.selectByIndex = function (index, duration) {
        this.updateFocusCurrent(index);
        this.selectImage();
        this.swipeStatus(null, "cancel", null, null, null, duration);

        return this;
    };

    /**
     * Initializes the gallery. Attach the swipe handler.
     */
    this.initialize = function () {
        // Assign options and select arrows; attach swipe
        // handlers
        var self = this;
        options = _.extend(defaults, options);
        options.leftArrow = view
            .$(options.leftArrow)
            .click(function(ev) { // tap left is swipe right
                self.swipeStatus(null, 'end', 'right');
            });

        options.rightArrow = view
            .$(options.rightArrow)
            .click(function(ev) { // tap right is swipe left
                self.swipeStatus(null, 'end', 'left');
            });

        focus.swipe({ // attach swipe handler
            triggerOnTouchEnd: true,
            swipeStatus: _.bind(self.swipeStatus, self),
            allowPageScroll: 'vertical'
        });

        $('.item', $gallery).on('click', function () {
            self.selectByIndex($(this).index());
        });

        this.selectImage();

        if (this.$el.parents('#hero-area').length) {
            this.selectByIndex(App.option('heroGalleryIndexPage', 0), 0);
        } else {
            this.selectByIndex(App.option('galleryIndexPage', 0), 0);
        }

        console.debug('initialized gallery.');
    };

    /* Initialize the gallery and bind event handlers to the widget
       gallery instance. */
    _.bindAll(this, 'swipeStatus', 'scrollImages');
    this.initialize();
});
