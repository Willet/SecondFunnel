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
    });
});