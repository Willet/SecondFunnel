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

    `<%= variable_name %>`

For example, assuming the template was passed in a variable called `foo` with a
value of `bar`:

    `<div><%= foo %></div>`

When the page is loaded, it becomes:

```html
<div>bar</div>
```

**Note:** this method is a little dangerous as it can insert HTML. If you want your data as-is, use `<%= variable_name %>` instead. It's recommended you use `<%-` unless you have to use `<%=`. (You will need to use in URLs as you do not want to modify the URL string.)

All product templates have access to a product object called `obj`. That object
includes the following variables:

- title
- price
- image
- images
- related-products
- caption
- url
- original-url
- original-id
- likes
- template
- content-type
- categories
- dominant-color
- type

All templates can be identified by their `id` attributes, and will
always look like this:

```html
<script type='text/template' id='template_name'></script>
```

Mobile devices use different templates than PCs. Mobile templates have similar
names except for `_mobile_` inserted before either `tile` or `preview`.

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
        <img class="image" src='<%= obj.image %>' />
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
    Mobile template. You don't have to replace both desktop and mobile; you
    can replace only one.
</script>
```

... and be supplied variables like this...

```javascript
{
    'obj': {
        'image': 'http://example.com/image.jpg'
        'title': 'My Awesome Product',
        'price': '$1 billion USD',
        'description': 'Description? We don't need no steenking description!',
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
## Replacing templates

### Desktop templates

To create a custom desktop template, copy a non-mobile template, and add
"`store name`_" in front of its name. Modify it to suit your needs. The
modified template will load instead of the default one. Note that the store name
is case-sensitive.

#### Example

(META examples can include variables, JS, fancier stuff. Should they?)

To edit `product_tile_template`:
- copy and paste the `product_tile_template` tag
  ```html
  <script id="product_tile_template"> Zoidberg </script>
  ```

- rename it to "`store name`_product_tile_template". So if you work for
  planetexpress, your new template would look something like
  ```html
  <script id="planetexpress_product_tile_template"> Zoidberg </script>
  ```

- modify it to suit your needs.
  ```html
  <script id="planetexpress_product_tile_template"> No Zoidberg </script>
  ```

### Mobile templates

Follow the same procedure as desktop templates; only make sure the template name
contains "mobile_" before tile. i.e. your template name would be one of:

- `store`_`content type`_`data type`_mobile_tile_template
- `content type`_`data type`_mobile_tile_template

#### Example

- copy and paste the `product_mobile_tile_template` tag
  ```html
  <script id="product_mobile_tile_template"> Zoidberg </script>
  ```

- rename it to "`store name`_product_mobile_tile_template". So if you work for
  planetexpress, your new template would look something like
  ```html
  <script id="planetexpress_product_mobile_tile_template"> Zoidberg </script>
  ```

- modify it to suit your needs.
  ```html
  <script id="planetexpress_product_mobile_tile_template"> No Zoidberg </script>
  ```
## JavaScript in templates

You can insert JavaScript code between &lt;% and %&gt; tags that will execute at
that stage when the template is loading. A nifty and simple trick you can use is
`for` loops. For example, to iterate over the images of a product, you can
insert this following snippet into your template:

```
<script type="text/template" id="iterate_over_images">
    <%  for(i in obj.images) { %>
            <img src="<%= i %>" />
    <%  } %>
</script>
```

Another trick you can use in your template is checking whether a field exists.
You can do that using the `if` keyword. For instance, the following snippet
will only include the field `obj.designer` if it exists.

```

<% if (obj.designer) { %>
	<%- obj.designer %>
<% } %>
```

