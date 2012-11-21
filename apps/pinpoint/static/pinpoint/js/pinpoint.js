// TODO: Split into submodules properly
// http://www.adequatelygood.com/2010/3/JavaScript-Module-Pattern-In-Depth

// Why do we mix and match jQuery and native dom?
var PINPOINT = (function($){
    var hidePreview,
        init,
        load,
        loadFB,
        loadTwitter,
        parseUri,
        ready,
        scripts,
        showBlock,
        showPreview,
        trackEvent;

    /* --- START Utilities --- */
    /* --- END Utilities --- */

    /* --- START element bindings --- */



    showPreview = function() {
        var data     = $(this).find('.data').data(),
            $mask    = $('.preview.mask'),
            $preview = $('.preview.product');

        $.each(data, function(key, value) {
            $preview.find('.'+key).html(value)
            // TODO: Any special cases
        });

        // TODO: Render buttons

        $preview.fadeIn(100);
        $mask.fadeIn(100);
    };

    hidePreview = function() {
        var $mask    = $('.preview.mask'),
            $preview = $('.preview.product');

        $preview.fadeOut(100);
        $mask.fadeOut(100);
    };

    ready = function() {
        $('.block.product').on('click', showPreview);
        $('.preview.mask, .preview.close').on('click', hidePreview)

        // TODO: Render buttons
    };
    /* --- END element bindings --- */

    /* --- START Social buttons --- */
    loadFB = function () {
        console.log('Post FB load');
    };

    loadTwitter = function () {
        console.log('Post Twitter load');
    };
    /* --- END Social buttons --- */

    /* --- START tracking --- */
    trackEvent = function (event) {
        // TODO: replace with actual tracking
        console.log('Tracking event: ', event)
    };

    // override existing implementations of methods
    var oldLoadTwitter = loadTwitter;
    loadTwitter = function() {
        oldLoadTwitter();

        // TODO: Verify twttr exists
        window.twttr.ready(function(twttr) {
            twttr.events.bind('tweet', function(event) {
                trackEvent({
                    "network": "Twitter",
                    "type": "shared"
                });
            });

            twttr.events.bind('click', function(event) {
                var sType;
                if (event.region == "tweet") {
                    sType = "clicked";
                } else if (event.region == "tweetcount") {
                    sType = "leftFor";
                } else {
                    sType = event.region;
                }

                trackEvent({
                    "network": "Twitter",
                    "type": sType
                });
            });
        });
    }

    var oldLoadFB = loadFB;
    loadTwitter = function() {
        oldLoadFB();
    }
    /* --- END tracking --- */

    /* --- START Script loading --- */
    // Either a URL, or an object with 'script' key and optional 'onload' key
    scripts = [
        ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js',
    {
        'src'   : 'http://connect.facebook.net/en_US/all.js#xfbml=0',
        'onload': loadFB
    }, {
        'src'   : '//platform.twitter.com/widgets.js',
        'onload': loadTwitter
    }];

    load = function(scripts) {
        var item, script;

        // TODO: Check if already loaded?
        // Use a dictionary, or just check all script tags?
        for (var i=0; i < scripts.length; i++) {
            item   = scripts[i];

            script        = document.createElement('script');
            script.async  = true;
            script.src    = item.src    || item;
            script.onload = item.onload || function() {};
            document.head.appendChild(script);
        }
    };
    /* --- END Script loading --- */

    init = function() {
        var _gaq = window._gaq || (window._gaq = []);

        _gaq.push(['_setAccount', 'UA-35018502-1']);
        _gaq.push(['_trackPageview']);

        load(scripts);
        $(document).ready(ready);
    };

    return {
        'init': init
    };
})(jQuery);

PINPOINT.init()