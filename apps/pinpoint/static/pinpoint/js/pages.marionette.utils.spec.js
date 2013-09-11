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
        moduleName = jasmine.getEnv().currentSpec.suite.parentSuite.description;
        module = app[moduleName];
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
            expect(module.safeString(" 0 ")).toEqual('');
            expect(module.safeString(" 0")).toEqual('');
        });

        it("should not do anything when keywords are present, but between words", function () {
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

        it("should return anything but true if it fails", function () {
            // this call never fails
        });
    });

    describe('addClass', function () {
        var defn = function () { return 5; };

        it("should return its own definition if it succeeds", function () {
            expect(module.addClass('derp', defn)).toEqual(defn);
        });

        it("should actually add something", function () {
            expect(app.classRegistry.Derp).toEqual(defn);
        });

        it("should return anything but the definition if it fails", function () {
            // this call never fails
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

    describe('pickImageSize', function () {
        it("should do nothing on nothing", function () {
            expect(module.pickImageSize()).toEqual(undefined);
        });

        it("should do nothing on wrong link", function () {
            var link = 'http://ohai.ca/~/dev/null';
            expect(module.pickImageSize(link)).toEqual(link);

            link = 'http://placekitten.com/300/200';
            expect(module.pickImageSize(link)).toEqual(link);
        });

        it("should do the right thing on IS links", function () {
            var link = 'http://images.secondfunnel.com/a/b/c/master.jpg';
            expect(module.pickImageSize(link, 10))
                .toEqual('http://images.secondfunnel.com/a/b/c/pico.jpg');

            expect(module.pickImageSize(link, 15))
                .toEqual('http://images.secondfunnel.com/a/b/c/pico.jpg');

            expect(module.pickImageSize(link, 16))
                .toEqual('http://images.secondfunnel.com/a/b/c/pico.jpg');

            expect(module.pickImageSize(link, 17))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 31))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');
        });

        it("should be resolution-aware (i.e. unless you're running this test " +
            "on a retina macbook or something," +
            "master.jpg is not returned)", function () {
            var link = 'http://images.secondfunnel.com/a/b/c/master.jpg';
            expect(module.pickImageSize(link, 32))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 1500))
                .not.toEqual('http://images.secondfunnel.com/a/b/c/master.jpg');

            expect(module.pickImageSize(link, 1500))
                .not.toEqual('http://images.secondfunnel.com/a/b/c/master.jpg');

            expect(module.pickImageSize(link, 2047))
                .not.toEqual('http://images.secondfunnel.com/a/b/c/master.jpg');

            expect(module.pickImageSize(link, 2048))
                .not.toEqual('http://images.secondfunnel.com/a/b/c/master.jpg');

            expect(module.pickImageSize(link, 2049))
                .not.toEqual('http://images.secondfunnel.com/a/b/c/master.jpg');
        });

        it("should handle min/max parameters", function () {
            var link = 'http://images.secondfunnel.com/a/b/c/master.jpg';
            expect(module.pickImageSize(link, 31))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 32))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 33))
                .toEqual('http://images.secondfunnel.com/a/b/c/thumb.jpg');

            expect(module.pickImageSize(link, 33, 'max'))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');
        });
    });
});