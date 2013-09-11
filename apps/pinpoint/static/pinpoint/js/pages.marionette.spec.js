/*global describe, jasmine, it, beforeEach, expect */
describe("SecondFunnel", function () {
    var app;

    beforeEach(function () {
        app = SecondFunnel;
        app.start(app.options);
    });

    afterEach(function () {

    });

    it("must exist", function () {
        expect(app).not.toEqual(undefined);
    });

    describe("General", function () {
        /*

        Not machine-testable

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
        /*

        Not machine-testable

        Landing pages must display in one of two display modes depending on the device’s effective resolution:
         If the effective resolution is X, the landing page must use the mobile display mode
         If the effective resolution is Y, the landing page must use the desktop display mode
        A landing page must maintain its display mode even if the device orientation changes.
         If a device is mobile or vice versa, it must always render in that mode, regardless if the initial orientation of the page.
        Landing pages must present some visual indication that a tile can be activated
         For non-mouse enabled devices, this indicator should be an element overlayed on the tile
         For mouse enabled devices, this indicator should be a mouse pointer
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