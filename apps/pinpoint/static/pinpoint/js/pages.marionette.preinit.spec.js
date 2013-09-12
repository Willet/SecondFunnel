/*global describe, jasmine, it, beforeEach, expect */
describe("preinit", function () {
    var app;

    beforeEach(function () {
        app = SecondFunnel;
    });

    describe("Console", function () {
        it("exists / is stubbed", function () {
            expect(window.console).toBeDefined();
            expect(window.console.log).toBeDefined();
            expect(window.console.warn).toBeDefined();
            expect(window.console.error).toBeDefined();
        });
    });

    describe("String", function () {
        describe("truncate", function () {
            it("exists", function () {
                expect(String.prototype.truncate).toBeDefined();
            });

            it("works with empty strings", function () {
                expect("".truncate(0)).toEqual("");
                expect("".truncate(1)).toEqual("");
                expect("".truncate(999)).toEqual("");
                expect("".truncate(-1)).toEqual("");
                expect("".truncate(10, true)).toEqual("");
                expect("".truncate(10, true, true)).toEqual("");
                expect("".truncate(10, true, false)).toEqual("");
            });

            it("works with normal strings", function () {
                expect("1234567890".truncate(5)).toEqual("12345");
                expect("1234567890".truncate(5, true)).toEqual("12345");
                expect("1234567890".truncate(5, true, true)).toEqual("12...");
                expect("1234567890".truncate(10, true, true)).toEqual("1234567890");
            });
        });
    });

    describe("Required jQuery patches", function () {
        describe("getClasses", function () {
            it("exists", function () {
                expect($.fn.getClasses).toBeDefined();
            });

            // TODO: actually test it
        });

        describe("scaleImages", function () {
            it("exists", function () {
                expect($.fn.scaleImages).toBeDefined();
            });

            // TODO: actually test it
        });

        describe("getScripts", function () {
            it("exists", function () {
                expect($.getScripts).toBeDefined();
            });

            // TODO: actually test it
        });
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