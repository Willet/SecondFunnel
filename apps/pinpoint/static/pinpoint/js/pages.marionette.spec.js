/*global describe, jasmine, it, beforeEach, afterEach, expect */
describe("SecondFunnel", function () {
    var app = SecondFunnel;

    beforeEach(function () {
        app = SecondFunnel;
    });

    afterEach(function () {

    });

    describe("General", function () {
        /*

        TODO

        Landing pages must support mobile devices. The following devices must work:
         iPhone (retina)
         iPhone (non-retina)
         iPad (retina)
         iPad (non-retina)
        Landing pages must support modern browsers. The following browsers must work:
         Chrome (Desktop, Android 4.x+)
         Firefox
         Internet Explorer 8+
         Safari (iOS 4+)
         Android browser (Android 2.x+)
        Theming should be limited to just HTML and CSS
        */
    });

    describe("Usability", function () {

        describe("Landing pages must display in one of two display modes depending on " +
            "the device’s effective resolution: If the effective resolution " +
            "is X, the landing page must use the mobile display mode", function () {
            var myWidth = $(window).width(),
                myPixelRatio = window.devicePixelRatio || 1,
                viewportData;

            beforeEach(function () {
                // default
                viewportData = app.viewport.determine();
                app.options.lockWidth = true;  // force enable
            });

            afterEach(function () {
                app.options.lockWidth = $.browser.mobile;  // restore default
            });

            it("should be disabled when window pixel ratio is not high " +
                "enough to be a portable device", function () {
                if (myPixelRatio < 1.5) {
                    expect(viewportData[0]).toEqual(false);
                } // else: not necessarily true
            });

            it("should be disabled when window width is too wide " +
                "to be a portable device", function () {
                if (myWidth >= 768) {
                    expect(viewportData[0]).toEqual(false);
                } // else: not necessarily true
            });

            it("should be enabled if believed " +
                "to be a portable device", function () {
                if ($.browser.mobile && myPixelRatio >= 1.5 && myWidth < 768) {
                    expect(viewportData[0]).toEqual(true);
                }
            });
        });

        describe("Landing pages must display in one of two display modes depending on " +
            "the device’s effective resolution: If the effective resolution " +
            "is Y, the landing page must use the desktop display mode", function () {

            it("must be in desktop mode if window width is too wide, " +
                "pixel density too low, or " +
                "forcibly disabled", function () {
                var myWidth = $(window).width(),
                    myPixelDensity = window.devicePixelDensity || 1,
                    viewportData = app.viewport.determine();

                if (myWidth >= 768) {
                    expect(viewportData[0]).toEqual(false);
                }

                if (myPixelDensity >= 1) {
                    expect(viewportData[0]).toEqual(false);
                }
            });
        });

        it("A landing page must maintain its display mode even if the device " +
            "orientation changes", function () {
            var isInMobileMode = ($(window).width() < 768);

            if (isInMobileMode) {
                // if in mobile mode, expect to stay in mobile mode
                SecondFunnel.vent.trigger("rotate");
                expect($(window).width()).toBeLessThan(768);
            }
        });

        it("If a device is mobile or vice versa, it must always render in that " +
            "mode, regardless if the initial orientation of the page.", function () {
            var isDeviceMobile = $.browser.mobile;

            if (isDeviceMobile) {
                // if in mobile mode, expect width to be locked below 768px
                // by the viewport agent.
                expect($(window).width()).toBeLessThan(768);
                SecondFunnel.vent.trigger("rotate");
                expect($(window).width()).toBeLessThan(768);
            }
        });

        describe("Landing pages must present some visual indication that a tile " +
            "can be activated:", function () {
            it("For non-mouse enabled devices, this indicator " +
                "should be an element overlayed on the tile.", function () {
                if (app.support.touch()) {
                    var tile = new SecondFunnel.classRegistry.Tile({});
                    tile.createView();  // trigger tap indicator
                    expect($('html').hasClass('touch-enabled')).toEqual(true);
                }
            });

            it("For mouse enabled devices, this indicator should be a " +
                "mouse pointer", function () {
                if (!app.support.touch() && window.getComputedStyle) {
                    var tile = new SecondFunnel.classRegistry.Tile(window.PAGES_INFO.featured),
                        view = tile.createView();  // trigger tile creation
                    if (view) {  // 'no template' is a reason why this check is needed
                        expect($('html').hasClass('touch-enabled')).toEqual(false);
                    }
                }
            });
        });

        /*

        TODO

        The number of columns should scale dependent on the effective resolution of the viewport
         The number of columns should not exceed 4 (added 08-23)
        A tile should be rendered as soon as possible
         If an image is loading, the user should see some indication that some action is taking place
         If an image is loading, a placeholder image should be displayed with the dominant colour as the background colour
        A tile must not be rendered if:
         The tile contains images that are broken
         The tile does not meet ‘acceptable tile’ criteria
         */
    });

    describe("Performance", function () {

    });

    describe("Flexibility", function () {

    });

    describe("Behaviour / Error Handling", function () {

    });

    describe("Tracking", function () {

    });

    describe("Theme Design / Templating", function () {

    });
});