# Using Templates with SecondFunnel: Reference

SecondFunnel uses templates for an array of things. Of interest to you are
previews and tiles, both of which will be covered by this document.

## Template names

In SecondFunnel, template names follow a convention. The name of your template
will decide how specific it is.

### Tiles

In order of decreasing specificity, here are the patterns for tile names:

- `store`_`content type`_`data type`_mobile_tile_template
- `content type`_`data type`_mobile_tile_template
- `store`_`data type`_mobile_tile_template
- `data type`_mobile_tile_template
- `store`_`content type`_image_tile_template
- `content type`_`data type`_tile_template
- `store`_`data type`_tile_template
- `data type`_tile_template

### Previews

In order of decreasing specificity, here are the patterns for preview names:
- `store`_`content type`_mobile_preview_template
- `content type`_mobile_preview_template
- `store`_`content type`_preview_template
- `content type`preview_template
- product_mobile_preview_template
- product_preview_template
- tile_mobile_preview_template
- tile_preview_template

## Template contents

Everything in your template will follow standard HTML and CSS rules, but you
also have access to variables related to the campaign.

**Template variables** can be included using this notation:

    `<%- variable_name %>`

For example, assuming the template was passed in a variable called `foo` with a
value of `bar`:

    `<div><%- foo %></div>`

When the page is loaded, it becomes:

```html
<div>bar</div>
```

**Note:** this method is HTML-escaped. If you want your data as-is, use
`<%= variable_name %>` instead.

All product templates have access to a product object called `obj`. That object
includes the following variables:

- title
- price
- images
- related-products
- caption
- url
- image
- original-url
- original-id
- likes
- template
- content-type
- categories
- dominant-color
- type

All templates can be identified by their `id` attribute, and will
always look like this:

```html
<script type='text/template' id='template_name'></script>
```

If you want mobile devices to use a different template, Add a mobile template,
which would have a similar name, except for `_mobile_` inserted before either
`tile` or `preview`

```html
<script type='text/template' id='product_preview_template'></script>
<script type='text/template' id='product_mobile_preview_template'></script>

<script type='text/template' id='product_tile_template'></script>
<script type='text/template' id='product_mobile_tile_template'></script>
```

Putting it all together, a template might look like this:

```
<script type='text/template' id='storeName_preview_template'>
    <div class="preview">
        <img class="image" src='<%- obj.image %>' />
        <div class="product">
            <div class="title"><%- obj.title %></div>
            <div class="price"><%- obj.price %></div>
            <div class="desc"><%- obj.description %></div>
            <div class="shop-button">
                <a href='<%= obj.url %>' target='_blank'>link</a>
            </div>
        </div>
    </div>
</script>


<script type='text/template' id='storeName_mobile_preview_template'>
    mobile template (optional)
</script>
```

... and be supplied variables like this...

```javascript
{
    'obj': {
        'image': 'http://example.com/image.jpg'
        'title': 'My Awesome Product',
        'price': '$1 billion USD',
        'description': 'Description? We don\'t need no steenking description!',
        'url': 'http://example.com/my-awesome-product'
    },
}
```

... and it will show up on the page like this:

```html
<div class="preview">
    <img class="image" src='http://example.com/image.jpg' />
    <div class="product">
        <div class="title">My Awesome Product</div>
        <div class="price">$1 billion USD</div>
        <div class="desc">Description? We don\'t need no steenking description!</div>
        <div class="shop-button">
            <a href='http://example.com/my-awesome-product' target='_blank'>link</a>
        </div>
    </div>
</div>
```


## JavaScript in templates

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

