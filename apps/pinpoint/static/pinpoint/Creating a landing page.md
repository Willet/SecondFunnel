# Creating a SecondFunnel campaign
(TODO: talk about what SF campaigns are about)

SecondFunnel campaigns are meant to present viewers with a visually-appealing
pallette of products that encourages them to stay on the page and interact with
the images on the page.

Creating a campaign is fast and simple. The only three things you need to use
to create one are HTML, CSS, and Underscore templates.

## Creating a functioning page

A functioning landing page has to include the main elements in a page and at
least minimal templates.

If there are issues, fix them. Otherwise, proceed.

## Components of a landing page

A landing is a standard HTML page. The main parts in a SecondFunnel landing
page are:

(TODO fix)

- the "hero image" `.visible-xs.jumbotron`, `.visible-sm.jumbotron`,
  `.visible-md.jumbotron`, `.visible-lg.jumbotron`

    This image will be visible at the top of your page. It will be big, and it
will communciate what your page is about. The various classes exist for
different screen sizes.
  
- the discovery feed `div#discovery-area`

    The discovery feed is the region that contains the tiles for your campaign.
  
- tiles `div.tile`

    Tiles are images and additional elements you might choose to include. They
are meant to give the viewer an idea about the product behind the tile.

- previews `div.preview`

    Previews can be thought of as expanded tiles. They are modals that sit on
top of the page, and they become the focus of the browser when they are
clicked. Previews should give the details about a product.

## Structure of a landing page

A SecondFunnel landing page follows the following structure:

- `body`
    - `div.container`
        - `div.discovery-area`
            - `div.tile`
    - `div.previewContainer`
        - `...`
            - `div.preview`

## Demo

    (TODO Insert simple demo here)

## Underscore templates

Underscore templates are a method for adding HTML tags to content that has not
added to the page yet. Tiles and previews will be pulled from our servers, and
Underscore templates will add the HTML tags and attributes based on their
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
will decide how specific it is. (TODO explain names)

### Template contents

Everything in your template will follow standard HTML and CSS rules, but you
also have access to variables related to the campaign.

The key to accessing those variables is the tag (TODO: wording) `<% %>`.
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
# Optional Customizations

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
    <li class="active"> <a data-toggle="tab" data-target=".tab1"> tab1 </a></li>
    <li> <a data-toggle="tab" data-target=".tab2"> tab2 </a> </li>
    <li> <a data-toggle="tab" data-target=".tab3"> tab3 </a> </li>
</ul>

<div class="tab-content">
    <div class="tab-pane description active tab1">
        tab1
    </div>
    
    <div class="tab-pane tab2">
        tab2
    </div>
    
    <div class="tab-pane tab3">
        tab3
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
            <a class="accordion-toggle" data-toggle="sf-collapse" data-target=".collapse1" data-parent="#my-accordion" >
                <div class=' panel-heading'>
                    collapse1 title
                </div>
            </a>

            <div class="panel-collapse collapse in collapseOne">
                <div> collapse1 content</div>
            </div>
        </div>


        <div class="panel panel-default">
            <a  class="accordion-toggle" data-toggle="sf-collapse" data-target=".collapse2" data-parent="#my-accordion">
                <div class="panel-heading">
                    collapse2 title
                </div>
            </a>

            <div class="panel-collapse collapse collapseTwo">
                <div class="panel-body">
                    collapse2 content
                </div>
            </div>
        </div>
    </div>
</div>
```
SecondFunnel detects accordions when it finds the structure `.accordion-container > .panel-group > .panel`.

### Accordion style

You need to follow the accordion structure to make sure your accordion will be styled correctly.

To change the style of your accordion pages, modify the style of 
