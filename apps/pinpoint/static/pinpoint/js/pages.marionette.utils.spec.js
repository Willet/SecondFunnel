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
            expect(app.classRegistry.Derp).toEqual(defn);
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
        var validURLs = [
                // TODO: mustn't response also be an image?
                'ftp://example.com',
                'http://example.com/hello.jpg',
                'https://placekitten.com/100/100',
                '//ssl.gstatic.com/gb/images/k1_a31af7ac.png',
                'file:///home/bob/images/k1_a31af7ac.gif'
            ],
            invalidURLs = [
                undefined,
                '',
                'a',
                'abc',
                'The syntax of FTP URLs',
                'Testing «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!',
                true,
                false,
                null,
                {'url': ''},
                {'url': undefined},
                {'url': 'http://example.com'}
            ],
            isURLs = [
                'http://images.secondfunnel.com/a/b/c/master.jpg',
                'https://images.secondfunnel.com/store/newegg/product/15627/image/79078979342793572937598237894/pico.jpg',
                '//images.secondfunnel.com/store/newegg/product/15627/image/79078979342793572937598237894/icon.jpg',
                'http://images.secondfunnel.com/store/newegg/product/15627/image/79078979342793572937598237894/thumb.jpg',
                'https://images.secondfunnel.com/store/gap/product/15623/image/bbfdac708580d968208900f5fe8339a0/small.jpg',
                '//images.secondfunnel.com/store/gap/product/15623/image/bbfdac708580d968208900f5fe8339a0/compact.jpg',
                'http://images.secondfunnel.com/store/gap/product/15623/image/bbfdac708580d968208900f5fe8339a0/medium.jpg',
                'https://images.secondfunnel.com/store/gap/product/15627/image/8974ec565299b96dde8e6b9f580ccc24/large.jpg',
                '//images.secondfunnel.com/store/gap/product/15627/image/8974ec565299b96dde8e6b9f580ccc24/grande.jpg',
                'http://images.secondfunnel.com/store/gap/product/15627/image/8974ec565299b96dde8e6b9f580ccc24/1024x1024.jpg'
            ],
            nonISURLs = [
                // TODO: mustn't response also be an image?
                'http://ohai.ca/~/dev/null',
                'http://placekitten.com/300/200',
                'http://blogsearch.google.com/ping/RPC2',
                'http://blogshares.com/rpc.php',
                'http://blogstyle.jp/xmlrpc/',
                'http://coreblog.org/ping/',
                'http://feedfindings.com/rpc/',
                'http://feedsky.com/api/RPC2',
                'http://focuslook.com/ping.php',
                'http://geourl.org/ping/',
                'http://holycowdude.com/rpc/ping',
                'http://mapufacture.com/ping/api',
                'http://newsisfree.com/RPC',
                'http://ping.amagle.com/',
                'http://ping.bitacoras.com/',
                'http://ping.blo.gs/',
                'http://ping.blog360.jp/rpc',
                'http://ping.bloggers.jp/rpc',
                'http://ping.blogoon.net/',
                'http://ping.feedburner.com/',
                'http://ping.namaan.net/rpc/',
                'http://ping.syndic8.com/xmlrpc.php',
                'http://ping.weblogalot.com/rpc.php',
                'http://ping.wordblog.de/',
                'http://pinger.blogflux.com/rpc/',
                'http://rcs.datashed.net/RPC2',
                'http://rpc.blogcatalog.com/',
                'http://rpc.blogrolling.com/pinger/',
                'http://rpc.icerocket.com:10080/',
                'http://rpc.tailrank.com/',
                'http://rpc.technorati.com/rpc/ping',
                'http://rpc.weblogs.com/RPC2',
                'http://rssfwd.com/xmlrpc/api',
                'http://services.newsgator.com/ngws/xmlrpcping.aspx',
                'ftp://snipsnap.org/RPC2',
                '//topicexchange.com/RPC2',
                'https://trackback.bakeinu.jp/bakeping.php'
            ],
            dimensionsToTest = {
                '-1': 'pico',  // TODO: is this desirable?
                0: 'pico',
                1: 'pico',
                2: 'pico',
                10: 'pico',
                15: 'pico',
                16: 'pico',  // boundary
                17: 'icon',
                24: 'icon',
                31: 'icon',
                32: 'icon',  // boundary
                33: 'thumb',
                42: 'thumb',
                49: 'thumb',
                50: 'thumb',  // boundary
                51: 'small',
                75: 'small',
                99: 'small',
                100: 'small',  // boundary
                101: 'compact',
                135: 'compact',
                159: 'compact',
                160: 'compact',  // boundary
                161: 'medium',
                180: 'medium',
                239: 'medium',
                240: 'medium',  // boundary
                241: 'large',
                384: 'large',
                479: 'large',
                480: 'large',  // boundary
                481: 'grande',
                500: 'grande',
                599: 'grande',
                600: 'grande',  // boundary
                601: '1024x1024',
                750: '1024x1024',
                1023: '1024x1024',
                1024: '1024x1024',  // boundary
                1025: 'master',
                1280: 'master',
                1366: 'master',
                1600: 'master',
                2000: 'master',
                2048: 'master',
                2049: 'master',
                4096: 'master',
                8192: 'master',
                Infinity: 'master'
            };

        it("should throw an exception if URL is missing, too short, " +
            "or invalid, and should not throw an exception unless URL is missing, " +
            "too short, or invalid", function () {

            _.each(invalidURLs, function (url) {
                expect(function () {
                    return module.pickImageSize(url);
                }).toThrow();
            });

            _.each(validURLs, function (url) {
                expect(function () {
                    return module.pickImageSize(url);
                }).not.toThrow();
            });
        });

        it("given valid URL, unless the URL is an ImageService URL, " +
            "return the same URL", function () {

            _.each(nonISURLs, function (url) {
                expect(module.pickImageSize(url)).toEqual(url);
            });
        });

        it("given valid URL, if the URL is an ImageService URL, " +
            "return the same URL, with its file name changed " +
            "(or unchanged, if current window size exceeds the size of " +
            "the dimensions of master.jpg) to the file name of the " +
            "image of dimensions that is the least large, among the list of " +
            "qualifying image dimensions that are at least as large as the " +
            "requested dimensions, width-wise or length-wise", function () {

            _.each(isURLs, function (url) {
                _.each(dimensionsToTest, function (imgName, size) {
                    // "found" condition
                    var maxLogicalSize = Math.min($(window).width(), $(window).height());
                    if (size <= maxLogicalSize) {
                        // when not subject to window size
                        expect(module.pickImageSize(url, size)
                            .indexOf(imgName))
                            .toBeGreaterThan(-1);
                    }
                });
            });
        });

        it("should be resolution-aware (given the current screen is less than " +
            "2048px in either width or height, master.jpg is not served)", function () {
            var maxLogicalSize = Math.min($(window).width(), $(window).height());

            if (maxLogicalSize < 1024) {
                // current screen size constraints output
                // = never master.jpg
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('master'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 600) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('1024x1024'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 480) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('grande'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 240) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('large'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 160) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('medium'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 100) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('compact'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 50) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('small'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 32) {
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('thumb'))
                            .toEqual(-1);
                    });
                });
            }

            if (maxLogicalSize < 16) {
                // base case (pico is always served even if window has 0 width)
                _.each(isURLs, function (url) {
                    _.each(dimensionsToTest, function (imgName, size) {
                        expect(module.pickImageSize(url, size)
                            .indexOf('pico'))
                            .not.toEqual(-1);
                    });
                });
            }
        });

        it("should handle min/max parameters", function () {
            var link = 'http://images.secondfunnel.com/a/b/c/master.jpg';
            expect(module.pickImageSize(link, 31))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 31, 'min'))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 31, 'max'))
                .toEqual('http://images.secondfunnel.com/a/b/c/pico.jpg');

            expect(module.pickImageSize(link, 32))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 32, 'min'))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');

            expect(module.pickImageSize(link, 32, 'max'))
                .toEqual('http://images.secondfunnel.com/a/b/c/pico.jpg');

            expect(module.pickImageSize(link, 33))
                .toEqual('http://images.secondfunnel.com/a/b/c/thumb.jpg');

            expect(module.pickImageSize(link, 33, 'min'))
                .toEqual('http://images.secondfunnel.com/a/b/c/thumb.jpg');

            expect(module.pickImageSize(link, 33, 'max'))
                .toEqual('http://images.secondfunnel.com/a/b/c/icon.jpg');
        });
    });
});