# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'StoreTheme.discovery_youtube'
        db.delete_column('pinpoint_storetheme', 'discovery_youtube')

        # Deleting field 'StoreTheme.preview_product'
        db.delete_column('pinpoint_storetheme', 'preview_product')

        # Deleting field 'StoreTheme.page_template'
        db.delete_column('pinpoint_storetheme', 'page_template')

        # Deleting field 'StoreTheme.discovery_product'
        db.delete_column('pinpoint_storetheme', 'discovery_product')

        # Adding field 'StoreTheme.page'
        db.add_column('pinpoint_storetheme', 'page',
                      self.gf('django.db.models.fields.TextField')(default='\n    <!DOCTYPE HTML>\n    <html>\n        <head>\n            {{ header_content }}\n        </head>\n        <body>\n            {{ js_templates }}\n            {{ body_content }}\n        </body>\n    </html>\n    '),
                      keep_default=False)

        # Adding field 'StoreTheme.shop_the_look'
        db.add_column('pinpoint_storetheme', 'shop_the_look',
                      self.gf('django.db.models.fields.TextField')(default="\n    <script type='text/template' data-template-id='shop-the-look'>\n    </script>\n    "),
                      keep_default=False)

        # Adding field 'StoreTheme.product'
        db.add_column('pinpoint_storetheme', 'product',
                      self.gf('django.db.models.fields.TextField')(default="\n    <script type='text/template' data-template-id='product'>\n    </script>\n    "),
                      keep_default=False)

        # Adding field 'StoreTheme.combobox'
        db.add_column('pinpoint_storetheme', 'combobox',
                      self.gf('django.db.models.fields.TextField')(default="\n    <script type='text/template' data-template-id='combobox'>\n    </script>\n    "),
                      keep_default=False)

        # Adding field 'StoreTheme.youtube'
        db.add_column('pinpoint_storetheme', 'youtube',
                      self.gf('django.db.models.fields.TextField')(default="\n    <script type='text/template' data-template-id='youtube'>\n    </script>\n    "),
                      keep_default=False)

        # Adding field 'StoreTheme.preview'
        db.add_column('pinpoint_storetheme', 'preview',
                      self.gf('django.db.models.fields.TextField')(default="\n    <script type='text/template' data-template-id='preview'>\n    </script>\n    "),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'StoreTheme.discovery_youtube'
        db.add_column('pinpoint_storetheme', 'discovery_youtube',
                      self.gf('django.db.models.fields.TextField')(default='\n    {% youtube_video video %}\n    '),
                      keep_default=False)

        # Adding field 'StoreTheme.preview_product'
        db.add_column('pinpoint_storetheme', 'preview_product',
                      self.gf('django.db.models.fields.TextField')(default="\n    <div class='title'></div>\n    <div class='price'></div>\n    <div class='description'></div>\n    <div class='url'></div>\n    <div class='image'></div>\n    <div class='images'></div>\n    <div class='social-buttons'></div>\n    "),
                      keep_default=False)

        # Adding field 'StoreTheme.page_template'
        db.add_column('pinpoint_storetheme', 'page_template',
                      self.gf('django.db.models.fields.TextField')(default="\n    <!DOCTYPE HTML>\n    <html>\n        <head>\n            {{ header_content }}\n        </head>\n        <body>\n            <div class='page'>\n                {{ featured_content }}\n                {{ discovery_area }}\n            </div>\n            {{ preview_area }}\n        </body>\n    </html>\n    "),
                      keep_default=False)

        # Adding field 'StoreTheme.discovery_product'
        db.add_column('pinpoint_storetheme', 'discovery_product',
                      self.gf('django.db.models.fields.TextField')(default="\n    <img src='{{ product.images.0 }}'/>\n    <div>{{ product.name }}</div>\n    {% social_buttons product %}\n    <div style='display: none'>\n        <!-- Testing -->\n        <div class='price'>{{ product.price }}</div>\n        <div class='description'>{{ product.description }}</div>\n        <div class='url'>{{ product.url }}</div>\n        <ul>\n            {% for image in product.images %}\n            <li>{{ image }}</li>\n            {% endfor %}\n        </ul>\n    </div>\n    "),
                      keep_default=False)

        # Deleting field 'StoreTheme.page'
        db.delete_column('pinpoint_storetheme', 'page')

        # Deleting field 'StoreTheme.shop_the_look'
        db.delete_column('pinpoint_storetheme', 'shop_the_look')

        # Deleting field 'StoreTheme.product'
        db.delete_column('pinpoint_storetheme', 'product')

        # Deleting field 'StoreTheme.combobox'
        db.delete_column('pinpoint_storetheme', 'combobox')

        # Deleting field 'StoreTheme.youtube'
        db.delete_column('pinpoint_storetheme', 'youtube')

        # Deleting field 'StoreTheme.preview'
        db.delete_column('pinpoint_storetheme', 'preview')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'live': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
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
            'combobox': ('django.db.models.fields.TextField', [], {'default': '"\\n    <script type=\'text/template\' data-template-id=\'combobox\'>\\n    </script>\\n    "'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'featured_product': ('django.db.models.fields.TextField', [], {'default': '"\\n    <script type=\'text/template\' data-template-id=\'featured-product\'>\\n    </script>\\n    "'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.TextField', [], {'default': "'\\n    <!DOCTYPE HTML>\\n    <html>\\n        <head>\\n            {{ header_content }}\\n        </head>\\n        <body>\\n            {{ js_templates }}\\n            {{ body_content }}\\n        </body>\\n    </html>\\n    '"}),
            'preview': ('django.db.models.fields.TextField', [], {'default': '"\\n    <script type=\'text/template\' data-template-id=\'preview\'>\\n    </script>\\n    "'}),
            'product': ('django.db.models.fields.TextField', [], {'default': '"\\n    <script type=\'text/template\' data-template-id=\'product\'>\\n    </script>\\n    "'}),
            'shop_the_look': ('django.db.models.fields.TextField', [], {'default': '"\\n    <script type=\'text/template\' data-template-id=\'shop-the-look\'>\\n    </script>\\n    "'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'theme'", 'unique': 'True', 'to': "orm['assets.Store']"}),
            'youtube': ('django.db.models.fields.TextField', [], {'default': '"\\n    <script type=\'text/template\' data-template-id=\'youtube\'>\\n    </script>\\n    "'})
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
        }
    }

    complete_apps = ['pinpoint']