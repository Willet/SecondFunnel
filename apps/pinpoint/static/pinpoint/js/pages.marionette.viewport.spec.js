/*global describe, jasmine, it, beforeEach, expect */
describe("viewport", function () {
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
        resetMeta = function () {
            meta.attr('content', '');
        },
        originalContent = meta.attr('content');

    beforeEach(function () {
        app = SecondFunnel;
        app.options.mobile = false;
        $.browser.mobile = false;
        resetMeta();
    });

    describe('scale', function () {
        it("should be disabled on desktops", function () {
            app.viewport.scale();
            expect(meta.attr('content')).toEqual(originalContent);
        });

        it("should be enabled on tablets", function () {
            // fake a mobile device
            app.options.mobile = true;
            $.browser.mobile = true;
            window.devicePixelRatio = 1.5;
            app.viewport.scale();
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should be enabled on mobiles", function () {
            // fake a mobile device
            app.options.mobile = true;
            $.browser.mobile = true;
            window.devicePixelRatio = 2;
            app.viewport.scale();
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should be enabled on HTC Butterfly", function () {
            // fake a mobile device
            app.options.mobile = true;
            $.browser.mobile = true;
            window.devicePixelRatio = 3;
            app.viewport.scale();
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should handle functions", function () {
            // fake a mobile device
            app.options.mobile = true;
            $.browser.mobile = true;
            window.devicePixelRatio = 2;

            app.viewport.scale(function () {
                return 1024;
            });
            expect(meta.attr('content')).not.toEqual(originalContent);
        });

        it("should scale correctly after successive resizes", function () {
            // fake a mobile device
            app.options.mobile = true;
            $.browser.mobile = true;
            window.devicePixelRatio = 2;

            var ratio = ($(window).width() / 1024).toFixed(2);
            app.viewport.scale(1024);
            expect(meta.attr('content')).toEqual('user-scalable=no,width=1024,initial-scale=' +
                ratio + ',minimum-scale=' + ratio + ',maximum-scale=' + ratio);

            ratio = ($(window).width() / 768).toFixed(2);
            app.viewport.scale(768);
            expect(meta.attr('content')).toEqual('user-scalable=no,width=768,initial-scale=' +
                ratio + ',minimum-scale=' + ratio + ',maximum-scale=' + ratio);

            ratio = ($(window).width() / 2048).toFixed(2);
            app.viewport.scale(2048);
            expect(meta.attr('content')).toEqual('user-scalable=no,width=2048,initial-scale=' +
                ratio + ',minimum-scale=' + ratio + ',maximum-scale=' + ratio);
        });

        it("should handle incorrect width values", function () {
            // fake a mobile device
            app.options.mobile = true;
            $.browser.mobile = true;
            window.devicePixelRatio = 2;
            app.viewport.scale('poop master');
            expect(meta.attr('content')).toEqual(originalContent);

            resetMeta();
            app.viewport.scale(-1);
            expect(meta.attr('content')).toEqual(originalContent);

            resetMeta();
            app.viewport.scale(0);
            expect(meta.attr('content')).not.toEqual(originalContent);

            resetMeta();
            app.viewport.scale(1);
            expect(meta.attr('content')).not.toEqual(originalContent);

            resetMeta();
            app.viewport.scale(1500);
            expect(meta.attr('content')).not.toEqual(originalContent);

            resetMeta();
            app.viewport.scale(2048);
            expect(meta.attr('content')).not.toEqual(originalContent);

            resetMeta();
            app.viewport.scale(2049);
            expect(meta.attr('content')).toEqual(originalContent);
        });
    });
});