/*global describe, jasmine, it, beforeEach, expect */
describe("preinit", function () {
    var app,
        randomLowerCaseStringSpaced = function (len) {
            var charSet = 'abcdefghijklmnopqrstuvwxyz ';
            var randomString = '';
            for (var i = 0; i < len; i++) {
                var randomPoz = Math.floor(Math.random() * charSet.length);
                randomString += charSet.substring(randomPoz,randomPoz+1);
            }
            return randomString;
        };

    beforeEach(function () {
        app = App;
        jasmine.Clock.installMock();
    });

    afterEach(function () {
        jasmine.Clock.uninstallMock();
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

        describe("getScripts", function () {
            it("exists", function () {
                expect($.getScripts).toBeDefined();
            });

            // TODO: actually test it
        });
    });

    describe("Required Underscore patches", function () {
        describe("capitalize", function () {
            it("exists", function () {
                expect(_.capitalize).toBeDefined();
            });

            it("always converts first character to upper", function () {
                expect(_.capitalize('')).toEqual('');
                expect(_.capitalize('abc')).toEqual('Abc');
                expect(_.capitalize('aBC')).toEqual('ABC');
                expect(_.capitalize('abc_def')).toEqual('Abc_def');
                expect(_.capitalize('abc def')).toEqual('Abc def');
            });

            it("never converts characters after the first character to upper", function () {
                var str = '', comp = '';

                // verify that other characters are never converted to upper
                for(var i = 10000; i < 10100; i++) {
                    // generate a random string of length i
                    str = randomLowerCaseStringSpaced(i);
                    comp = str.toLowerCase();
                    expect(_.capitalize(str).substring(1))
                               .toEqual(comp.substring(1));
                }
            })
        });

        describe("get", function () {
            it("exists", function () {
                expect(_.get).toBeDefined();
            });

            it("works", function () {
                expect(_.get({}, 'derp')).not.toBeDefined();
                expect(_.get({}.derp, 'derp')).not.toBeDefined();
                expect(_.get({'a': 'b'}, 'a')).toEqual('b');
            });
        });
    });

    describe("Required Marionette patches", function () {
        describe("missing template mofo", function () {
            it("works for View", function () {
                var DummySubclass = Marionette.View.extend({
                        'template': '#templateThatNeverExists',
                        'onMissingTemplate': $.noop
                    }),
                    dvInstance = new DummySubclass();
                spyOn(dvInstance, 'onMissingTemplate');

                dvInstance.render();

                expect(dvInstance.onMissingTemplate).toHaveBeenCalled();
            });

            it("works for CompositeView", function () {
                var DummySubclass = Marionette.CompositeView.extend({
                        'template': '#templateThatNeverExists',
                        'onMissingTemplate': $.noop
                    }),
                    dvInstance = new DummySubclass();
                spyOn(dvInstance, 'onMissingTemplate');

                dvInstance.render();

                expect(dvInstance.onMissingTemplate).toHaveBeenCalled();
            });

            it("works for ItemView", function () {
                var DummySubclass = Marionette.ItemView.extend({
                        'template': '#templateThatNeverExists',
                        'onMissingTemplate': $.noop
                    }),
                    dvInstance = new DummySubclass();
                spyOn(dvInstance, 'onMissingTemplate');

                dvInstance.render();

                expect(dvInstance.onMissingTemplate).toHaveBeenCalled();
            });
        });
    });
});
