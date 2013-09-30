# SecondFunnel: An Introduction

SecondFunnel campaigns are meant to present viewers with a visually-appealing
palette of products that encourages them to stay on the page and interact with
the products.

This tutorial will give you an overview of SecondFunnel pages and show you how
to get your page running.

## You will need

To create a new theme, you will need

- a web browser
- a text editor
- basic knowledge of **HTML**, **CSS**, and **JavaScript**

This tutorial includes a short introduction into using Underscore templates with
SecondFunnel.

## Making a functioning page

A functioning landing page has to include the main elements in a page and at
least minimal templates.

Take a look at [this example](example.html) and modify it to match your needs.

## Components of a landing page

A landing page is a standard HTML page. The main parts in a SecondFunnel landing
page are:

- **tiles**: images that are meant to give the viewer an idea about your
  products.

- **the discovery feed**: the region that contains your campaign's tiles.

- **previews**: modal dialogs that include details about a product.

## Structure of a landing page

In order for SecondFunnel to function correctly, your page should contain
the element
```html
<div id="discovery-area"></div>
```

You can add content anywhere as long as `div#discovery-area` is present.

**Tiles** are added to the page as direct children of the div#discovery-area
element.

A **preview** is added to the page as a direct child of body.

The structure of the page with tiles and previews would look something like:

- `body`
    - `div.container` discovery feed wrapper
        - `div#discovery-area` discovery feed (tiles)
            - `div.tile` individual tiles
    - `div.previewContainer` preview wrapper
        - `div.tablecell`
            - `div.content` preview content

## Customizing a landing page

To learn about changing the style of your page, please refer to
[the style document](style.md)

### Using templates

To make it easier to theme a landing page, its parts are broken down into
several Underscore templates.
You can find the full template documentation
[here](http://underscorejs.org/#template)



If you need to modify a template, please refer to [the templates section in the
technical documentation](technical.md#templates)

## Widgets

SecondFunnel supports the following widgets:

- tabs
- accordions

### Tabs
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

#### Tab style

Include the titles of the tabs as a list (`ul` and `li` elements). Ensure `ul`
belongs to classes `nav` and `nav-tabs`.

Your **tab pages** should go under elements of class `.tab-pane`. You will
usually need to use a `div` element. Additionally, add the tab name as a class.
For example, if your tab is named yew, `yew` would have to be one of the
classes of your tab page.

#### Tab behavior

The `data-toggle="tab"` attribute tells SecondFunnel this is a tab toggle, and
`data-target=".tab1"` indicates the target of this tab. Note that `.tab1` is a
`class`.

The class `.active` indicates which tabs are active. Marking a tab as active
in your page will make it the default tab. Ensure you have one active tab.

#### Tab pages

The content of the tab page should go under an element of class `.tab-pane`.
This will indicate to SecondFunnel it needs to display it when the tab is
active and hide it otherwise.

### Accordions

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

Read the next section to learn about accordion style and setting accordion
height.

#### Accordion style

You need to follow the accordion structure to make sure your accordion will be
styled
correctly.

To change the style of your accordion, you need to override one or more of the
following:

- `.accordion-container > .panel-group > .panel > .accordion-toggle` Accordion
toggles
- `.accordion-container > .panel-group > .panel > .panel-collapse` Accordion
contents

Accordions have a constant height. If you would like to override the height, set
(TODO what element) to the desired height in your custom.css file.

## Further reading

- [customizing the look of your page](style.md)
- [web development documentation](technical.md)