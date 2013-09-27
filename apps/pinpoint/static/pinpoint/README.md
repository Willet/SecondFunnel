# SecondFunnel: How-to implement the features you want

SecondFunnel campaigns are meant to present viewers with a visually-appealing
palette of products that encourages them to stay on the page and interact with
the products.

## Making a functioning page

A functioning landing page has to include the main elements in a page and at
least minimal templates.

It's recommended that you use [this example](example/example.html) and modify
it to match your needs.

If you choose to build your page from scratch, ensure you include all the
elements needed for SecondFunnel to function, and add the following at the
end of your HTML &lt;body&gt; element:

```html

<!-- Javascript Files -->
<script type="text/javascript" src="js/test_config.js"></script>
<script type="text/javascript" src="//connect.facebook.net/en_US/all.js"></script>
<script type="text/javascript" src="/static/js/respond.min.js"></script><!-- "as early after the css as possible" -->
<script type="text/javascript" src="/static/js/jquery.min.js"></script>
<script type="text/javascript" src="/static/js/jquery.mobile.swipeonly.min.js"></script>
<script type="text/javascript" src="/static/js/jquery.viewport.min.js"></script><!-- after jquery -->
<script type="text/javascript" src="/static/js/json2.js"></script>
<script type="text/javascript" src="/static/js/underscore.js"></script>
<script type="text/javascript" src="/static/js/backbone.js"></script>
<script type="text/javascript" src="/static/js/backbone.marionette.min.js"></script><!-- after backbone -->
<script type="text/javascript" src="/static/js/imagesloaded.pkgd.min.js"></script>
<script type="text/javascript" src="/static/js/jquery.masonry.pkgd.min.js"></script>
<script type="text/javascript" src="js/jquery.masonry.extensions.js"></script>
<script type="text/javascript" src="/static/js/bootstrap.min.js"></script>
<script type="text/javascript" src="js/pages.marionette.preinit.js"></script><!-- after marionette -->
<script type="text/javascript" src="js/pages.marionette.utils.js"></script>
<script type="text/javascript" src="js/pages.marionette.js"></script><!-- after preinit -->
<script type="text/javascript" src="js/pages.marionette.support.js"></script><!-- after marionette -->
<script type="text/javascript" src="js/pages.marionette.tracker.js"></script><!-- after marionette -->
<script type="text/javascript" src="js/pages.marionette.layoutengine.js"></script><!-- after marionette -->
<script type="text/javascript" src="js/pages.marionette.sharing.js"></script><!-- after marionette -->
<script type="text/javascript" src="js/pages.marionette.ir.js"></script><!-- after marionette -->
<script type="text/javascript" src="js/pages.marionette.viewport.js"></script><!-- after pages -->
<script type="text/javascript" src="js/pages.marionette.init.js"></script><!-- after pages -->
<script type="text/javascript" src="js/pages.marionette.widget.gallery.js"></script>
<script type="text/javascript" src="/static/js/css3-mediaqueries.js"></script><!-- IE8 -->
<script type="text/javascript">
    if (window.SecondFunnel) {
        // Start the SecondFunnel app
        SecondFunnel.start();
        window.sizeImage = SecondFunnel.utils.pickImageSize;  // export for designers

        // Example: add UI events
        new SecondFunnel.tracker.EventManager({
        'click .navbar-brand': function (ev) {
            console.log('bur... custom event triggered');
        }
        });

        // Example: handle right hand side link clicks
        new SecondFunnel.tracker.EventManager({
        'click .navbar-right a': function (ev) {
            var $ev = $(ev.currentTarget);

            console.log('Click detected! ' + $ev.attr('href'));
        }
        });


        // Example: receive event notifications
        receive({
        'previewRendered': function () {
            console.log('doh! preview rendered');
        }
        });
    }
</script>
<!-- End Javascript -->
```


## You will need

To create a new theme, you will need

- a web browser
- basic knowledge of HTML, CSS, JavaScript, and Underscore Templates

This tutorial includes a short introduction into working with UnderScore templates.

## Components of a landing page

A landing is a standard HTML page. The main parts in a SecondFunnel landing
page are:

- **the discovery feed**: the region that contains your campaign's tiles.

- **tiles**: images that are meant to give the viewer an idea about the
product behind the tile.

- **previews**: modals that include details about a product.

## Structure of a landing page

In order for SecondFunnel to function correctly, your page should contain
the element `div#discovery-area`

When SecondFunnel runs, and tiles are loaded, they are added to the page
as direct children of the div#discovery-area element.

A preview is loaded when a tile is clicked, and it is added as a direct
child of body.

The structure of the page with tiles and previews would look something like:

- `body`
    - `div.container`
        - `div#discovery-area`
        	- `div.tile`
    - `div.previewContainer`
        - `...`
            - `div.preview`

## Customizing a landing page

You can add content anywhere as long as the elements SecondFunnel requires are where they need to be.

If you would like to change the style of the page, create a **styles.css** in the **css/** directory. Do not use inline styles. If you would like to overwrite or add a style, include it in styles.css.

Elements you might want to consider styling:

- `.tile` tiles
- `.previewContainer` previews
- `.social-buttons` social buttons (maybe not)
- `.sharing` __not sure__
- `.previewContainer .price`

### Underscore templates

(You can find the full documentation [here](http://underscorejs.org/#template))

Templates are a method for adding HTML tags to content that has not added
to the page yet. Tiles and previews will be pulled from our servers, and
Underscore templates will add the HTML tags and attributes from the most
appropriate template.

Templates are used in tiles and previews as their content is fetched from our
servers after the page is loaded. They will take the fetched content and insert
it into the page the way you decide.

(TODO fix the following)

```

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
```

#### Defining templates

You define a template using the `<script type="text/template">` tag. You put
the template name in the script tag as an id attribute. For example, if your
template has the name "name", your template definition will have the tag
`<script type="text/template" id="name">`.

#### Template names

In SecondFunnel, template names follow a convention. The name of your template
will decide how specific it is. In order of decreasing specificity, the rules for
naming templates are:

(META these are tile templates. Make sure conventions apply everywhere.)
(TODO talk about them, finish. Add other templates if warranted)

- `store`_`content type`_`data type`_mobile_tile_template
- `content type`_`data type`_mobile_tile_template
- `store`_`data type`_mobile_tile_template
- `data type`_mobile_tile_template
- `store`_`content type`_image_tile_template
- `content type`_`data type`_tile_template
- `store`_`data type`_tile_template
- `data type`_tile_template

#### Template contents

Everything in your template will follow standard HTML and CSS rules, but you
also have access to variables related to the campaign.

The key to accessing those variables is the tag (TODO: wording) `<%- %>`.
Everything included between the opening and closing tag will be treated as
JavaScript. You do not need to know JavaScript to access the data.

Accessing the data is as simple as typing `object.field`. For example,
`obj.price` would give you the price of an item. `obj.name` will give you the
name of the product. The following fields are supported by most campaigns:

(TODO: add fields)

#### JavaScript in templates

You can insert JavaScript code between &lt;% and %&gt; tags that will execute at
that stage when the template is loading. A nifty and simple trick you can use is
`for` loops. For example, to iterate over the images of related products, you
can insert this following snippet into your template: (TODO: add snippet)

Another trick you can use in your template is checking whether a field exists.
You can do that using the `if` keyword. For instance,

```

<% if (obj.designer) { %>
	<%- obj.designer %> <!-- will only include the field if it exists. -->
<% } %>
```

## Optional Customizations

SecondFunnel supports the following features:

- Social buttons (enabled by default)
- Accordions
- Tabs

## Tabs
To add tabs to your page, you will need to follow the following example:

```html

<ul class="nav nav-tabs">
    <li class="active"> <a data-toggle="tab" data-target=".banana"> banana </a></li>
    <li> <a data-toggle="tab" data-target=".orange"> orange </a> </li>
    <li> <a data-toggle="tab" data-target=".apple"> apple </a> </li>
</ul>

<div class="tab-content">
    <div class="tab-pane description active banana">
        banana
    </div>

    <div class="tab-pane orange">
        orange
    </div>

    <div class="tab-pane apple">
        apple
    </div>
</div>
```

### Tab style

Include the titles of the tabs as a list (`ul` and `li` elements). Ensure `ul`
belongs to classes `nav` and `nav-tabs`.

Your **tab pages** should go under elements of class `.tab-pane`. You will
usually need to use a `div` element. Additionally, add the tab name as a class.
For example, if your tab is named tab1, `tab1` would have to be one of the
classes of your tab page.

### Tab behavior

The `data-toggle="tab"` attribute tells SecondFunnel this is a tab toggle, and
`data-target=".tab1"` indicates the target of this tab. Note that `.tab1` is a
`class`.

The class `.active` indicates which tabs are active. Marking a tab as active
in your page will make it the default tab. Ensure you have one active tab.

### Tab pages

The content of the tab page should go under an element of class `.tab-pane`.
This will indicate to SecondFunnel it needs to display it when the tab is
active and hide it otherwise.

## Accordions

To add an accordion to your page, follow the following example:

```html

<div class="accordion-container">
    <div class="panel-group"  id="my-accordion">
        <div class="panel panel-default">
            <a class="accordion-toggle" data-toggle="sf-collapse"
            data-target=".pineapple" data-parent="#my-accordion" >
                <div class=' panel-heading'>
                    pineapple title
                </div>
            </a>

            <div class="panel-collapse collapse in collapseOne">
                <div> pineapple content</div>
            </div>
        </div>

        <div class="panel panel-default">
            <a  class="accordion-toggle" data-toggle="sf-collapse"
            data-target=".papaya" data-parent="#my-accordion">
                <div class="panel-heading">
                    papaya title
                </div>
            </a>

            <div class="panel-collapse collapse collapseTwo">
                <div class="panel-body">
                    papaya content
                </div>
            </div>
        </div>
    </div>
</div>
```

SecondFunnel detects accordions when it finds the structure
`.accordion-container > .panel-group > .panel`.

Read the next section to learn about accordion style and setting accordion height.

### Accordion style

You need to follow the accordion structure to make sure your accordion will be styled
correctly.

To change the style of your accordion, you need to override one or more of the following:

- `.accordion-container > .panel-group > .panel > .accordion-toggle` Accordion toggles
- `.accordion-container > .panel-group > .panel > .panel-collapse` Accordion contents

Accordions have a constant height. If you would like to override the height, set
(TODO what element) to the desired height in your custom.css file.