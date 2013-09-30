# Changing the Style

## pages2.css

pages2.css is not meant to be modified. If there is anything you want to change
that's in pages2.css, you have to overwrite it.

## The right way to customize your page

To change your page's style, create a styles.css file, and file, and add your
styles into that file.

### Elements you might want to style

- `body`
- `.tile` tiles
- `.previewContainer` previews
- `.social-buttons` social buttons (maybe not)
- `.sharing` __not sure__
- `.previewContainer .price`

## Changing Template Elements

### Desktop templates

Do not modify the templates in the example.

To create a custom desktop template, copy a non-mobile template, and add
"`store name`_" in front of its name. Modify it to suit your needs. The
modified template will load instead of the default one. Note that the store name
is case-sensitive.

#### Illustration

- to edit `product_tile_template`, copy and paste the `product_tile_template`
tag, and rename it to "`store name`_product_tile_template".
- To edit `image_preview_template`, copy and paste the `image_preview_template`
tag, and rename it to "`store name`_image_preview_template".

### Mobile templates

Follow the same procedure as desktop templates; only make sure the template name
contains "mobile_" before tile. i.e. your template name would be one of:

- `store`_`content type`_`data type`_mobile_tile_template
- `content type`_`data type`_mobile_tile_template