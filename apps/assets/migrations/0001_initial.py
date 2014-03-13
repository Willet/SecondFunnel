# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Store'
        db.create_table(u'assets_store', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_theme', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='store', null=True, to=orm['assets.Theme'])),
            ('public_base_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'assets', ['Store'])

        # Adding M2M table for field staff on 'Store'
        m2m_table_name = db.shorten_name(u'assets_store_staff')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('store', models.ForeignKey(orm[u'assets.store'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['store_id', 'user_id'])

        # Adding model 'Product'
        db.create_table(u'assets_product', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('details', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('sku', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('price', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('default_image', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='default_image', null=True, to=orm['assets.ProductImage'])),
            ('last_scraped_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('attributes', self.gf('jsonfield.fields.JSONField')(null=True)),
        ))
        db.send_create_signal(u'assets', ['Product'])

        # Adding model 'ProductImage'
        db.create_table(u'assets_productimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='product_images', to=orm['assets.Product'])),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('original_url', self.gf('django.db.models.fields.TextField')()),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('dominant_color', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('attributes', self.gf('jsonfield.fields.JSONField')(default={}, null=True, blank=True)),
        ))
        db.send_create_signal(u'assets', ['ProductImage'])

        # Adding model 'Content'
        db.create_table(u'assets_content', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('source_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('attributes', self.gf('jsonfield.fields.JSONField')(null=True)),
        ))
        db.send_create_signal(u'assets', ['Content'])

        # Adding M2M table for field tagged_products on 'Content'
        m2m_table_name = db.shorten_name(u'assets_content_tagged_products')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('content', models.ForeignKey(orm[u'assets.content'], null=False)),
            ('product', models.ForeignKey(orm[u'assets.product'], null=False))
        ))
        db.create_unique(m2m_table_name, ['content_id', 'product_id'])

        # Adding model 'Image'
        db.create_table(u'assets_image', (
            (u'content_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Content'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('original_url', self.gf('django.db.models.fields.TextField')()),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('dominant_color', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
        ))
        db.send_create_signal(u'assets', ['Image'])

        # Adding model 'Video'
        db.create_table(u'assets_video', (
            (u'content_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Content'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('caption', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('player', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('original_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'assets', ['Video'])

        # Adding model 'Review'
        db.create_table(u'assets_review', (
            (u'content_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Content'], unique=True, primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Product'])),
            ('body', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'assets', ['Review'])

        # Adding model 'Theme'
        db.create_table(u'assets_theme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('template', self.gf('django.db.models.fields.CharField')(default='apps/pinpoint/templates/pinpoint/campaign_base.html', max_length=1024)),
        ))
        db.send_create_signal(u'assets', ['Theme'])

        # Adding model 'Feed'
        db.create_table(u'assets_feed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('feed_algorithm', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal(u'assets', ['Feed'])

        # Adding model 'Page'
        db.create_table(u'assets_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('theme', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='page', null=True, to=orm['assets.Theme'])),
            ('theme_settings', self.gf('jsonfield.fields.JSONField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('url_slug', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('legal_copy', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('last_published_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Feed'])),
        ))
        db.send_create_signal(u'assets', ['Page'])

        # Adding model 'Tile'
        db.create_table(u'assets_tile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('starting_score', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('clicks', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tiles', to=orm['assets.Feed'])),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('prioritized', self.gf('django.db.models.fields.BooleanField')()),
            ('attributes', self.gf('jsonfield.fields.JSONField')(default={}, null=True)),
        ))
        db.send_create_signal(u'assets', ['Tile'])

        # Adding M2M table for field products on 'Tile'
        m2m_table_name = db.shorten_name(u'assets_tile_products')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tile', models.ForeignKey(orm[u'assets.tile'], null=False)),
            ('product', models.ForeignKey(orm[u'assets.product'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tile_id', 'product_id'])

        # Adding M2M table for field content on 'Tile'
        m2m_table_name = db.shorten_name(u'assets_tile_content')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tile', models.ForeignKey(orm[u'assets.tile'], null=False)),
            ('content', models.ForeignKey(orm[u'assets.content'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tile_id', 'content_id'])

        # Adding model 'TileRelation'
        db.create_table(u'assets_tilerelation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('tile_a', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['assets.Tile'])),
            ('tile_b', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['assets.Tile'])),
            ('starting_score', self.gf('django.db.models.fields.FloatField')(default=0.0)),
        ))
        db.send_create_signal(u'assets', ['TileRelation'])


    def backwards(self, orm):
        # Deleting model 'Store'
        db.delete_table(u'assets_store')

        # Removing M2M table for field staff on 'Store'
        db.delete_table(db.shorten_name(u'assets_store_staff'))

        # Deleting model 'Product'
        db.delete_table(u'assets_product')

        # Deleting model 'ProductImage'
        db.delete_table(u'assets_productimage')

        # Deleting model 'Content'
        db.delete_table(u'assets_content')

        # Removing M2M table for field tagged_products on 'Content'
        db.delete_table(db.shorten_name(u'assets_content_tagged_products'))

        # Deleting model 'Image'
        db.delete_table(u'assets_image')

        # Deleting model 'Video'
        db.delete_table(u'assets_video')

        # Deleting model 'Review'
        db.delete_table(u'assets_review')

        # Deleting model 'Theme'
        db.delete_table(u'assets_theme')

        # Deleting model 'Feed'
        db.delete_table(u'assets_feed')

        # Deleting model 'Page'
        db.delete_table(u'assets_page')

        # Deleting model 'Tile'
        db.delete_table(u'assets_tile')

        # Removing M2M table for field products on 'Tile'
        db.delete_table(db.shorten_name(u'assets_tile_products'))

        # Removing M2M table for field content on 'Tile'
        db.delete_table(db.shorten_name(u'assets_tile_content'))

        # Deleting model 'TileRelation'
        db.delete_table(u'assets_tilerelation')


    models = {
        u'assets.content': {
            'Meta': {'object_name': 'Content'},
            'attributes': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'source_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Store']"}),
            'tagged_products': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['assets.Product']", 'null': 'True', 'symmetrical': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'assets.feed': {
            'Meta': {'object_name': 'Feed'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed_algorithm': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'assets.image': {
            'Meta': {'object_name': 'Image', '_ormbases': [u'assets.Content']},
            u'content_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['assets.Content']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dominant_color': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'original_url': ('django.db.models.fields.TextField', [], {}),
            'width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'assets.page': {
            'Meta': {'object_name': 'Page'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_published_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'legal_copy': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Store']"}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'page'", 'null': 'True', 'to': u"orm['assets.Theme']"}),
            'theme_settings': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'assets.product': {
            'Meta': {'object_name': 'Product'},
            'attributes': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'default_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'default_image'", 'null': 'True', 'to': u"orm['assets.ProductImage']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_scraped_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'price': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Store']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'assets.productimage': {
            'Meta': {'object_name': 'ProductImage'},
            'attributes': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'dominant_color': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'original_url': ('django.db.models.fields.TextField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'product_images'", 'to': u"orm['assets.Product']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {}),
            'width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'assets.review': {
            'Meta': {'object_name': 'Review', '_ormbases': [u'assets.Content']},
            'body': ('django.db.models.fields.TextField', [], {}),
            u'content_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['assets.Content']", 'unique': 'True', 'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Product']"})
        },
        u'assets.store': {
            'Meta': {'object_name': 'Store'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'default_theme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'store'", 'null': 'True', 'to': u"orm['assets.Theme']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'public_base_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'staff': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'stores'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'assets.theme': {
            'Meta': {'object_name': 'Theme'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'default': "'apps/pinpoint/templates/pinpoint/campaign_base.html'", 'max_length': '1024'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'assets.tile': {
            'Meta': {'object_name': 'Tile'},
            'attributes': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True'}),
            'clicks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['assets.Content']", 'symmetrical': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tiles'", 'to': u"orm['assets.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'prioritized': ('django.db.models.fields.BooleanField', [], {}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['assets.Product']", 'symmetrical': 'False'}),
            'starting_score': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'assets.tilerelation': {
            'Meta': {'object_name': 'TileRelation'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'starting_score': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'tile_a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['assets.Tile']"}),
            'tile_b': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['assets.Tile']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'assets.video': {
            'Meta': {'object_name': 'Video', '_ormbases': [u'assets.Content']},
            'caption': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            u'content_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['assets.Content']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'original_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'player': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['assets']