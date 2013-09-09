/*global describe, jasmine, it, beforeEach, expect */
describe("Viewport", function () {
    var app,
        meta = (function () {
            var tag = $('meta[name="viewport"]', 'head');

            if (!tag.length && window.devicePixelRatio) {
                // if no viewport is found of it, it will be made.
                // (assuming the device supports it)
                tag = $('<meta />', {
                    'name': 'viewport',
                    'content': ''
                });
                $('head').append(tag);
            }
            return tag;
        }()),
        originalContent = meta.attr('content');

    beforeEach(function () {
        app = SecondFunnel;
        app.options.mobile = false;
        meta.attr('content', '');
    });

    describe('scale', function () {
        it("should be disabled on desktops", function () {
            app.viewport.scale();
            expect(meta.attr('content')).toEqual(originalContent);
        });

        it("should be enabled on tablets", function () {
            // fake a mobile device
            app.options.mobile = true;
            window.devicePixelRatio = 1.5;
            app.viewport.scale();
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should be enabled on mobiles", function () {
            // fake a mobile device
            app.options.mobile = true;
            window.devicePixelRatio = 2;
            app.viewport.scale();
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should be enabled on HTC Butterfly", function () {
            // fake a mobile device
            app.options.mobile = true;
            window.devicePixelRatio = 3;
            app.viewport.scale();
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should handle incorrect width values", function () {
            // fake a mobile device
            app.options.mobile = true;
            window.devicePixelRatio = 2;
            app.viewport.scale(-1);
            expect(meta.attr('content')).toEqual(originalContent);
        });
    });
});