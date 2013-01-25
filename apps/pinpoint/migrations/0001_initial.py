# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StoreTheme'
        db.create_table('pinpoint_storetheme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('store', self.gf('django.db.models.fields.related.OneToOneField')(related_name='theme', unique=True, to=orm['assets.Store'])),
            ('page_template', self.gf('django.db.models.fields.TextField')(default="\n    <!DOCTYPE HTML>\n    <html>\n        <head>\n            {{ header_content }}\n        </head>\n        <body>\n            <div class='page'>\n                {{ featured_content }}\n                {{ discovery_area }}\n            </div>\n            {{ preview_area }}\n        </body>\n    </html>\n    ")),
            ('featured_product', self.gf('django.db.models.fields.TextField')(default="\n    <img src='{{ product.featured_image }}' />\n    <p>Other images</p>\n    <ul>\n    {% if product.images|length > 1 %}\n        {% for image in product.images %}\n        <li>{{ image }}</li>\n        {% endfor %}\n    {% else %}\n        <li>No other images</li>\n    {% endif %}\n    </ul>\n    <div class='title'>{{ product.name }}</div>\n    <div class='price'>{{ product.price }}</div>\n    <div class='description'>{{ product.description }}</div>\n    <div class='url'>{{ product.url }}</div>\n\n    {% social_buttons product %}\n    ")),
            ('preview_product', self.gf('django.db.models.fields.TextField')(default="\n    <div class='title'></div>\n    <div class='price'></div>\n    <div class='description'></div>\n    <div class='url'></div>\n    <div class='image'></div>\n    <div class='images'></div>\n    <div class='social-buttons'></div>\n    ")),
            ('discovery_product', self.gf('django.db.models.fields.TextField')(default="\n    <img src='{{ product.images.0 }}'/>\n    <div>{{ product.name }}</div>\n    {% social_buttons product %}\n    <div style='display: none'>\n        <!-- Testing -->\n        <div class='price'>{{ product.price }}</div>\n        <div class='description'>{{ product.description }}</div>\n        <div class='url'>{{ product.url }}</div>\n        <ul>\n            {% for image in product.images %}\n            <li>{{ image }}</li>\n            {% endfor %}\n        </ul>\n    </div>\n    ")),
            ('discovery_youtube', self.gf('django.db.models.fields.TextField')(default='\n    {% youtube_video video %}\n    ')),
        ))
        db.send_create_signal('pinpoint', ['StoreTheme'])

        # Adding model 'StoreThemeMedia'
        db.create_table('pinpoint_storethememedia', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('remote', self.gf('django.db.models.fields.CharField')(max_length=555, null=True, blank=True)),
            ('hosted', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('media_type', self.gf('django.db.models.fields.CharField')(default='css', max_length=3, null=True, blank=True)),
            ('theme', self.gf('django.db.models.fields.related.ForeignKey')(related_name='media', to=orm['pinpoint.StoreTheme'])),
        ))
        db.send_create_signal('pinpoint', ['StoreThemeMedia'])

        # Adding model 'BlockType'
        db.create_table('pinpoint_blocktype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('handler', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('pinpoint', ['BlockType'])

        # Adding model 'BlockContent'
        db.create_table('pinpoint_blockcontent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('block_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pinpoint.BlockType'])),
            ('priority', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('pinpoint', ['BlockContent'])

        # Adding model 'Campaign'
        db.create_table('pinpoint_campaign', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('live', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('pinpoint', ['Campaign'])

        # Adding M2M table for field content_blocks on 'Campaign'
        db.create_table('pinpoint_campaign_content_blocks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('campaign', models.ForeignKey(orm['pinpoint.campaign'], null=False)),
            ('blockcontent', models.ForeignKey(orm['pinpoint.blockcontent'], null=False))
        ))
        db.create_unique('pinpoint_campaign_content_blocks', ['campaign_id', 'blockcontent_id'])

        # Adding M2M table for field discovery_blocks on 'Campaign'
        db.create_table('pinpoint_campaign_discovery_blocks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('campaign', models.ForeignKey(orm['pinpoint.campaign'], null=False)),
            ('blockcontent', models.ForeignKey(orm['pinpoint.blockcontent'], null=False))
        ))
        db.create_unique('pinpoint_campaign_discovery_blocks', ['campaign_id', 'blockcontent_id'])

        # Adding model 'FeaturedProductBlock'
        db.create_table('pinpoint_featuredproductblock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Product'])),
            ('existing_image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.ProductMedia'], null=True, blank=True)),
            ('custom_image', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.GenericImage'], unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('pinpoint', ['FeaturedProductBlock'])

        # Adding model 'ShopTheLookBlock'
        db.create_table('pinpoint_shopthelookblock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, null=True, blank=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Product'])),
            ('existing_image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.ProductMedia'], null=True, blank=True)),
            ('custom_image', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.GenericImage'], unique=True, null=True, blank=True)),
            ('existing_ls_image', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ls_image_set', null=True, to=orm['assets.ProductMedia'])),
            ('custom_ls_image', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='ls_image', unique=True, null=True, to=orm['assets.GenericImage'])),
        ))
        db.send_create_signal('pinpoint', ['ShopTheLookBlock'])


    def backwards(self, orm):
        # Deleting model 'StoreTheme'
        db.delete_table('pinpoint_storetheme')

        # Deleting model 'StoreThemeMedia'
        db.delete_table('pinpoint_storethememedia')

        # Deleting model 'BlockType'
        db.delete_table('pinpoint_blocktype')

        # Deleting model 'BlockContent'
        db.delete_table('pinpoint_blockcontent')

        # Deleting model 'Campaign'
        db.delete_table('pinpoint_campaign')

        # Removing M2M table for field content_blocks on 'Campaign'
        db.delete_table('pinpoint_campaign_content_blocks')

        # Removing M2M table for field discovery_blocks on 'Campaign'
        db.delete_table('pinpoint_campaign_discovery_blocks')

        # Deleting model 'FeaturedProductBlock'
        db.delete_table('pinpoint_featuredproductblock')

        # Deleting model 'ShopTheLookBlock'
        db.delete_table('pinpoint_shopthelookblock')


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
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'last_scraped': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'lifestyleImage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['assets.GenericImage']", 'null': 'True', 'blank': 'True'}),
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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'discovery_product': ('django.db.models.fields.TextField', [], {'default': '"\\n    <img src=\'{{ product.images.0 }}\'/>\\n    <div>{{ product.name }}</div>\\n    {% social_buttons product %}\\n    <div style=\'display: none\'>\\n        <!-- Testing -->\\n        <div class=\'price\'>{{ product.price }}</div>\\n        <div class=\'description\'>{{ product.description }}</div>\\n        <div class=\'url\'>{{ product.url }}</div>\\n        <ul>\\n            {% for image in product.images %}\\n            <li>{{ image }}</li>\\n            {% endfor %}\\n        </ul>\\n    </div>\\n    "'}),
            'discovery_youtube': ('django.db.models.fields.TextField', [], {'default': "'\\n    {% youtube_video video %}\\n    '"}),
            'featured_product': ('django.db.models.fields.TextField', [], {'default': '"\\n    <img src=\'{{ product.featured_image }}\' />\\n    <p>Other images</p>\\n    <ul>\\n    {% if product.images|length > 1 %}\\n        {% for image in product.images %}\\n        <li>{{ image }}</li>\\n        {% endfor %}\\n    {% else %}\\n        <li>No other images</li>\\n    {% endif %}\\n    </ul>\\n    <div class=\'title\'>{{ product.name }}</div>\\n    <div class=\'price\'>{{ product.price }}</div>\\n    <div class=\'description\'>{{ product.description }}</div>\\n    <div class=\'url\'>{{ product.url }}</div>\\n\\n    {% social_buttons product %}\\n    "'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page_template': ('django.db.models.fields.TextField', [], {'default': '"\\n    <!DOCTYPE HTML>\\n    <html>\\n        <head>\\n            {{ header_content }}\\n        </head>\\n        <body>\\n            <div class=\'page\'>\\n                {{ featured_content }}\\n                {{ discovery_area }}\\n            </div>\\n            {{ preview_area }}\\n        </body>\\n    </html>\\n    "'}),
            'preview_product': ('django.db.models.fields.TextField', [], {'default': '"\\n    <div class=\'title\'></div>\\n    <div class=\'price\'></div>\\n    <div class=\'description\'></div>\\n    <div class=\'url\'></div>\\n    <div class=\'image\'></div>\\n    <div class=\'images\'></div>\\n    <div class=\'social-buttons\'></div>\\n    "'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'theme'", 'unique': 'True', 'to': "orm['assets.Store']"})
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