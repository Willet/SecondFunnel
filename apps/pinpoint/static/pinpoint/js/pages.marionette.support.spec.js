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
        it("should be false (most of the time)", function () {
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