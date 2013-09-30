Detailed documentation will go here

## Templates

### Template names

In SecondFunnel, template names follow a convention. The name of your template
will decide how specific it is. In order of decreasing specificity, the rules
for naming templates are:

(META these are tile templates. Make sure conventions apply everywhere.)
(TODO talk about them, finish. Add other templates if warranted)
(TODO move to technical)

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

**Template variables** can be included using this notation:

    `<%- variable_name %>`

For example, assuming the template was passed in a variable called `foo` with a
value of `bar`:

```<div><%= foo %></div>```

When the page is loaded, it becomes:

```html
<div>bar</div>
```

Every template has access to certain variables:

- **page**: Information about the page
- **store**: Information about the store

The following fields are available to most campaigns:

Useful:
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

Pretty useless:
- tile-id
- content-id
- username
- related-products
- db-id
- user-image

All templates can be identified by their `data-template-id` attribute, and will always look like this:

    <script type='text/template' data-template-id='template_name'></script>

If you want mobile devices to use a different template, add a new tag below it, so it looks like this:

    <script type='text/template' data-template-id='template_name'></script>
    <script type='text/template' data-template-id='template_name' data-media='mobile'></script>

Putting it all together, a template might look like this:

```
<script type='text/template' data-template-id='shop-the-look'>
    <div class="shop-the-look">
        <img class="look-image" src='<%= page["stl-image"] %>' />
        <img class="prod-image" src='<%= page["featured-image"] %>' />
        <div class="product">
            <div class="title"><%= page.product.title %></div>
            <div class="price"><%= page.product.price %></div>
            <div class="desc"><%= page.product.description %></div>
            <div class="shop-button">
                <a href='<%= page.product.url %>' target='_blank'>link</a>
            </div>
        </div>
    </div>
</script>


<script type='text/template' data-template-id='shop-the-look'
                             data-media='mobile'>
    mobile template (optional)
</script>
```

... and be supplied variables like this...

```json
{
    'page': {
        'featured-image': 'http://example.com/image2.jpg'
        'stl-image': 'http://example.com/image.jpg'
        'product': {
            'title': 'My Awesome Product',
            'price': '$1 billion USD',
            'description': 'Description? We don\'t need no steenking description!',
            'url': 'http://example.com/my-awesome-product'
        }
    },
}
```

... and it will show up on the page like this:

```html
<div class="shop-the-look">
    <img class="look-image" src='http://example.com/image.jpg' />
    <img class="prod-image" src='http://example.com/image2.jpg' />
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


### JavaScript in templates

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

### Template style

There are many types of tiles available to you, all of which are suffixed with
`_template` in `index.html`.

To change the appearance of any template, *do not edit them*. Copy and paste
the template with a new id, with your company name prefixed. For example,

* to edit `product_tile_template`, copy and paste the `product_tile_template`
tag, and rename it to `yourStoreName_product_tile_template`.
* To edit `image_preview_template`, copy and paste the `image_preview_template`
tag, and rename it to `yourStoreName_image_preview_template`.

Your store name is case-sensitive.

### Create a template just for mobile devices

If `pages.js` thinks it is being viewed from a mobile device, it prefers
`abc_xyz_mobile_template` to `abc_xyz_template`. To override a desktop
template, create its mobile counterpart with a `_mobile` ID.

