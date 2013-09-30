/**
 * touchscroll.js (Willet edition)
 * This function makes a div scrollable with android and iphone
 */
$.fn.touchScroll = function () {
    "use strict";
    var isTouchDevice, touchScroll;

    isTouchDevice = function () {
        /* Added Android 3.0 honeycomb detection because touchscroll.js breaks
         the built in div scrolling of android 3.0 mobile safari browser */
        if ((navigator.userAgent.match(/android 3/i)) ||
            (navigator.userAgent.match(/honeycomb/i))) {
            return false;
        }
        try {
            document.createEvent("TouchEvent");
            return true;
        } catch (e) {
            return false;
        }
    };

    touchScroll = function (el) {
        if (isTouchDevice()) {  // if touch events exist...
            var scrollStartPosY = 0, scrollStartPosX = 0;

            el.addEventListener("touchstart",
                function (ev) {
                    scrollStartPosY = this.scrollTop + ev.touches[0].pageY;
                    scrollStartPosX = this.scrollLeft + ev.touches[0].pageX;
                    //event.preventDefault(); // Keep this remarked so you can click on buttons and links in the div
                }, false);

            el.addEventListener("touchmove",
                function (ev) {
                    if ((this.scrollTop < this.scrollHeight - this.offsetHeight &&
                        this.scrollTop + ev.touches[0].pageY < scrollStartPosY - 5) ||
                        (this.scrollTop != 0 && this.scrollTop + ev.touches[0].pageY > scrollStartPosY + 5)) {
                        ev.preventDefault();
                    }
                    if ((this.scrollLeft < this.scrollWidth - this.offsetWidth &&
                        this.scrollLeft + ev.touches[0].pageX < scrollStartPosX - 5) ||
                        (this.scrollLeft != 0 && this.scrollLeft + ev.touches[0].pageX > scrollStartPosX + 5)) {
                        ev.preventDefault();
                    }
                    this.scrollTop = scrollStartPosY - ev.touches[0].pageY;
                    this.scrollLeft = scrollStartPosX - ev.touches[0].pageX;
                }, false);
        }
    };

    return this.each(function() {
        touchScroll(this);
    });
};