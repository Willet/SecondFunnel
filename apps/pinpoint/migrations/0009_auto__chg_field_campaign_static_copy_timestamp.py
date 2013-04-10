# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Campaign.static_copy_timestamp'
        db.alter_column('pinpoint_campaign', 'static_copy_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Campaign.static_copy_timestamp'
        raise RuntimeError("Cannot reverse this migration. 'Campaign.static_copy_timestamp' and its values cannot be restored.")

    models = {
        'assets.genericimage': {
            'Meta': {'object_name': 'GenericImage'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hosted': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'remote': ('django.db.models.fields.CharField', [], {'max_length': '555', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'assets.product': {
            'Meta': {'object_name': 'Product'},
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'default_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_product'", 'null': 'True', 'to': "orm['assets.ProductMedia']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'last_scraped': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'lifestyleImages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'associated_products'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['assets.GenericImage']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'original_url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'rescrape': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.Store']", 'null': 'True', 'blank': 'True'})
        },
        'assets.productmedia': {
            'Meta': {'object_name': 'ProductMedia'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hosted': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'media'", 'to': "orm['assets.Product']"}),
            'remote': ('django.db.models.fields.CharField', [], {'max_length': '555', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'assets.store': {
            'Meta': {'object_name': 'Store'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'social_auth': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['social_auth.UserSocialAuth']", 'null': 'True', 'blank': 'True'}),
            'staff': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pinpoint.blockcontent': {
            'Meta': {'object_name': 'BlockContent'},
            'block_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pinpoint.BlockType']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'priority': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'pinpoint.blocktype': {
            'Meta': {'object_name': 'BlockType'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'handler': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'pinpoint.campaign': {
            'Meta': {'object_name': 'Campaign'},
            'content_blocks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'content_campaign'", 'symmetrical': 'False', 'to': "orm['pinpoint.BlockContent']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'discovery_blocks': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'discovery_campaign'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['pinpoint.BlockContent']"}),
            'has_static_copy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'live': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'static_copy_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.Store']"})
        },
        'pinpoint.featuredproductblock': {
            'Meta': {'object_name': 'FeaturedProductBlock'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'custom_image': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['assets.GenericImage']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'existing_image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.ProductMedia']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.Product']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'pinpoint.shopthelookblock': {
            'Meta': {'object_name': 'ShopTheLookBlock'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'custom_image': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['assets.GenericImage']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'custom_ls_image': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'ls_image'", 'unique': 'True', 'null': 'True', 'to': "orm['assets.GenericImage']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'existing_image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.ProductMedia']", 'null': 'True', 'blank': 'True'}),
            'existing_ls_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ls_image_set'", 'null': 'True', 'to': "orm['assets.ProductMedia']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.Product']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'pinpoint.storetheme': {
            'Meta': {'object_name': 'StoreTheme'},
            'combobox': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'combobox\\\'>\\n    <div class=\\\'block product\\\'>\\n        <img src=\\\'<%= data["lifestyle-image"] %>\\\'/>\\n        <div><%= data.title %></div>\\n        <div><%= data.description %></div>\\n        <img src=\\\'<%= data.image %>\\\'/>\\n        <div><%= data.url %></div>\\n        <% _.each(page.product.images, function(image){ %>\\n        <img src=\\\'<%= image %>\\\'/>\\n        <% }); %>\\n    </div>\\n</script>\\n    \''}),
            'combobox_preview': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'combobox-preview\\\'>\\n    <div class=\\\'image\\\'><img src=\\\'<%= data.image %>\\\' /></div>\\n    <div class=\\\'images\\\'>\\n        <% _.each(data.images, function(image) { %>\\n        <img src=\\\'<%= image %>\\\' />\\n        <% }); %>\\n    </div>\\n    <div class=\\\'price\\\'><%= data.price %></div>\\n    <div class=\\\'title\\\'><%= data.title %></div>\\n    <div class=\\\'description\\\'><%= data.description %></div>\\n    <div class=\\\'url\\\'><a href=\\\'<%= data.url %>\\\' target="_blank">BUY\\n        NOW</a></div>\\n    <% include social_buttons %>\\n    </div>\\n</script>\\n    \''}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'featured_product': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'featured-product\\\'>\\n    <img src=\\\'<%= page["featured-image"] %>\\\' />\\n    <div><%= page.product.title %></b></div>\\n    <div><%= page.product.price %></div>\\n    <div><%= page.product.description %></div>\\n    <div>\\n    <% _.each(page.product.images, function(image){ %>\\n        <img src=\\\'<%= image %>\\\'/>\\n    <% }); %>\\n    </div>\\n    <div>\\n        <% include social_buttons %>\\n    </div>\\n    <div>\\n        <a href=\\\'<%= page.product.url %>\\\' target=\\\'_blank\\\'>link</a>\\n    </div>\\n</script>\\n    \''}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instagram': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'instagram\\\'\\n        data-appearance-probability=\\\'0.25\\\'>\\n    <div class=\\\'block image external-content instagram\\\'>\\n        <div class=\\\'product\\\'>\\n            <div class=\\\'img-container\\\'>\\n                <img src=\\\'<%= sizeImage(data.image, "master") %>\\\'\\n                     alt=\\\'Instagram image\\\'\\n                     data-original-id=\\\'<%= data["original-id"] %>\\\' />\\n            </div>\\n        </div>\\n    </div>\\n</script>\\n    \''}),
            'instagram_preview': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'instagram-preview\\\'>\\n    <img src=\\\'<%= data["image"] %>\\\'/>\\n</script>\\n    \''}),
            'instagram_product_preview': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'instagram-product-preview\\\'>\\n    <img src=\\\'<%= data["image"] %>\\\'/>\\n</script>\\n    \''}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.TextField', [], {'default': '\'\\n<!DOCTYPE HTML>\\n<html>\\n    <head>\\n        <!--\\n        This statement is required; it loads any content needed for the\\n        head, and must be located in the <head> tag\\n        -->\\n        {{ header_content }}\\n\\n    </head>\\n    <body>\\n        <!--This div will load the \\\'shop-the-look\\\' template-->\\n        <div class="template target featured product" data-src="shop-the-look"></div>\\n\\n        <!--This div will load the \\\'featured-product\\\' template-->\\n        <div class="template target featured product" data-src="featured-product"></div>\\n\\n        <div class=\\\'divider\\\'>\\n            <div class=\\\'bar\\\'></div>\\n            <span class=\\\'text\\\'>Browse more</span>\\n        </div>\\n        <div class=\\\'discovery-area\\\'></div>\\n\\n        <!--\\n        This statement ensures that templates are available,\\n        and should come before {{body_content}}\\n        -->\\n        {{ js_templates }}\\n\\n        <!--\\n        This statement loads any scripts that may be required. If you want to\\n        include your own javascript, include them after this statement\\n        -->\\n        {{ body_content }}\\n    </body>\\n</html>\\n    \''}),
            'product': ('django.db.models.fields.TextField', [], {'default': '"\\n<script type=\'text/template\' data-template-id=\'product\'>\\n    <div class=\'block product\'>\\n        <div><%= data.title %></div>\\n        <div><%= data.description %></div>\\n        <img src=\'<%= data.image %>\'/>\\n        <div><%= data.url %></div>\\n        <% _.each(page.product.images, function(image){ %>\\n        <img src=\'<%= image %>\'/>\\n        <% }); %>\\n    </div>\\n</script>\\n    "'}),
            'product_preview': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'product-preview\\\'>\\n    <div class=\\\'image\\\'><img src=\\\'<%= data.image %>\\\' /></div>\\n    <div class=\\\'images\\\'>\\n        <% _.each(data.images, function(image) { %>\\n        <img src=\\\'<%= image %>\\\' />\\n        <% }); %>\\n    </div>\\n    <div class=\\\'price\\\'><%= data.price %></div>\\n    <div class=\\\'title\\\'><%= data.title %></div>\\n    <div class=\\\'description\\\'><%= data.description %></div>\\n    <div class=\\\'url\\\'><a href=\\\'<%= data.url %>\\\' target="_blank">BUY\\n        NOW</a></div>\\n    <% include social_buttons %>\\n    </div>\\n</script>\\n    \''}),
            'shop_the_look': ('django.db.models.fields.TextField', [], {'default': '\'\\n<script type=\\\'text/template\\\' data-template-id=\\\'shop-the-look\\\'>\\n    <img src=\\\'<%= page["stl-image"] %>\\\' />\\n    <img src=\\\'<%= page["featured-image"] %>\\\' />\\n    <div><%= page.product.title %></b></div>\\n    <div><%= page.product.price %></div>\\n    <div><%= page.product.description %></div>\\n    <div>\\n    <% _.each(page.product.images, function(image){ %>\\n        <img src=\\\'<%= image %>\\\'/>\\n    <% }); %>\\n    </div>\\n    <div>\\n        <% include social_buttons %>\\n    </div>\\n    <div>\\n        <a href=\\\'<%= page.product.url %>\\\' target=\\\'_blank\\\'>link</a>\\n    </div>\\n</script>\\n    \''}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'theme'", 'unique': 'True', 'to': "orm['assets.Store']"}),
            'youtube': ('django.db.models.fields.TextField', [], {'default': '"\\n<script type=\'text/template\' data-template-id=\'youtube\'>\\n    <% include youtube_video_template %>\\n</script>\\n    "'})
        },
        'pinpoint.storethememedia': {
            'Meta': {'object_name': 'StoreThemeMedia'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hosted': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'media_type': ('django.db.models.fields.CharField', [], {'default': "'css'", 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'remote': ('django.db.models.fields.CharField', [], {'max_length': '555', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'media'", 'to': "orm['pinpoint.StoreTheme']"})
        },
        'social_auth.usersocialauth': {
            'Meta': {'unique_together': "(('provider', 'uid'),)", 'object_name': 'UserSocialAuth'},
            'extra_data': ('social_auth.fields.JSONField', [], {'default': "'{}'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'social_auth'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['pinpoint']