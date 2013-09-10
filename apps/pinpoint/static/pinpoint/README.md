# `pages.js`: How-to implement the features you want

## Edit the page's styles

1. Create `styles.css` in the `css/` directory. Do not edit `pages2.css`.
2. Override any styles you wish in `styles.css`. 
3. Never use inline styles.

## Change a template

There are many types of tiles available to you, all of which are suffixed with
`_template` in `index.html`.

To change the appearance of any template, *do not edit them*. Copy and paste
the template with a new id, with your company name prefixed. For example,

* to edit `product_tile_template`, copy and paste the `product_tile_template`
tag, and rename it to `yourStoreName_product_tile_template`.
* To edit `image_preview_template`, copy and paste the `image_preview_template`
tag, and rename it to `yourStoreName_image_preview_template`.

Your store name is case-sensitive.

## Create a template just for mobile devices

If `pages.js` thinks it is being viewed from a mobile device, it prefers
`abc_xyz_mobile_template` to `abc_xyz_template`. To override a desktop
template, create its mobile counterpart with a `_mobile` ID.

## Modify page behaviour

There is a `window.PAGES_INFO` or `window.TEST_PAGE_DATA` object on the page.
You can tweak values from there. *Never modify `pages.js`*.

## Add page behaviour

### Listen to events

`pages.js` notifies you of many events, all of which you can find by searching
`broadcast(...)` in the code. To do something when events are fired, use this
example code.

    SecondFunnel.vent.on({
        'previewRendered': function () {  // listen to the "previewRendered" event.
            console.log('bur... preview rendered');  // do something about it.
        }
    });

### Listen to events that `pages.js` doesn't broadcast

If you want to do something that `pages.js` was not designed to notify, you can
still write your own event handlers. For example, while `pages.js` does not
tell you if a certain link is clicked, you can still add events for it.

    new SecondFunnel.classRegistry.EventManager({
        'click .navbar-brand': function (ev) {  // (event) (selector)
            console.log('bur... custom event triggered');
        }
    });

### Add complex behaviour

Should you need to add more elaborate behaviour to your page, you can do so by
adding *widgets*.

    SecondFunnel.utils.addWidget(
        'gallery',  // name (must be unique)
        '.gallery',  // selector (scoped!)
        function (view, $el, option) {
            ...
        }
    );

Widgets are only available in certain page elements. Experiment with the code
to get an idea where it works and where it doesn't.

## Change the number of columns for the discovery area

Normally, you cannot. However, you can experiment with overriding the width of
`.container`, a style provided by `bootstrap.css`.

## Change the "hero image"

Assign background images to one or more of these selectors:
`.visible-xs.jumbotron, .visible-sm.jumbotron, .visible-md.jumbotron, .visible-lg.jumbotron`

## Add product information to the hero area

Write a `text/template` with the id `featured_template`. If this template
exists, it will replace the default `.jumbotron` area. Inside this template,
an `obj` object is available to you, containing information you provided in
`PAGES_INFO.featured` or `TEST_PAGE_DATA.featured`. An example featured
template would look like this.

    <script type="text/template" id="featured_template">
        <div class='featured product'>
            <!-- Main Display Area -->
            <img class='img-responsive pull-left' src='<%= obj.image %>' />
            <div class='pull-right'><%= obj.title %></div>
                <div class='price'><%= obj.price %></div>
                <div>
                    <a href='<%= obj.url %>' target='_blank'>BUY NOW</a>
                </div>
            </div>
        </div>

        <div class='spacer'></div>
    </script>