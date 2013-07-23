// Order matters!
// This is the base JS file, the first file that is called when we test the
// sauce for the SecondFunnel project.  It instantiates the needed modules.
var Willet = Willet || {}, 
    local_data = local_data || {};

window.PAGES_INFO = {
    // Static info to use?  Or change as needed?
    'base_url': "http://127.0.0.1:8000",
    'page': {
        'pubDate': "",
        'id': "32",
        'main-block-template': "shop-the-look",
        'SHUFFLE_RESULTS': true,
        'stl-image': '',
        'featured-image': "",
        'description': "",
        'offline': false,
        'product': "",
        'categories': [],
    },        
    'store': {
        'id': "nativeshoes",
        'name': "Native Shoes",
    },
    'product': {
        'name': "Jimmy - Jiffy Black",
        'product-id': "5383",
    },
    'content': [],
    'featured': {
        'id': "5383",
        'name': "Jimmy - Jiffy Black"
    },
    'backupResults': []
};