# Creating a SecondFunnel Theme: Tutorial

SecondFunnel landing pages are beautiful image palettes that try to get the user
to interact.

This tutorial will give you an overview of SecondFunnel pages and show you how
you can create a theme for your page.

## You will need

To create a new theme, you will need

- a web browser
- a text editor
- basic knowledge of **HTML**, **CSS**, and **JavaScript**
- [our example](example.html)
- this tutorial

## Step One: download the example, look around

Use the example linked above as the base for your theme. You will modify it and
add styles until you're happy with it.

Take a look at example.html. Scroll, click around, click around some more.

Notice that the landing page has two main components:

- tiles: images that give visitors an idea about the products
- previews: modal dialogs that contain details about the products

The region where the tiles are displayed is called the **discovery feed**.

## Step Two: Look at the example source

Use your editor to look at the source for example.html. Notice the body contains
three main parts:

- visible elements: your visitors will see this
- templates: SecondFunnel uses templates to add tiles and previews to the page. Look
  for the comment that says "Templates" to find this part.
- JavaScript: The scripts SecondFunnel needs to run.

Take a quick look at the default stylesheet included in the example. If you
would like to disable or modify any of the styles there, you will have to
override them. (Instructions in the next step.)

## Step Three: modify the example

### 1. Modify the HTML and CSS

Add a css/ directory, and inside it create styles.css. Include your styles in
this file. You can override any of the default styles here. If the default style
is still being loaded after you tried overriding, consider adding "!important"
at the end of your style, but use it sparingly.

Modify the elements in the example as you please; however, ensure everything
SecondFunnel requires stays on the page. SecondFunnel requires the following:

- at least minimal templates
- the discovery feed `<div id="discovery-area></div>`
- the stylesheets included in the example.
- the scripts included in the example.

There are many things you can change about your page to make it represent your
brand. Here are a few things to start off with:

- add a header that identifies your brand
- add buttons that send users to your social media pages
- change the color scheme
- add banners (make sure they're not distracting)

Now you have a landing page that makes visitors think of your brand. The next
thing to do is customize tiles and previews.

### 2. Add your JavaScript files

If you would like to add JavaScript to your landing page, put the source files
in a js/ folder, and add `script` tags in the JavaScript part (located at the
end of `body`).

### 3. Add your templates

If you have worked with Underscore templates before, this will be a refresher
for you. If you've never worked with Underscore templates before, not to worry,
we have enough material to get you started.

#### What are templates?

In SecondFunnel, templates are associated with products. When a viewer loads
your landing page, they see tiles added to the discovery feed. Each of these
tiles represents a product, and each of these tiles was created using a
template. When a user clicks on a tile, a preview is loaded. That preview is
created using a template.

Templates can be thought of as relationships between products and elements
on the page.

`product` -&gt; `tile template` -&gt; `tile`
`product` -&gt; `preview template` -&gt; `preview`

#### Getting familiar with SecondFunnel templates

The first thing you should do is take a look at the different templates we have.
Some of them are tile templates; others are preview templates. You can tell
which category a template belongs to by looking at its name. A template's name
is stored in its `id` attribute.

For example, the following template is named `product_tile_template`, so it's
a tile template.

```html
<script type="text/template" id="product_tile_template"> </script>
```

Note that templates are added using the `<script type="text/template>` tag.

Also note that the above template contains does not contain anything between its
opening and closing tag, so if it's ever used, it will insert a blank.

A preview template would have `preview` somewhere in its name. Example:

```html
<script type="text/template" id="product_preview_template"> </script>
```

#### Replacing templates

You should **never delete any of the default templates**. If you want to replace
the default templates, simply copy the template, and add `<yourStoreName>_` in
in front of the template name.

Let's say you want to replace the above templates. You would copy and paste
them then modify their names so they look something like:

```html
<script type="text/template" id="storeName_product_tile_template"> </script>
<script type="text/template" id="storeName_product_preview_template"> </script>
```

Now when someone visits your site, your templates will be used instead of the
default ones.

Note that there are also **mobile templates**. The same rules apply to those.
They are used if a visitor is using a mobile device to view your page. If you
want to replace them, follow the same procedure outlined above.

#### Adding variables, scripts

Templates are useful because they allow you to insert new items into the page
after it's loaded. In SecondFunnel, since templates are associated with
products, every template has access to an object called `obj`. This object will
give you access to different fields related to the product. The following fields
are supported by all campaigns:

- title
- price
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
- images

So if we were to modify the above templates and make it meaningful, we can have:

```
<script type="text/template" id="storeName_product_tile_template">
    <%= obj.image %>
</script>

<script type="text/template" id="storeName_product_preview_template">
    <div class="title"> <%= obj.title %> </div>
    <div class="image"> <img src="<%= obj.image %>" /> </div>
    <div class="price"> <%= obj.price %> </div>
    <div class="url"> <a href="<%= obj.url %>"> buy </a> </div>
</script>
```

Now our tile will include an image, and our preview will include a title, an
image, and a price.

Note that variables are added between `<%=` and `%>`.

(META should we mention `<%-` or would that be information overload?)

We have more material to guide you in creating beautiful templates at the end of
this tutorial. Visit them when you are done reading.

P.S. SecondFunnel widgets would can make great additions to previews. They are
customized to be easy to insert into a preview. Make sure you take a look when
you're done reading this tutorial. (link at the end)

## Step Five: Upload your modified landing page

(TODO add uploading instructions)

## Further reading

The following are references that will help you create a landing page that will
impress your visitors:

- [Customizing the Look of Your Page](style.md)
- [Using templates with SecondFunnel](templates.md)
- [Adding Widgets to Your Page](widgets.md)