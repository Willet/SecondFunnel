# Customising the Look of your Page

Make sure you read [the intro](README.md) first as this document builds on the
information presented there.

## Desktop and Mobile

SecondFunnel is meant to be viewed on both desktops and mobile devices. It's
important to keep that in mind as you create your theme.

To make it possible to render all the elements on both types of devices,
SecondFunnel detects the type of the device it's being viewed on at every level
and makes decisions based on that.

### Templates

You already know there are tile and preview templates. If you have read
[the template reference](template.md), you also know that there are mobile
and desktop templates. Mobile templates are used when SecondFunnel believes it's
being viewed on a mobile device.

You can override either one or both type of templates. Refer to the template
reference for information on that.

### CSS

We make use of the BootStrap library, which includes several styles that make
it possible to display or hide elements at different resolution levels. You
can refer to [the BootStrap documentation](http://getbootstrap.com/css/) to
learn about how you can use those classes.

## Structure of a landing page

**Tiles** are direct children of the discovery feed `div#discovery-area`

A **preview** is a direct child of `body`.

The structure of the page with tiles and previews would look something like:

- `body`
    - `div.container` discovery feed wrapper
        - `div#discovery-area` discovery feed (collection of tiles)
            - `div.tile` individual tiles
    - `div.previewContainer` preview wrapper
        - `div.tablecell`
            - `div.content` preview content

## Elements you might want to decorate

- tiles: `.tile`
- previews: `.content`

Note that decorating the above elements will likely require modifying the
templates. You should refer to [the template reference](template.md) for
information on that.

(META when we create our example.html, it needs to have a clear 'text' region.
 Add that to the list when it's here)

### Tiles

Consider adding information to tiles when they're being hovered on. Note that
this will only work for desktop templates.

To achieve that, you will need to overlay content on top of the tile that
is only visible when it's being hovered on.

Example:

Replace the default tile template, and add an overlay on top of it:

```html
<style>.tile:hover>.tile-onhover{visibility: visible;}
    .tile-onhover {width:100%; height:1.5em; top: 0px; background-color: #000;
                   filter: alpha(opacity=40); opacity:0.4; position: absolute;
                   visibility: hidden;}
    .tile-onhover > .price {vertical-align: middle;}
</style>

<script type="text/template" id="product_tile_template">
<div> tile content... </div>

<div class="tile-onhover">
    <div class="price> <%- obj.price %> </div>
</div>
</script>
```

The above example will display the price at the top of the tile when the tile
is under the cursor. Use the above snippet and modify it to your liking, or
create your own way of adding content to tiles.
[The template reference](templates.md) will definitely be handy.

You can add anything to your tile that you think visitors will value. It can be
triggered by hovering, or it can always be visible.

### Previews

As with tiles above, you will likely have to modify templates if you want to
decorate previews. Consider doing the following:

- change the focus of the preview (choices include: image, price, description,
  buy button)
- change the color scheme of the preview
- change the background
- create columns, rows, tables
- customize the "buy" and "find in store" buttons
- [add widgets](widgets.md)

Widgets are an easy way to decorate your previews. They are customized for
SecondFunnel, which makes them easy to add, so give them a look.

Remember that previews are the point at which the conversion is made, so you
want the customer to see enough information and to be encouraged to click on one
of the two action buttons ("buy", "find in store"). Make the buttons visible and
appealing. By making the buttons playful, you will be more likely to get a
reaction

Note: By default, the maximum dimensions for a preview on a desktop screen are
768px * 666px
