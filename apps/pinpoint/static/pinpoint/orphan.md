
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
