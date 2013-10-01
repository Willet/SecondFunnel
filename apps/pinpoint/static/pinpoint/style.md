# Customising the Look of your Page

Make sure you read [the intro](README.md) first.

This tutorial will show you how you can add your styles to a SecondFunnel theme.

## Create a stylesheet

Create a css/ folder, and add a styles.css file in it. Include your styles in
that file

### Elements you might want to style

- tiles: `.tile`
- preview wrappers: `.previewContainer`
- previews: `.content`
(TODO add text, etc.)

## Modify existing styles

Do not take out the stylesheets included in [the example provided](example.md).
If you'd like to change any of the styles it includes, overwrite it in your
stylesheet.

## Change template elements

If you need to change the layout of a template in order to achieve the
appearance you'd like, read the following and refer to
[the template documentation](templates.md).

### Desktop templates

Do not modify the templates in the example.

To create a custom desktop template, copy a non-mobile template, and add
"`store name`_" in front of its name. Modify it to suit your needs. The
modified template will load instead of the default one. Note that the store name
is case-sensitive.

#### Example

(META examples can include

To edit `product_tile_template`:
- copy and paste the `product_tile_template` tag
  ```html
  <script id=product_tile_template> Zoidberg </script>
  ```

- rename it to "`store name`_product_tile_template". So if you work for
  planetexpress, your new template would look something like
  ```html
  <script id=planetexpress_product_tile_template> Zoidberg </script>
  ```

- modify it to suit your needs.
  ```html
  <script id=planetexpress_product_tile_template> No Zoidberg </script>

### Mobile templates

Follow the same procedure as desktop templates; only make sure the template name
contains "mobile_" before tile. i.e. your template name would be one of:

- `store`_`content type`_`data type`_mobile_tile_template
- `content type`_`data type`_mobile_tile_template

#### Example

- copy and paste the `product_mobile_tile_template` tag
  ```html
  <script id=product_mobile_tile_template> Zoidberg </script>
  ```

- rename it to "`store name`_product_mobile_tile_template". So if you work for
  planetexpress, your new template would look something like
  ```html
  <script id=planetexpress_product_mobile_tile_template> Zoidberg </script>
  ```

- modify it to suit your needs.
  ```html
  <script id=planetexpress_product_mobile_tile_template> No Zoidberg </script>
