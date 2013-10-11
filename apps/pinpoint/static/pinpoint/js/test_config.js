window.PAGES_INFO = {
    'debug': 0,
    'base_url': "http://www.secondfunnel.com",
    'discoveryTarget': "#discovery-area",
    'itemSelector': ".tile",
    'store': {
        'id': "38",
        'name': "gap",
        'slug': "gap",  // required for store-specific themes
        'displayName': ""  // leave blank to use "Gap"
    },
    'page': {  // required
        'id': 9001,  // required
        'product': undefined,  // optional (supplied to featured template)
        'offline': false  // optional (if true, loads .content immediately)
    },
    'campaign': 96,
    'categories': [
        {  // you will still need to make elements with data-category="96" on the page.
            'id': 96
        },
        {
            'id': 97
        },
        {
            'id': 98
        },
        {
            'id': 99
        }
    ],
    'columnWidth': function($element) {
        return 240 + 15;
    },
    'events': undefined,  // page event bindings (optional)
    'socialButtons': [
        "facebook",
        "twitter",
        "pinterest",
        "tumblr",
        "share"  // who requested this feature?
     ], // optional
    //'shareSocialButtons': [], // optional; default: all
    'shareSources': {},  // optional: default: see sharing module
    'socialButtonsEnableCondition': function (button) {
        // required.
        // this function must return true for a social button to show
        // and return false for a social button not to show
        return true;
    },
    'showCount': true,  // optional, for social buttons (default: true)
    'enableTracking': true, // optional; default: true
    'eventMap': undefined,  // optional
    'tileElement': undefined,  // optional. alters the type of tag used by tiles.
    'imageTileWide': 0.25,
    'imageSizes': undefined,  // optional, overrides built-in size map
    'tapIndicatorText': undefined,  // optional
    'previewAnimationDuration': 100,  // in ms
    'previewMobileAnimationDuration': 0,
    'masonry': {  // passed to masonry
        'animationDuration': 0.4  // in seconds
    },
    'featured': { // the featured product
        "tile-id": 19325,
        "content-id": 19325,
        "name": "1969 ankle-zip legging skimmer jeans",
        "title": "1969 ankle-zip legging skimmer jeans",
        "url": "http://www.gap.com/browse/product.do?pid=600011002",
        "price": "$69.95",
        "tags": {
            "": "",
            "campaign": "99"
        },
        "db-id": 19325,
        "template": "product",
        "images": ["http://images.secondfunnel.com/store/gap/product/19325/image/54681ad98adb419528b985b73b8f21e2/master.jpg", "http://images.secondfunnel.com/store/gap/product/19325/image/41d0864dd5f98c7f23a58a6c7ce47c09/master.jpg", "http://images.secondfunnel.com/store/gap/product/19325/image/a2b381e086cfdd2aa6ea748940fafc5d/master.jpg"],
        "image": "http://images.secondfunnel.com/store/gap/product/19325/image/54681ad98adb419528b985b73b8f21e2/master.jpg",
        "id": "19325",
        "description": "Fabrication: Premium stretch knit. Hardware: Button closure, zip fly. Features: Five-pocket styling. Zipper detailing at coin pocket and ankle backs.\nCut: Mid-rise with a shorter length. Fit: Skinny through the hip and thigh. Leg opening: Skinny. Inseams: regular: 28\", tall: 32\", petite: 26\""
    },
    'initialResults': [  // stuff that loads when page loads, even if IR is available
        {
            'caption': "None",
            'content-id': 562949953426705,
            'content-type': "Instagram",
            'db-id': 5393,
            'image': "http://images.secondfunnel.com/store/gap/lifestyle/b127ff7bd36c348c8de82c8951f30ff1/master.gif",
            'original-id': "tumblr_mra6qu7uh11s6ofheo1_500",
            'template': "instagram",
            'tile-id': 562949953426705
        },
        {
            'caption': "None",
            'content-id': 562949953426705,
            'content-type': "Instagram",
            'db-id': 5393,
            'image': "http://images.secondfunnel.com/store/gap/lifestyle/b127ff7bd36c348c8de82c8951f30ff1/master.gif",
            'original-id': "tumblr_mra6qu7uh11s6ofheo1_500",
            'template': "instagram",
            'tile-id': 562949953426705
        },
        {
            'caption': "None",
            'content-id': 562949953426705,
            'content-type': "Instagram",
            'db-id': 5393,
            'image': "http://images.secondfunnel.com/store/gap/lifestyle/b127ff7bd36c348c8de82c8951f30ff1/master.gif",
            'original-id': "tumblr_mra6qu7uh11s6ofheo1_500",
            'template': "instagram",
            'tile-id': 562949953426705
        },
        {
            'caption': "None",
            'content-id': 562949953426705,
            'content-type': "Instagram",
            'db-id': 5393,
            'image': "http://images.secondfunnel.com/store/gap/lifestyle/b127ff7bd36c348c8de82c8951f30ff1/master.gif",
            'original-id': "tumblr_mra6qu7uh11s6ofheo1_500",
            'template': "instagram",
            'tile-id': 562949953426705
        }
    ],
    'IRResultsCount': 10,
    'IRTimeout': 5000,
    'IRSource': "http://intentrank-test.elasticbeanstalk.com/intentrank", // optional, defaults to intentrank-test
    'gaAccountNumber': 'UA-65432-1',  // UA-65432-1 is not a real account

    // number of viewports worth of results to keep below the page.
    // 0 is not an acceptable value, but 0.0001 is. default is 1,
    // i.e. there will always be one page worth of results
    // underneath, no matter how fast you scroll.
    'prefetchHeight': 1,

    'lockWidth': true,  // must be true (not 1, {}, ...) or a function that returns true
    'desiredWidth': 1024,

    'backupResults': [
        // stuff that loads when IR doesn't respond within PAGES_INFO.IRTimeout.
        // it really should contain at least 10 products.
        {
            'caption': "None",
            'content-id': 562949953426705,
            'content-type': "Instagram",
            'db-id': 5393,
            'image': "http://images.secondfunnel.com/store/gap/lifestyle/b127ff7bd36c348c8de82c8951f30ff1/master.gif",
            'original-id': "tumblr_mra6qu7uh11s6ofheo1_500",
            'template': "instagram",
            'tile-id': 562949953426705
        },
        {
            'caption': "None",
            'content-id': 562949953426705,
            'content-type': "Instagram",
            'db-id': 5393,
            'image': "http://images.secondfunnel.com/store/gap/lifestyle/b127ff7bd36c348c8de82c8951f30ff1/master.gif",
            'original-id': "tumblr_mra6qu7uh11s6ofheo1_500",
            'template': "instagram",
            'tile-id': 562949953426705
        }
    ]
};
