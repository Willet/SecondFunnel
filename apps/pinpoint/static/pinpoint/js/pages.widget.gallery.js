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
App.utils.registerWidget('gallery', '.gallery', function (view, $el, options) {
    var images, focusWidth, arrows,
        wndWidth = $(window).width(),
        focusCurrent = 0,
        speed = 250, // transition speed for mobile
        $gallery = view.$('.gallery'), // reference to gallery
        self = this, // self is widget gallery
        focus = view.$(view.$('.main-image').length ? '.main-image' : '.image img'),
        defaults = {
            leftArrow: '.gallery-swipe-left',
            rightArrow: '.gallery-swipe-right',
            disabledClass: 'grey',
            selectedClass: 'selected'
        };

    // Check for children as may have already appended
    if ($el && $el.children().length > 0) {
        return;
    }

    /**
     * Manually updates the position of images in the gallery.
     *
     * @param distance    Distance to scroll horizontally
     * @param duration    Time it takes for the transition
     * @return this
     */
    this.scrollImages = function (distance, duration) {
        duration = duration ? duration : speed;
        distance = distance * -1;
        focus.css('-webkit-transition-duration', (duration / 1000).toFixed(1) + 's')
             .css('-webkit-transform', "translate3d(" + distance + "px, 0px, 0px)");

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
    this.swipeStatus = function (event, phase, direction, distance, fingers) {
        var offset;
        focusWidth = focus.children().eq(0).width();
        offset = focusWidth * focusCurrent;

        /* Determine the event from the phase and the direction
           of the touch event that took place */
        if (phase === "move") {
            // div is being dragged, determine direction
            if (direction === "left") {
                this.scrollImages(distance + offset);
            } else if (direction === "right") {
                this.scrollImages(offset - distance);
            }
        } else if (phase === "end") {
            // animate to the next image based on direction
            if (direction === "right") {
                focusCurrent = Math.max(focusCurrent - 1, 0);
            } else if (direction === "left") {
                focusCurrent = Math.min(focusCurrent + 1, focus.children().length - 1);
            }
            this.scrollImages(focusCurrent * focusWidth);
            this.selectImage(); // mark selected
        } else if (phase === "cancel") {
            // animate back as dragging has been cancelled
            this.scrollImages(focusWidth * focusCurrent);
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
        var hash,
            arrows,
            len = focus.children().length - 1;

        // Determine the selected image
        $gallery
            .children()
            .removeClass(options.selectedClass)
            .eq(focusCurrent)
            .addClass(options.selectedClass);

        // Undisable by default
        arrows = $()
            .add(options.leftArrow)
            .add(options.rightArrow)
            .removeClass(options.disabledClass)
            .eq(focusCurrent / len);

        if (!! arrows[0]) {
            arrows.addClass(options.disabledClass);
        }

        if (!!window.location.hash) { // set hash if nonexistant
            hash = window.location.hash + '&photo=' + focusCurrent;
            App.vent.trigger('tracking:trackPageView', hash);
        }

        return this;
    };

    /**
     * Initializes the regular version of the gallery.
     */
    this.initialize = function () {
        // Desktop is nice, doesn't need anything
        options = _.extend(defaults, options);
        this.selectImage();

        console.debug("initialized desktop gallery.");
    };

    /**
     * Initializes the mobile version of the gallery.  Attach
     * the swipe handler.
     */
    this.initializeMobile = function () {
        var width = $(window).width();

        // Need fixed width for swipe to work
        focus.children().css('width', width);
        width = width * focus.children().length;
        focus.width(width);

        // Assign options and select arrows; attach swipe
        // handlers
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
            allowPageScroll: "vertical"
        });

        this.selectImage();
        console.debug("initialized mobile gallery.");
    };

    /* Find the images to use in the gallery. */
    images = view.model.get('related-products');
    if (images && images.length) { // ensure related images exist
        images = images[0].images.slice(0);

        if (App.support.mobile()) {
            images.splice(0, 0, view.model.get('defaultImage'));
        }
    } else {
        images = view.model.get('images');
    }

    _.each(images, function(image) { // iterate over images to create gallery
        var $img;
        $img = App.support.mobile() ?
            $('<div></div>').css('background-image', 'url(' + image.width(wndWidth * 1.5) + ')') :
            $('<img />').attr('src', image.width());

        $img
            .addClass('img')
            .click(function (ev) {
                if (App.support.mobile()) return; // mobile does nothing
                var hash,
                    $selected = $(ev.currentTarget),
                    newURL = $selected.attr('src');

                focus.attr('src', newURL); // change image
                $gallery.animate({ // animate gallery on click
                    scrollLeft: $selected.offset().left - $gallery.offset().left
                }, 700);
                focusCurrent = $selected.index();
                self.selectImage();
            });

        if (App.support.mobile()) { // append to display area and create tile for gallery
            focus.append($img);
            $el.append($('<div />').addClass('img'));
        } else { // otherwise append to gallery
            $el.append($img);
        }
    });

    /* Initialize the gallery and bind event handlers to the widget
       gallery instance. */
    _.bindAll(this, 'swipeStatus', 'scrollImages');
    if (App.support.mobile()) this.initializeMobile();
    else this.initialize();
});
