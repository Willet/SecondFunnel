# Creating a SecondFunnel Theme

SecondFunnel campaigns are meant to present viewers with a visually-appealing
pallette of products that encourages them to stay on the page and interact with
the products.

Creating a theme is fast and simple. The only three things you need to use
are HTML, CSS, and Underscore templates.

## Making a functioning page

A functioning landing page has to include the main elements in a page and at
least minimal templates.

You can use [this example](example/example.html) and modify it to match your needs.

If you choose to build your page from scratch, ensure you include all the
elements needed for SecondFunnel to function, and add the following at the
end of your HTML <body> tag:

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
        SecondFunnel.start(SecondFunnel.options);
        window.sizeImage = SecondFunnel.utils.pickImageSize;  // export for designers

        // Example: add UI events
        new SecondFunnel.classRegistry.EventManager({
            'click .navbar-brand': function (ev) {
                console.log('bur... custom event triggered');
            }
        });

        // Example: handle right hand side link clicks
        new SecondFunnel.classRegistry.EventManager({
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

## Components of a landing page

A landing is a standard HTML page. The main parts in a SecondFunnel landing
page are:

(TODO fix)
  
- **the discovery feed**: the discovery feed is the region that contains the 
tiles for your campaign.
  
- **tiles**: images that are meant to give the viewer an idea about the 
product behind the tile.

- **previews**: Modals that include details about a product

## Structure of a landing page

A SecondFunnel landing page follows the following structure:

- `body`
    - `div.container`
        - `div#discovery-area`
            - `div.tile`
    - `div.previewContainer`
        - `...`
            - `div.preview`

## Demo

	(META moved to Creating a functioning page)
	
## Underscore templates

(You can learn everything you need to know about Underscore templates 
[here](http://underscorejs.org/#template))

Templates are a method for adding HTML tags to content that has not added
to the page yet. Tiles and previews will be pulled from our servers, and
Underscore templates will add the HTML tags and attributes based on the
template type they're associated with.

Templates are used in tiles and previews as their content is fetched from our
servers after the page is loaded. They will take the fetched content and insert
it into the page the way you decide.

### Defining templates

You define a template using the `<script type="text/template">` tag. You put
the template name in the script tag as an id attribute. For example, if your
template has the name "name", your template definition will have the tag
`<script type="text/template" id="name"`.

### Template names

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

### Template contents

Everything in your template will follow standard HTML and CSS rules, but you
also have access to variables related to the campaign.

The key to accessing those variables is the tag (TODO: wording) `<%- %>`.
Everything included between the opening and closing tag will be treated as
JavaScript. You do not need to know JavaScript to access the data.

Accessing the data is as simple as typing `object.field`. For example,
`obj.price` would give you the price of an item. `obj.name` will give you the
name of the product. The following fields are supported by most campaigns:

(TODO: add fields)

### JavaScript in templates

You can insert JavaScript code between those two tags that will execute at that
stage when the template is loading. A nifty and simple trick you can use is
`for` loops. For example, to iterate over the images of related products, you
can insert this following snippet into your template: (TODO: add snippet)


## Styling your page

Include your styles in a CSS file, and upload them to the server. Elements you
might want to consider customizing are:

- `body`
- `.tile` tiles
- `.previewContainer` previews
- `.social-buttons` social buttons (maybe not)
- `.sharing` __not sure__ 
- `.previewContainer .price`

## Adding social buttons

	(META should this be emphasized more than the other features? It feels important enough.)
## Optional Customizations

To make your page more appealing and to drive more traffic or achieve higher
conversion rates, you might want to add the following features to your page

- Social buttons
- Accordions
- Tabs

## Social buttons

To add social buttons to your page, you will simply need to include (TODO)

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

### Accordion style

You need to follow the accordion structure to make sure your accordion will be styled 
correctly.

To change the style of your accordion, you need to override one or more of the following:

- `.accordion-container > .panel-group > .panel > .accordion-toggle` Accordion toggles
- `.accordion-container > .panel-group > .panel > .panel-collapse` Accordion contents