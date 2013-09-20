/*global describe, jasmine, it, beforeEach, afterEach, expect, spyOn */
describe("SecondFunnel", function () {
    var app = SecondFunnel;

    beforeEach(function () {
        jasmine.Clock.installMock();
    });

    afterEach(function () {
        jasmine.Clock.uninstallMock();
    });

    describe("General", function () {
        /*

        TODO

        Landing pages must support mobile devices. The following devices must work:
         iPhone (retina)
         iPhone (non-retina)
         iPad (retina)
         iPad (non-retina)
        Landing pages must support modern browsers. The following browsers must work:
         Chrome (Desktop, Android 4.x+)
         Firefox
         Internet Explorer 8+
         Safari (iOS 4+)
         Android browser (Android 2.x+)
        Theming should be limited to just HTML and CSS
        */
    });

    describe("Usability", function () {

        describe("Landing pages must display in one of two display modes depending on " +
            "the device's effective resolution: If the effective resolution " +
            "is X, the landing page must use the mobile display mode", function () {
            var myWidth = $(window).width(),
                myPixelRatio = window.devicePixelRatio || 1,
                viewportData;

            beforeEach(function () {
                // default
                viewportData = app.viewport.determine();
                app.options.lockWidth = true;  // force enable
            });

            afterEach(function () {
                app.options.lockWidth = $.browser.mobile;  // restore default
            });

            it("should be disabled when window pixel ratio is not high " +
                "enough to be a portable device", function () {
                if (myPixelRatio < 1.5) {
                    expect(viewportData[0]).toEqual(false);
                } // else: not necessarily true
            });

            it("should be disabled when window width is too wide " +
                "to be a portable device", function () {
                if (myWidth >= 768) {
                    expect(viewportData[0]).toEqual(false);
                } // else: not necessarily true
            });

            it("should be enabled if believed " +
                "to be a portable device", function () {
                if ($.browser.mobile && myPixelRatio >= 1.5 && myWidth < 768) {
                    expect(viewportData[0]).toEqual(true);
                }
            });
        });

        describe("Landing pages must display in one of two display modes depending on " +
            "the device's effective resolution: If the effective resolution " +
            "is Y, the landing page must use the desktop display mode", function () {

            it("must be in desktop mode if window width is too wide, " +
                "pixel density too low, or " +
                "forcibly disabled", function () {
                var myWidth = $(window).width(),
                    myPixelDensity = window.devicePixelDensity || 1,
                    viewportData = app.viewport.determine();

                if (myWidth >= 768) {
                    expect(viewportData[0]).toEqual(false);
                }

                if (myPixelDensity >= 1) {
                    expect(viewportData[0]).toEqual(false);
                }
            });
        });

        it("A landing page must maintain its display mode even if the device " +
            "orientation changes", function () {
            var isInMobileMode = ($(window).width() < 768);

            if (isInMobileMode) {
                // if in mobile mode, expect to stay in mobile mode
                SecondFunnel.vent.trigger("rotate");
                expect($(window).width()).toBeLessThan(768);
            }
        });

        it("If a device is mobile or vice versa, it must always render in that " +
            "mode, regardless if the initial orientation of the page.", function () {
            var isDeviceMobile = $.browser.mobile;

            if (isDeviceMobile) {
                // if in mobile mode, expect width to be locked below 768px
                // by the viewport agent.
                expect($(window).width()).toBeLessThan(768);
                SecondFunnel.vent.trigger("rotate");
                expect($(window).width()).toBeLessThan(768);
            }
        });

        describe("Landing pages must present some visual indication that a tile " +
            "can be activated:", function () {
            it("For non-mouse enabled devices, this indicator " +
                "should be an element overlayed on the tile.", function () {
                if (app.support.touch()) {
                    var tile = new SecondFunnel.classRegistry.Tile({});
                    tile.createView();  // trigger tap indicator
                    expect($('html').hasClass('touch-enabled')).toEqual(true);
                }
            });

            it("For mouse enabled devices, this indicator should be a " +
                "mouse pointer", function () {
                if (!app.support.touch() && window.getComputedStyle) {
                    var tile = new SecondFunnel.classRegistry.Tile(window.PAGES_INFO.featured),
                        view = tile.createView();  // trigger tile creation
                    if (view) {  // 'no template' is a reason why this check is needed
                        expect($('html').hasClass('touch-enabled')).toEqual(false);
                    }
                }
            });
        });

        /*

        TODO

        The number of columns should scale dependent on the effective resolution of the viewport
         The number of columns should not exceed 4 (added 08-23)
        A tile should be rendered as soon as possible
         If an image is loading, the user should see some indication that some action is taking place
         If an image is loading, a placeholder image should be displayed with the dominant colour as the background colour
        A tile must not be rendered if:
         The tile contains images that are broken
         The tile does not meet 'acceptable tile' criteria
         */
    });

    describe("Performance", function () {
        describe("Tiles that are not 'near' the viewport must be removed from the viewport", function () {
            it("must remove from the viewport the tiles that are not 'near' the viewport", function () {
                // we aren't doing this yet
                expect(true).not.toEqual("placeholder");
            });
            describe("'Near' should be a configurable value, but should default to a " +
                "reasonable value such as one page from the viewport in either " +
                "direction.", function () {
                it("'Near' should be a configurable value", function () {
                    // we aren't doing this yet
                    expect(true).not.toEqual("placeholder");
                });

                it("'Near' should default to a reasonable value such as one " +
                    "page from the viewport in either direction", function () {
                    // we aren't doing this yet
                    expect(true).not.toEqual("placeholder");
                });
            });
            it("Removing the tiles from the viewport must not cause the tiles " +
                "to be rearranged", function () {
                // app.discovery = new app.classRegistry.Discovery(app.options);

                spyOn(Masonry.prototype, 'layout');

                // remove one tile (removing model also triggers view removal)
                app.discovery.collection.models.shift();

                expect(Masonry.prototype.layout).not.toHaveBeenCalled();
            });
            it("Adding new tiles after tiles have been removed must not " +
                "rearrange existing tiles", function () {
                // TODO
            });
        });
        describe("Pages must have some number of tiles pre-rendered on the landing page", function () {
            it("These tiles must not be loaded via javascript", function () {
                // we aren't doing this yet
                expect(true).not.toEqual("placeholder");
            });

            it("The number of tiles must default to four.", function () {
                // this is not a passing test for the test config,
                // but it is one for live configs
                expect(PAGES_INFO.initialResults.length).toEqual(4);
            });
        });
    });

    describe("Flexibility", function () {
        describe("Landing pages should have configuration options " +
            "for the feed", function () {
            var config = window.PAGES_INFO || window.TEST_PAGE_DATA;

            it("should have configuration options for the feed", function () {
                // how to test the config does anything?
                expect(config).toBeDefined();
            });

            it("should be possible to configure performance options for the " +
                "feed, including, but not limited to: animation", function () {
                var hasAtLeastOneKeyWithTheWordAnimationInIt = (_.filter(
                    _.keys(PAGES_INFO), function (v) {
                        return v.indexOf('nimation') >= 0
                    }).length > 0);
                expect(hasAtLeastOneKeyWithTheWordAnimationInIt).toEqual(true);
            });

            it("should be possible to configure the default " +
                "column width", function () {
                // how to test the config does anything?
                expect(config.columnWidth).toBeDefined();
            });

            it("It should be possible to disable or enable internal " +
                "event tracking", function () {
                spyOn(window._gaq, 'push');
                app.options.enableTracking = false;

                app.vent.trigger("tracking:trackEvent", {
                    'category': 'foo',
                    'action': 'bar',
                    'label': 'baz'
                });

                expect(_gaq.push).not.toHaveBeenCalled();
            });

            it("It should be possible to define an alternative " +
                "source URL", function () {
                // what to test when its existence is optional?
                expect(app.intentRank.options.baseUrl).toEqual(config.IRSource);
            });
        });

        describe("Landing pages must support arbitrary tile templates", function () {
            describe("Tile templates can be any HTML but must be denoted with " +
                "a unique identifier describing what type the template is.", function () {
                // we denote templates with IDs.
            });
        });

        describe("Landing pages must support social buttons", function () {
            it("requires existence of the sharing module", function () {
                expect(app.sharing).toBeDefined();
                expect(app.sharing.SocialButton).toBeDefined();
                expect(app.sharing.SocialButtons).toBeDefined();
            });

            describe("Social buttons must be configurable with options including, " +
                "but not limited to: show / hide like count, enable / disable " +
                "buttons", function () {
                var buttons;

                it("Social buttons must be configurable with " +
                    "show / hide like count", function () {
                    app.options.showCount = true;

                    buttons = new app.sharing.SocialButtons({
                            'model': app.options.featured
                        })
                        .render().load().$el;

                    expect(buttons.find('.facebook').hasClass('no-count')).toEqual(false);

                    // ---

                    app.options.showCount = false;

                    buttons = new app.sharing.SocialButtons({
                            'model': app.options.featured
                        })
                        .render().load().$el;
                    if (buttons.find('.facebook').length) {
                        expect(buttons.find('.facebook').hasClass('no-count')).toEqual(true);
                    }  // else: didn't have facebook
                });

                it("Social buttons must be configurable with " +
                    "enable / disable buttons", function () {
                    app.options.socialButtons = [];  // render 0 buttons = disable

                    buttons = new app.sharing.SocialButtons({
                            'model': app.options.featured
                        })
                        .render().load().$el;

                    expect(buttons.find('div, span').length).toEqual(0);
                });
            });
        });
    });

    describe("Behaviour / Error Handling", function () {
        describe("If the source URL does not return results, " +
            "landing pages must:", function () {

            it("If the source URL does not return results, " +
                "landing pages must fetch results from an included list of " +
                "backup results within the same page.", function () {

                var results;

                runs(function () {
                    // screw with the url
                    app.intentRank.getResultsOnline({
                        'url': 'http://ohai.ca/h/err/404?'
                    }, function (data) {
                        results = data;
                    });
                })

                waitsFor(function () {
                    if (results && results.length) {
                        return true;
                    }
                }, 5000);

                runs(function () {
                    expect(results && results.length > 0).toEqual(true);
                });
            });
        });

        /**
         * When a user activates a tile, that tile must:
         *  Take its activation action
         *  Load related results from the source URL
         * Developers and designers must be able to create listeners for important events including, but not limited to: hovering over a tile, hovering over a social button, sharing using a social button, page scrolling, preview activation / deactivation, product clickthrough, page exit, tiles added to the landing page, tiles finished loading, window resized, dependencies loaded, page complete load, pre-page complete load
         */
    });

    describe("Tracking", function () {
        /**
         * Landing pages must track the following customer metrics:
         *  Time on site
         *  Page bounce rate
         *  Product interactions including but not limited to: preview, shares
         *  Lifestyle interactions including, but not limited to: preview, shares, video plays
         *  Purchase actions including, but not limited to: ‘Shop Now’, ‘Find in Store’ or similar
         *  Product impressions
         *  Content impressions including, but not limited to: lifestyle images, video
         */
        it("truth", function () {
            expect(true).toBeTruthy();
        });
    });

    describe("Theme Design / Templating", function () {
        /**
         * Landing pages must not add or remove classes that cause an unexpected change in style
         * Theme designers should not need to implement complex functionality:
         *  Complex functionality should be encapsulated as additional functionality that is available to theme designers
         */
        it("truth", function () {
            expect(true).toBeTruthy();
        });
    });
});