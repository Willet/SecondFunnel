/*global describe, jasmine, it, beforeEach, expect */
describe("support", function () {
    var app,
        module,
        moduleName;

    beforeEach(function () {
        $('html').removeClass('touch-enabled');  // if present

        app = SecondFunnel;
        moduleName = jasmine.getEnv().currentSpec.suite.parentSuite.description;
        module = app[moduleName];
    });

    describe('mobile', function () {
        it("should not change", function () {
            expect(module.mobile()).toEqual(module.mobile());
        });
    });

    describe('touch', function () {
        it("should be overwritten", function () {
            expect(module.touch()).toEqual(false);
        });

        it("should be overwritten", function () {
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

        it("should be false (most of the time)", function () {
            expect(module.isAniPad()).toEqual(false);
        });

        it("should be true now", function () {
            // not while testing in IE
            changeUA('Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25');
            expect(module.isAniPad()).toEqual(true);
        });

        it("should be false for other iProducts", function () {
            changeUA('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10');
            expect(module.isAniPad()).toEqual(false);

            changeUA('Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5');
            expect(module.isAniPad()).toEqual(false);

            changeUA('Mozilla/5.0 (iPhone; U; ru; CPU iPhone OS 4_2_1 like Mac OS X; ru) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5');
            expect(module.isAniPad()).toEqual(false);
        });
    });

    describe('failsafe', function () {
        it("should never throw errors", function () {
            expect(function () {
                module.failsafe(function () {
                    throw 'poop onto the stack';
                });
            }).not.toThrow();
        });

        it("should never throw errors when context is madness", function () {
            expect(function () {
                module.failsafe(function () {
                    return this.$.correctSyntax / 0;
                }, console);
            }).not.toThrow();
        });
    });
});