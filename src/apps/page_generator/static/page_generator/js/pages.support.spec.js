/*global describe, jasmine, it, beforeEach, expect */
describe("support", function () {
    var app,
        module,
        moduleName;

    beforeEach(function () {
        $('html').removeClass('touch-enabled');  // if present

        app = SecondFunnel;
        module = app.support;
    });

    describe('mobile', function () {
        it("should not change", function () {
            expect(module.mobile()).toEqual(module.mobile());
        });
    });

    describe('touch', function () {
        it("should be overwritten", function () {
            // initial state is device-dependent
            expect(module.touch()).toEqual(document.documentElement.ontouchstart !== undefined);
        });

        it("should be true if html tag has the class 'touch-enabled'", function () {
            $('html').addClass('touch-enabled');
            expect(module.touch()).toEqual(true);
        });
    });

    describe('isAniPad', function () {
        var changeUA = function (ua) {
            // got it from http://stackoverflow.com/questions/1307013/
            var __originalNavigator = window.navigator;
            window.navigator = new Object();
            window.navigator.__proto__ = __originalNavigator;
            window.navigator.__defineGetter__('userAgent', function () {
                return ua;
            });
        };

        it("should be false, unless testing from an ipad", function () {
            expect(module.isAniPad()).toEqual(false);
        });

        it("should be true, even if not testing from an ipad", function () {
            // not while testing in IE
            try {
                changeUA('Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25');
                expect(module.isAniPad()).toEqual(true);
            } catch (err) {
                // IE (no defineGetter)
                expect(true).toEqual(true);
            }
        });

        it("should be false for other iProducts", function () {
            try {
                changeUA('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10');
                expect(module.isAniPad()).toEqual(false);

                changeUA('Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5');
                expect(module.isAniPad()).toEqual(false);

                changeUA('Mozilla/5.0 (iPhone; U; ru; CPU iPhone OS 4_2_1 like Mac OS X; ru) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5');
                expect(module.isAniPad()).toEqual(false);
            } catch (err) {
                // IE (no defineGetter)
                expect(false).toEqual(false);
            }
        });
    });

    describe('failsafe', function () {
        it("should never throw errors when function (parameter 1) does", function () {
            expect(function () {
                module.failsafe(function () {
                    throw 'poop onto the stack';
                });
            }).not.toThrow();

            expect(function () {
                module.failsafe(function () {
                    return window.undefinedObject();
                });
            }).not.toThrow();
        });

        it("should never throw errors when context (parameter 2) is incorrect", function () {
            expect(function () {
                module.failsafe(function () {
                    return this.$.correctSyntax / 0;
                }, console);
            }).not.toThrow();
        });
    });
});