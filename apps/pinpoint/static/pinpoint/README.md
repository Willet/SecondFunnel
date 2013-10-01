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
- (our example)[example.html]
- this tutorial
- [the style document](style.md)

## Making a functioning page

Use [this example](example.html) as the basis for your page. Modify it according
to this introduction and (style.md)[style.md] to achieve the appearance you
want.
In order for SecondFunnel to function, your page has to include:

- at least minimal templates
- the element
  ```html
  <div id="discovery-area></div>
  ```
- the stylesheets included in the example.
- the scripts included in the example.


## Components of a landing page

The main parts in a SecondFunnel landing page are:

- **tiles**: images that are meant to give the viewer an idea about your
  products.

- **the discovery feed**: the region that contains your campaign's tiles.

- **previews**: modal dialogs that include details about a product.

## Structure of a landing page

You can add content anywhere as long as
```html
<div id="discovery-area></div>
```
is present.

**Tiles** are direct children of the div#discovery-area
element.

A **preview** is a direct child of body.

The structure of the page with tiles and previews would look something like:

- `body`
    - `div.container` discovery feed wrapper
        - `div#discovery-area` discovery feed (collection of tiles)
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

If you need to modify a template, please refer to
[the templates  documentation](templates.md)

## Widgets

SecondFunnel supports the following widgets:

- gallery
- tabs
- accordions

You can find demos and tutorials related to those widgets in
[the widgets tutorial](widgets.md)

## Further reading

- [Customising the look of your page](style.md)
- [Adding widgets to your page](widgets.md)
- [Using templates with SecondFunnel](technical.md)