/*global describe, jasmine, it, beforeEach, expect */
describe("utils", function () {
    var app,
        module,
        moduleName,
        randomString = function (len, charSet) {
            charSet = charSet || 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 <>?,./;\':"[]{}!@#$~%^&*()_+-=\"';
            var randomString = '';
            for (var i = 0; i < len; i++) {
                var randomPoz = Math.floor(Math.random() * charSet.length);
                randomString += charSet.substring(randomPoz,randomPoz+1);
            }
            return randomString;
        };

    beforeEach(function () {
        app = SecondFunnel;
        module = app.utils;
    });

    describe('safeString', function () {
        it("should do nothing when keywords are missing", function () {
            var i,
                testStr = 'hello world';
            expect(module.safeString(testStr)).toEqual(testStr);

            for (i = 0; i < 1000; i++) {
                testStr = $.trim(randomString(100));
                expect(module.safeString(testStr)).toEqual(testStr);
            }
        });

        it("should do something when keywords are present", function () {
            expect(module.safeString("None")).toEqual('');
            expect(module.safeString("None ")).toEqual('');
            expect(module.safeString(" None")).toEqual('');
            expect(module.safeString(" None ")).toEqual('');
            expect(module.safeString(" False ")).toEqual('');
            expect(module.safeString(" false ")).toEqual('');
            expect(module.safeString(" undefined ")).toEqual('');
            expect(module.safeString(" Undefined ")).toEqual(" Undefined ");
            expect(module.safeString(" 0 ")).toEqual('');
            expect(module.safeString(" 0")).toEqual('');
        });

        it("should do something only when the keywords make up the entirety of the string, " +
            "excluding leading and trailing newlines, spaces " +
            "(including non-breaking spaces), and tabs", function () {
            expect(module.safeString("None was lost")).toEqual("None was lost");
            expect(module.safeString("There was None")).toEqual("There was None");
            expect(module.safeString("True  False Maybe")).toEqual("True  False Maybe");
            expect(module.safeString("$50.00")).toEqual("$50.00");
        });
    });

    describe('registerWidget', function () {
        it("should return true if it succeeds", function () {
            expect(module.registerWidget('derp', '', function () {})).toEqual(true);
        });
    });

    describe('addClass', function () {
        var defn = function () { return 5; };

        it("should return the definition of the class if the call succeeds", function () {
            expect(module.addClass('derp', defn)).toEqual(defn);
        });

        it("should register the class under its intended name", function () {
            expect(app.core.Derp).toEqual(defn);
        });
    });

    describe('findClass', function () {
        var app = SecondFunnel,
            defn = function () { return 5; },
            defn2 = function () { return 6; };

        app.utils.addClass('derp', defn);
        app.utils.addClass('derp2', defn2);

        it("should return the correct class", function () {
            expect(app.utils.findClass('derp')()).toEqual(5);
            expect(app.utils.findClass('derp2')()).toEqual(6);
        });
    });
});