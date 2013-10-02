# Adding Widgets to your Page

## Gallery

Creating a gallery is very simple. Insert a gallery into your template, and it
will make it possible for a viewer to look at different images of your product.

To insert a gallery, you will need two things:

- an image inside a `div.image`

```html
<div class='image'>
    <img src="..." />
</div>
```

- The element `div.gallery`

```
<% if(obj.images.length >1) { %>
    <div class='gallery'></div>
<% } %>
```

The gallery widget will replace the image inside `div.image` with the gallery
image that the user clicks on.

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
For example, if your tab is named yew, `yew` would have to be one of the
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

Read the next section to learn about accordion style and setting accordion
height.

### Accordion style

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
