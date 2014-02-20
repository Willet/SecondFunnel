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
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_theme', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='store', null=True, to=orm['pinpoint.StoreTheme'])),
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
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('details', self.gf('django.db.models.fields.TextField')(null=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('sku', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('price', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('default_image', self.gf('django.db.models.fields.related.ForeignKey')(related_name='default_image', null=True, to=orm['assets.ProductImage'])),
            ('last_scraped_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('attributes', self.gf('jsonfield.fields.JSONField')(null=True)),
        ))
        db.send_create_signal(u'assets', ['Product'])

        # Adding model 'ProductImage'
        db.create_table(u'assets_productimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Product'])),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('original_url', self.gf('django.db.models.fields.TextField')()),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('height', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
        ))
        db.send_create_signal(u'assets', ['ProductImage'])

        # Adding model 'Content'
        db.create_table(u'assets_content', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('source_url', self.gf('django.db.models.fields.TextField')(null=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('tagged_products', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=512, null=True)),
            ('attributes', self.gf('jsonfield.fields.JSONField')(null=True)),
        ))
        db.send_create_signal(u'assets', ['Content'])

        # Adding model 'Image'
        db.create_table(u'assets_image', (
            (u'content_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Content'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('original_url', self.gf('django.db.models.fields.TextField')()),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('height', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
        ))
        db.send_create_signal(u'assets', ['Image'])

        # Adding model 'Video'
        db.create_table(u'assets_video', (
            (u'content_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Content'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('player', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_checksum', self.gf('django.db.models.fields.CharField')(max_length=512)),
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
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal(u'assets', ['Theme'])

        # Adding model 'Feed'
        db.create_table(u'assets_feed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('feed_algorithm', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'assets', ['Feed'])

        # Adding model 'Page'
        db.create_table(u'assets_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('theme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Theme'], null=True)),
            ('theme_settings', self.gf('jsonfield.fields.JSONField')(null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('url_slug', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('legal_copy', self.gf('django.db.models.fields.TextField')(null=True)),
            ('last_published_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Feed'])),
        ))
        db.send_create_signal(u'assets', ['Page'])

        # Adding model 'Tile'
        db.create_table(u'assets_tile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('old_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Feed'])),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('prioritized', self.gf('django.db.models.fields.BooleanField')()),
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


    models = {
        u'assets.content': {
            'Meta': {'object_name': 'Content'},
            'attributes': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'source_url': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Store']"}),
            'tagged_products': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '512', 'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'assets.feed': {
            'Meta': {'object_name': 'Feed'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed_algorithm': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'assets.image': {
            'Meta': {'object_name': 'Image', '_ormbases': [u'assets.Content']},
            u'content_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['assets.Content']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'original_url': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {}),
            'width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        u'assets.page': {
            'Meta': {'object_name': 'Page'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_published_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'legal_copy': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Theme']", 'null': 'True'}),
            'theme_settings': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'assets.product': {
            'Meta': {'object_name': 'Product'},
            'attributes': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'default_image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'default_image'", 'null': 'True', 'to': u"orm['assets.ProductImage']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_scraped_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'price': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Store']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'assets.productimage': {
            'Meta': {'object_name': 'ProductImage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'original_url': ('django.db.models.fields.TextField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Product']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {}),
            'width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
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
            'default_theme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'store'", 'null': 'True', 'to': u"orm['pinpoint.StoreTheme']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'public_base_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'staff': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'stores'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'assets.theme': {
            'Meta': {'object_name': 'Theme'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Store']"}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'assets.tile': {
            'Meta': {'object_name': 'Tile'},
            'content': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['assets.Content']", 'symmetrical': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['assets.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'prioritized': ('django.db.models.fields.BooleanField', [], {}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['assets.Product']", 'symmetrical': 'False'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'assets.video': {
            'Meta': {'object_name': 'Video', '_ormbases': [u'assets.Content']},
            u'content_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['assets.Content']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'player': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.TextField', [], {})
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
        },
        u'pinpoint.storetheme': {
            'Meta': {'unique_together': "(('store_id', 'page_id'),)", 'object_name': 'StoreTheme'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.TextField', [], {'default': '\'<!DOCTYPE html>\\r\\n<html lang="en">\\r\\n<head>\\r\\n    {{ opengraph_tags }}\\r\\n    {{ campaign_config }}\\r\\n    {{ head_content }}\\r\\n    <link rel="shortcut icon"\\r\\n         href="http://www.gap.com/favicon.ico" />\\r\\n    <link rel="stylesheet"\\r\\n          href="https://elasticbeanstalk-us-east-1-056265713214.s3.amazonaws.com/static-misc-secondfunnel/themes/gap.css"/>\\r\\n    <title>{{ page.name|default:"Gap" }}</title>\\r\\n    <style type="text/css">\\r\\n        /* out of necessity */\\r\\n        .visible-xs.jumbotron, .visible-sm.jumbotron { /* mobile hero */\\r\\n            {% if mobile_hero_image %}\\r\\n                background-image: url(\\\'{{ mobile_hero_image }}\\\');\\r\\n            {% else %}\\r\\n                background-image: url(\\\'{{ desktop_hero_image }}\\\');\\r\\n            {% endif %}\\r\\n        }\\r\\n        .visible-md.jumbotron, .visible-lg.jumbotron { /* desktop hero */\\r\\n            {% if desktop_hero_image %}\\r\\n                background-image: url(\\\'{{ desktop_hero_image }}\\\');\\r\\n            {% else %}\\r\\n                background-image: url(\\\'{{ mobile_hero_image }}\\\');\\r\\n            {% endif %}\\r\\n        }\\r\\n    </style>\\r\\n</head>\\r\\n<body>\\r\\n    <div class=\\\'header\\\'>\\r\\n        <div class="navbar navbar-fixed-top navbar-static-top"\\r\\n             role="navigation">\\r\\n            <div class="container">\\r\\n                <ul class="nav navbar-nav navbar-left">\\r\\n                    <li>\\r\\n                        <a class="navbar-brand gap" href="http://www.gap.com" target="_blank">&nbsp;</a>\\r\\n                        <a class="navbar-brand old_navy navbar-brand hidden-xs hidden-sm" href="http://www.oldnavy.com" target="_blank">&nbsp;</a>\\r\\n                        <a class="navbar-brand banana_republic hidden-xs hidden-sm" href="http://www.bananarepublic.com" target="_blank">&nbsp;</a>\\r\\n                        <a class="navbar-brand piperlime hidden-xs hidden-sm" href="http://www.piperlime.com" target="_blank">&nbsp;</a>\\r\\n                        <a class="navbar-brand athleta hidden-xs hidden-sm"  href="http://www.athleta.com" target="_blank">&nbsp;</a>\\r\\n                    </li>\\r\\n                    <li class="other-brands dropdown hidden-md hidden-lg">\\r\\n                        <a href="#" class="dropdown-toggle" data-toggle="dropdown">&nbsp;</a>\\r\\n                        <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel">\\r\\n                            <li>\\r\\n                                <a href="http://www.gap.com" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Gap</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="old_navy">\\r\\n                                <a href="http://oldnavy.com" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Old Navy</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="banana_republic">\\r\\n                                <a href="http://www.bananarepublic.com" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Banana Republic</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="piperlime">\\r\\n                                <a href="http://www.piperlime.com" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Piperlime</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="athleta">\\r\\n                                <a href="http://www.athleta.com" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Athleta</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                        </ul>\\r\\n                    </li>\\r\\n                    <li class="stay-connected dropdown hidden-md hidden-lg">\\r\\n                        <a href="#" class="dropdown-toggle" data-toggle="dropdown">&nbsp;</a>\\r\\n                        <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel">\\r\\n                            <li class="facebook">\\r\\n                                <a href="http://www.facebook.com/Gap" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Facebook</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="twitter">\\r\\n                                <a href="http://www.twitter.com/gap" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Twitter</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="pinterest">\\r\\n                                <a href="http://www.pinterest.com/Gap" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Pinterest</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="instagram">\\r\\n                                <a href="http://www.instagram.com/gap" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Instagram</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                            <li class="tumblr">\\r\\n                                <a href="http://gap.tumblr.com" target="_blank">\\r\\n                                    <span class="icon"></span>\\r\\n                                    <span class="text">Tumblr</span>\\r\\n                                </a>\\r\\n                            </li>\\r\\n                        </ul>\\r\\n                    </li>\\r\\n                </ul>\\r\\n                <ul class="nav navbar-nav navbar-right">\\r\\n                    <li class="sharing hidden-xs hidden-sm">\\r\\n                        Stay Connected:\\r\\n                        <ul>\\r\\n                            <li class="icon pinterest">\\r\\n                                <a href="http://www.pinterest.com/Gap"\\r\\n                                   target="_blank">&nbsp;</a>\\r\\n                            </li>\\r\\n                            <li class="icon facebook">\\r\\n                                <a href="http://www.facebook.com/Gap"\\r\\n                                   target="_blank">&nbsp;</a>\\r\\n                            </li>\\r\\n                            <li class="icon twitter">\\r\\n                                <a href="http://www.twitter.com/gap"\\r\\n                                   target="_blank">&nbsp;</a>\\r\\n                            </li>\\r\\n                            <li class="icon instagram">\\r\\n                                <a href="http://www.instagram.com/gap"\\r\\n                                   target="_blank">&nbsp;</a>\\r\\n                            </li>\\r\\n                            <li class="icon youtube">\\r\\n                                <a href="http://www.youtube.com/Gap"\\r\\n                                   target="_blank">&nbsp;</a>\\r\\n                            </li>\\r\\n                            <li class="icon tumblr">\\r\\n                                <a href="http://gap.tumblr.com"\\r\\n                                   target="_blank">&nbsp;</a>\\r\\n                            </li>\\r\\n                        </ul>\\r\\n                    </li>\\r\\n                </ul>\\r\\n            </div>\\r\\n            <!-- /.navbar-collapse -->\\r\\n        </div>\\r\\n    </div>\\r\\n    <div class="container">\\r\\n        <!-- .container is bootstrap magic, and has a viewport-dependent width. -->\\r\\n        <div id="hero-area"></div>\\r\\n        <div id="discovery-area" class="discovery-area"></div>\\r\\n        <div class="no-noscript loading"></div>\\r\\n        <noscript>\\r\\n            <!-- promotions to show when user does not have javascript.\\r\\n             this is a \\\'we need javascript\\\' message by default.\\r\\n             -->\\r\\n            <div class="alert alert-danger">\\r\\n                <b>Oh no!</b> We need JavaScript enabled to show you this page.\\r\\n            </div>\\r\\n        </noscript>\\r\\n    </div>\\r\\n\\r\\n\\r\\n    <div>\\r\\n        <!-- generic templates -->\\r\\n        <script type="text/template" id="disabled_featured_template">\\r\\n            <div class=\\\'featured product\\\'>\\r\\n                <!-- Main Display Area -->\\r\\n                <img class=\\\'img-responsive pull-left\\\' src=\\\'<%= obj.image.url %>\\\' />\\r\\n                <div class=\\\'pull-right\\\'><%= obj.title || obj.name %></div>\\r\\n                    <div class=\\\'price\\\'><%= obj.price %></div>\\r\\n                    <div>\\r\\n                        <a href=\\\'<%= obj.url %>\\\' target=\\\'_blank\\\'>BUY NOW</a>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n\\r\\n            <div class=\\\'spacer\\\'></div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="product_tile_template">\\r\\n            <div class="tap-indicator-target"></div>\\r\\n            <img class="focus" src="<%= obj.image.url %>" alt="<%= caption %>" />\\r\\n            <% if (App.option(\\\'debug\\\', 0) > 1) { %>\\r\\n                <span class="type"><%= obj[\\\'content-type\\\'] %></span>\\r\\n            <% } %>\\r\\n            <div class="name"><%= obj.title || obj.name %></div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="product_mobile_tile_template">\\r\\n            <div class="tap-indicator-target"></div>\\r\\n            <img class="focus" src="<%= obj.image.url %>" alt="<%= caption %>" />\\r\\n            <% if (App.option(\\\'debug\\\', 0) > 1) { %>\\r\\n                <span class="type"><%= obj[\\\'content-type\\\'] %></span>\\r\\n            <% } %>\\r\\n            <% if (obj.name) { %>\\r\\n                <div class="caption">\\r\\n                    <span><%= obj.name %></span>\\r\\n                </div>\\r\\n            <% } %>\\r\\n            <div class="social-buttons"></div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="image_tile_template">\\r\\n            <div class="tap-indicator-target"></div>\\r\\n            <div class=\\\'relative\\\'>\\r\\n                <img class="focus" src="<%= obj.image.url %>" alt="<%= obj.caption %>" />\\r\\n                <!-- Varies depending on source (e.g. facebook, styldby, etc)-->\\r\\n                <div class="overlay">\\r\\n                    <div class=\\\'align-container\\\'>\\r\\n                        <div class=\\\'cell\\\'>\\r\\n                            <% /* "Shop product" is actually wanted for the tile overlay */ %>\\r\\n                            <div class="title">\\r\\n                                <% if (obj.title || obj.name || obj.caption) { %>\\r\\n                                    <%= (obj.title || obj.name || obj.caption) %>\\r\\n                                <% } else if (obj[\\\'related-products\\\'] && obj[\\\'related-products\\\'].length > 0) { %>\\r\\n                                    <span>Shop product</span>\\r\\n                                    <br/>\\r\\n                                    <% _.each(obj[\\\'related-products\\\'], function (related) { %>\\r\\n                                        <span class=\\\'shop-products\\\'><%= related.title || related.name || related.caption %></span>\\r\\n                                    <% }); %>\\r\\n                                <% } else { %>\\r\\n                                    Shop product\\r\\n                                <% } %>\\r\\n                            </div>\\r\\n                            <% var validSources = [\\\'tumblr\\\', \\\'instagram\\\', \\\'facebook\\\', \\\'styld.by\\\']; %>\\r\\n                            <% if (_.indexOf(validSources, obj.source) != -1) { %>\\r\\n                                <div class=\\\'author\\\'>\\r\\n                                    <% if (obj.source == "styld.by") { %>\\r\\n                                        <%= obj.source %><%= obj.user %>\\r\\n                                    <% } else if (_.indexOf(validSources, (obj.source||\\\'\\\').toLowerCase()) != -1) { %>\\r\\n                                        <span class=\\\'propercase\\\'><%= obj.source %></span>\\r\\n                                    <% } %>\\r\\n                                </div>\\r\\n                            <% } %>\\r\\n                            </div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n            <% if (App.option("debug", 0) > 1) { %>\\r\\n                <span class="type"><%= obj["content-type"] %></span>\\r\\n            <% } %>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="youtube_tile_template">\\r\\n            <div class="img-responsive thumbnail"\\r\\n                 style="background-image: url(\\\'<%= obj.thumbnail || obj.image.url %>\\\');">\\r\\n              &nbsp;\\r\\n              <img src="" alt="this img tag intentionally left blank" style="visibility:hidden"/>\\r\\n            </div>\\r\\n            <%= obj.caption || obj.name %>\\r\\n            <div class="social-buttons"></div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="preview_container_template">\\r\\n            <div class="tablecell">\\r\\n                <div class="content">\\r\\n                    <span class="close">&#x00D7;</span>\\r\\n                    <div class="scrollable">\\r\\n                        <div class="template target"></div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n            <div class="mask"></div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="mobile_preview_container_template">\\r\\n            <div class="tablecell">\\r\\n                <div class="content">\\r\\n                    <span class="close">BACK</span>\\r\\n                    <div class="scrollable">\\r\\n                        <div class="template target"></div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n            <div class="mask"></div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="tile_preview_template">\\r\\n            <h2><span class="label label-info"><%= obj.template %>_preview_template</span> is missing.</h2>\\r\\n            <p>You can define one in your template.</p>\\r\\n            <ul>\\r\\n                <% for (i in obj) { %>\\r\\n                    <li><b><%= i %></b>: <%= obj[i] %></li>\\r\\n                <% } %>\\r\\n            </ul>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="tap_indicator_template">\\r\\n            +\\r\\n            <div>\\r\\n                <%= App.option(\\\'tapIndicatorText\\\', \\\'tap to see more\\\') %>\\r\\n            </div>\\r\\n        </script>\\r\\n        <script type="text/template" id="facebook_social_button_template">\\r\\n            <div class=\\\'button facebook\\\'>\\r\\n                <img src="//s3-us-west-2.amazonaws.com/static-misc-secondfunnel/images/fb-like-0.png" alt="Like" class="placeholder" />\\r\\n                <fb:like href="<%= url %>" width="48" layout="button_count"\\r\\n                         show_faces="false"></fb:like>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="twitter_social_button_template">\\r\\n            <% if (showCount) { %>\\r\\n                <div class=\\\'button twitter\\\' style=\\\'height: 13px; width: 77px;\\\'>\\r\\n                    <a href="https://twitter.com/share"\\r\\n                       class="twitter-share-button"\\r\\n                       data-text="<%= caption || description || name %> <%= url %>"\\r\\n                       data-lang="en" data-height= "15">\\r\\n                      Tweet\\r\\n                    </a>\\r\\n                </div>\\r\\n            <% } else { %>\\r\\n                <div class=\\\'button twitter\\\'>\\r\\n                    <a href="https://twitter.com/share?url=<%= url %>&text=<%= caption || description || name %>"\\r\\n                       target="_blank">\\r\\n                        <img src="//elasticbeanstalk-us-east-1-056265713214.s3.amazonaws.com/pinpoint/images/twitterButton.png"/>\\r\\n                    </a>\\r\\n                </div>\\r\\n            <% } %>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="pinterest_social_button_template">\\r\\n            <div class=\\\'button pinterest\\\'>\\r\\n                <a href="http://pinterest.com/pin/create/button/?url=<%= url %>&media=<%= image %>&description=<%= caption || description || name %>"\\r\\n                   target="_blank"><img src="//elasticbeanstalk-us-east-1-056265713214.s3.amazonaws.com/pinpoint/images/pinpointButton.png"/></a>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="reddit_social_button_template">\\r\\n            <div class="button reddit">\\r\\n                <a href="http://www.reddit.com/submit"\\r\\n                   onclick="window.location = \\\'http://www.reddit.com/submit?url=<%= url %>\\\'; return false"\\r\\n                  ><img src="http://www.reddit.com/static/spreddit7.gif"\\r\\n                       alt="submit to reddit"\\r\\n                       border="0" /></a>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="tumblr_social_button_template">\\r\\n            <div class="button tumblr">\\r\\n                <a href="http://www.tumblr.com/share/photo?source=<%= image %>&caption=<%= caption || description || name %>&click_thru=<%= url %>"\\r\\n                     target=\\\'_blank\\\'><img src="http://platform.tumblr.com/v1/share_1.png"/></a>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="share_social_button_template">\\r\\n            <div class="button share-this">\\r\\n                <a href=""><img src="//s3-us-west-2.amazonaws.com/static-misc-secondfunnel/images/Sharethis-draft1.png"\\r\\n                                alt="Share this" border="0" /></a>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="share_popup_template">\\r\\n            <div class="mask"></div>\\r\\n            <div class="tablecell">\\r\\n                <div class="content">\\r\\n                    <span class="close">&#x00D7;</span>\\r\\n                    <h2> Share This </h2>\\r\\n                    <div class="share"></div>\\r\\n                </div>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="share_popup_option_template">\\r\\n            <a href="<%= url %>" target="_blank">\\r\\n                <div style="position: relative;">\\r\\n                    <div class="share_img"></div>\\r\\n                    <span class="share_text"><%= text %></span>\\r\\n                </div>\\r\\n            </a>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="product_preview_template">\\r\\n            <!-- any (store.name)_(type)_... templates will be used in place\\r\\n             of default templates if they exist. -->\\r\\n            <div class=\\\'content-wrapper row\\\'>\\r\\n                <div class=\\\'cell middle image-div col-sm-6 col-md-6\\\'>\\r\\n                    <div class=\\\'image\\\'>\\r\\n                        <img src=\\\'<%= obj.image.url %>\\\'/>\\r\\n                    </div>\\r\\n                    <% if (obj.images.length > 1) { %>\\r\\n                    <div class=\\\'gallery\\\'></div>\\r\\n                    <% } %>\\r\\n                </div>\\r\\n                <div class=\\\'cell middle info col-sm-6 col-md-6\\\'>\\r\\n                    <div class=\\\'title\\\'><%= obj.title || obj.name %></div>\\r\\n                    <div class=\\\'red marker price\\\'><%= obj.price %></div>\\r\\n                    <div class=\\\'description\\\'>\\r\\n                        <div class=\\\'desc-title\\\'>Overview</div>\\r\\n                        <ul>\\r\\n                            <% var sentences =\\r\\n                            _.compact(obj.description.split(\\\'.\\\')); %>\\r\\n                            <% _.each(sentences, function(sentence) { %>\\r\\n                            <li><%= SecondFunnel.utils.safeString(sentence)\\r\\n                                %>\\r\\n                            </li>\\r\\n                            <% }); %>\\r\\n                        </ul>\\r\\n                    </div>\\r\\n                    <div>\\r\\n                        <div class="social-buttons"></div>\\r\\n                        <div class=\\\'spacer\\\'></div>\\r\\n                    </div>\\r\\n                    <div class=\\\'gap-buttons\\\'>\\r\\n                        <a class=\\\'button find-store\\\'\\r\\n                           href=\\\'http://www.gap.com/customerService/storeLocator.do\\\'\\r\\n                           target=\\\'_blank\\\'>\\r\\n                            <!-- find-store is magic -->\\r\\n                            Find in Store\\r\\n                        </a>\\r\\n                        <a class=\\\'button in-store\\\' href=\\\'<%= obj.url %>\\\'\\r\\n                           target=\\\'_blank\\\'>\\r\\n                            <!-- in-store is magic -->\\r\\n                            Shop on Gap.com\\r\\n                        </a>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="product_mobile_preview_template">\\r\\n            <div class=\\\'content-wrapper row\\\'>\\r\\n                <div class=\\\'image-div col-sm-6 col-md-6\\\'>\\r\\n                    <div class=\\\'image\\\'>\\r\\n                        <% if (obj.images.length > 1) { %>\\r\\n                            <span class="gallery-swipe-left"></span>\\r\\n                            <img src=\\\'<%= obj.image.url %>\\\'/>\\r\\n                            <span class="gallery-swipe-right"></span>\\r\\n                        <% } else { %>\\r\\n                            <img src=\\\'<%= obj.image.url %>\\\'/>\\r\\n                        <% } %>\\r\\n                    </div>\\r\\n                    <% if (obj.images.length > 1) { %>\\r\\n                        <div class=\\\'gallery\\\'></div>\\r\\n                    <% } %>\\r\\n                </div>\\r\\n                <div class=\\\'info col-sm-6 col-md-6\\\'>\\r\\n                    <div class=\\\'title\\\'><%= obj.title || obj.name %></div>\\r\\n                    <div class=\\\'red marker price\\\'><%= obj.price %></div>\\r\\n                    <div class=\\\'gap-buttons\\\'>\\r\\n                        <a class=\\\'button in-store\\\' href=\\\'<%= obj.url %>\\\'\\r\\n                           target=\\\'_blank\\\'>\\r\\n                            <!-- in-store is magic -->\\r\\n                            Shop on Gap.com\\r\\n                        </a>\\r\\n                        <a class=\\\'button find-store\\\'\\r\\n                           href=\\\'http://m.gap.com/storelocator.html\\\'\\r\\n                           target=\\\'_blank\\\'>\\r\\n                            <!-- find-store is magic -->\\r\\n                            Find in Store\\r\\n                        </a>\\r\\n                    </div>\\r\\n                    <div class=\\\'description\\\'>\\r\\n                        <div class=\\\'desc-title\\\'>Overview</div>\\r\\n                        <ul>\\r\\n                            <% var sentences = _.compact(obj.description.split(\\\'.\\\')); %>\\r\\n                            <% _.each(sentences, function(sentence) { %>\\r\\n                            <li><%= SecondFunnel.utils.safeString(sentence)\\r\\n                                %>\\r\\n                            </li>\\r\\n                            <% }); %>\\r\\n                        </ul>\\r\\n                    </div>\\r\\n                    <div>\\r\\n                        <div class="social-buttons"></div>\\r\\n                        <div class=\\\'spacer\\\'></div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="image_mobile_preview_template">\\r\\n            <% var products = obj[\\\'related-products\\\']; %>\\r\\n            <% if (products.length) { %>\\r\\n            <% product = products[0]; %>\\r\\n            <div class=\\\'image-with-related-products\\\'>\\r\\n            <% } else { %>\\r\\n            <div class=\\\'image-without-related-products\\\'>\\r\\n            <% } %>\\r\\n                <div class="row">\\r\\n                    <div class="image middle cell capped-width">\\r\\n                        <% if (products.length) { %>\\r\\n                            <span class="gallery-swipe-left"></span>\\r\\n                            <img src=\\\'<%= product.images[0].url %>\\\' alt="image"/>\\r\\n                            <span class="gallery-swipe-right"></span>\\r\\n                        <% } else { %>\\r\\n                            <img src=\\\'<%= obj.defaultImage.url %>\\\'/>\\r\\n                        <% } %>\\r\\n                    </div>\\r\\n                    <% var validSources = [\\\'tumblr\\\', \\\'instagram\\\', \\\'facebook\\\', \\\'styld.by\\\']; %>\\r\\n                    <% if (_.indexOf(validSources, obj.source) != -1) { %>\\r\\n                        <div class=\\\'author\\\'>\\r\\n                            <% if (obj.source == "styld.by") { %>\\r\\n                                <%= obj.source %><a href="<%= obj[\\\'source-url\\\']%>"><%= obj.user %></a>\\r\\n                            <% } else if (_.indexOf(validSources, (obj.source||\\\'\\\').toLowerCase()) != -1) { %>\\r\\n                                <span class=\\\'propercase\\\'><a href="<%= obj[\\\'source-url\\\']%>"><%= obj.source %></a></span>\\r\\n                            <% } %>\\r\\n                        </div>\\r\\n                    <% } %>\\r\\n                    <% if (products.length) { %>\\r\\n                        <div class=\\\'gallery\\\'></div>\\r\\n                    <% } %>\\r\\n                    <div class="middle cell">\\r\\n                        <% if (products.length) { %>\\r\\n                            <div class=\\\'title\\\'><%= product.title || product.name || ""  %></div>\\r\\n                            <div class=\\\'price\\\'><%= product.price %></div>\\r\\n                            <div class=\\\'gap-buttons\\\'>\\r\\n                                <a class=\\\'button in-store\\\' href=\\\'<%= obj.url %>\\\'\\r\\n                                   target=\\\'_blank\\\'>\\r\\n                                  <!-- in-store is magic -->\\r\\n                                  Shop on Gap.com\\r\\n                                </a>\\r\\n                                <a class=\\\'button find-store\\\'\\r\\n                                   href=\\\'http://m.gap.com/storelocator.html\\\'\\r\\n                                   target=\\\'_blank\\\'>\\r\\n                                  <!-- find-store is magic -->\\r\\n                                  Find in Store\\r\\n                                </a>\\r\\n                            </div>\\r\\n                            <div class=\\\'description\\\'>\\r\\n                                <div class=\\\'desc-title\\\'>Overview</div>\\r\\n                                <ul>\\r\\n                                    <% var sentences = _.compact(product.description.split(\\\'.\\\')); %>\\r\\n                                    <% _.each(sentences, function(sentence) { %>\\r\\n                                        <li><%= SecondFunnel.utils.safeString(sentence) %></li>\\r\\n                                    <% }); %>\\r\\n                                </ul>\\r\\n                            </div>\\r\\n                        <% } else { %>\\r\\n                            <div class=\\\'description\\\'>\\r\\n                                <%= SecondFunnel.utils.safeString(obj.caption || obj.description) %>\\r\\n                            </div>\\r\\n                        <% } %>\\r\\n                        <div>\\r\\n                            <div class="social-buttons"></div>\\r\\n                            <div class=\\\'spacer\\\'></div>\\r\\n                        </div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n        </script>\\r\\n\\r\\n        <script type="text/template" id="image_preview_template">\\r\\n            <% if (obj[\\\'related-products\\\'].length) { %>\\r\\n            <% var product = obj[\\\'related-products\\\'][0]; %>\\r\\n            <div class="image-with-related-products">\\r\\n                <div class="row">\\r\\n                    <div class="image middle cell capped-width">\\r\\n                        <img src="<%= obj.defaultImage.url %>" alt="image"/>\\r\\n                        <div class=\\\'caption\\\'><%= (obj.title || obj.name || obj.caption || "") %></div>\\r\\n                        <% var validSources = [\\\'tumblr\\\', \\\'instagram\\\', \\\'facebook\\\', \\\'styld.by\\\']; %>\\r\\n                        <% if (_.indexOf(validSources, obj.source) != -1) { %>\\r\\n                            <div class=\\\'author\\\'>\\r\\n                                <% if (obj.source == "styld.by") { %>\\r\\n                                    <%= obj.source %><a href="<%= obj[\\\'source-url\\\']%>"><%= obj.user %></a>\\r\\n                                <% } else if (_.indexOf(validSources, (obj.source||\\\'\\\').toLowerCase()) != -1) { %>\\r\\n                                    <span class=\\\'propercase\\\'><a href="<%= obj[\\\'source-url\\\']%>"><%= obj.source %></a></span>\\r\\n                                <% } %>\\r\\n                            </div>\\r\\n                        <% } %>\\r\\n                    </div>\\r\\n                    <div class="middle cell center">\\r\\n                        <% if (product.images.length > 1 && App.support.mobile()) { %>\\r\\n                            <div class="image">\\r\\n                                <span class="gallery-swipe-left gallery-related"></span>\\r\\n                                <img class="main-image" src="<%= product.images[0].url %>" alt="related product"/>\\r\\n                                <span class="gallery-swipe-right gallery-related"></span>\\r\\n                            </div>\\r\\n                        <% } else { %>\\r\\n                            <img class="main-image" src="<%= product.images[0].url %>" alt="related product"/>\\r\\n                        <% } %>\\r\\n                        <% if (product.images.length > 1) { %>\\r\\n                            <div class=\\\'gallery\\\'></div>\\r\\n                        <% } %>\\r\\n                    </div>\\r\\n                    <div class="middle cell">\\r\\n                        <div class=\\\'title\\\'><%= product.title || product.name%></div>\\r\\n                        <div class=\\\'price\\\'><%= product.price %></div>\\r\\n                        <div class=\\\'description\\\'>\\r\\n                            <div class=\\\'desc-title\\\'>Overview</div>\\r\\n                            <ul>\\r\\n                                <% var sentences =\\r\\n                                _.compact((product.description || "").split(\\\'.\\\'));%>\\r\\n                                <% _.each(sentences, function(sentence) { %>\\r\\n                                <li><%= SecondFunnel.utils.safeString(sentence)\\r\\n                                    %>\\r\\n                                </li>\\r\\n                                <% }); %>\\r\\n                            </ul>\\r\\n                        </div>\\r\\n                        <div>\\r\\n                            <div class="social-buttons"></div>\\r\\n                            <div class=\\\'spacer\\\'></div>\\r\\n                        </div>\\r\\n                        <div class=\\\'gap-buttons\\\'>\\r\\n                            <a class=\\\'button find-store\\\'\\r\\n                               href=\\\'http://www.gap.com/customerService/storeLocator.do\\\'\\r\\n                               target=\\\'_blank\\\'>\\r\\n                                Find in Store\\r\\n                            </a>\\r\\n                            <a class=\\\'button in-store\\\'\\r\\n                               href=\\\'<%= product.url %>\\\' target=\\\'_blank\\\'>\\r\\n                                Shop on Gap.com\\r\\n                            </a>\\r\\n                        </div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n            <% } else { %>\\r\\n            <div class="image-without-related-products">\\r\\n                <div class="row">\\r\\n                    <div class="image middle cell capped-width">\\r\\n                        <img src="<%= obj.defaultImage.url %>" alt="image"/>\\r\\n                    </div>\\r\\n                    <div class="middle cell">\\r\\n                        <div class="info">\\r\\n                            <div class=\\\'title\\\'><%= obj.title || obj.name || "Shop Product" %></div>\\r\\n                            <div class=\\\'author\\\'>\\r\\n                                <% if(obj.source == "styld.by") { %>\\r\\n                                    <%= obj.source %><%= obj.user %>\\r\\n                                <% } else if (_.indexOf(validSources, (obj.source||\\\'\\\').toLowerCase()) != -1) { %>\\r\\n                                    <span class=\\\'propercase\\\'><%= obj.source %></span>\\r\\n                                <% } %>\\r\\n                            </div>\\r\\n                            <div class=\\\'description\\\'>\\r\\n                                <%= SecondFunnel.utils.safeString(obj.caption || obj.description) %>\\r\\n                            </div>\\r\\n                            <div class="social-buttons"></div>\\r\\n                            <div class=\\\'spacer\\\'></div>\\r\\n                        </div>\\r\\n                    </div>\\r\\n                </div>\\r\\n            </div>\\r\\n            <% } %>\\r\\n        </script>\\r\\n\\r\\n        <!-- custom templates -->\\r\\n        <script type="text/template" id="hero_template">\\r\\n            <div class="visible-xs jumbotron">\\r\\n                <img src="{{ mobile_hero_image }}" alt="Hero" />\\r\\n            </div>\\r\\n            <div class="visible-sm jumbotron">\\r\\n                <img src="{{ mobile_hero_image }}" alt="Hero" />\\r\\n            </div>\\r\\n            <div class="visible-md visible-lg jumbotron"></div>\\r\\n            <div class="overlay">\\r\\n                <div class=\\\'buttons\\\'>\\r\\n                    <%\\r\\n                        var share = App.options.page.description;\\r\\n                        var src = top.location.href;\\r\\n                        var fbLink = \\\'https://www.facebook.com/sharer/sharer.php?\\\'\\r\\n                            + \\\'s=100\\\'\\r\\n                            + \\\'&p[title]=Gap\\\'\\r\\n                            + \\\'&p[summary]=\\\' + share.replace(\\\' \\\', \\\'+\\\')\\r\\n                            + \\\'&p[url]=\\\' + encodeURIComponent(src)\\r\\n                            + \\\'&p[images][0]={{ desktop_hero_image }}\\\';\\r\\n\\r\\n                        var twtLink = \\\'http://twitter.com/share?\\\'\\r\\n                            + \\\'url=\\\' + encodeURIComponent(src)\\r\\n                            + \\\'&text=\\\' + encodeURIComponent(share);\\r\\n\\r\\n                        var mailLink = \\\'mailto:?\\\'\\r\\n                            + \\\'body=\\\' + encodeURIComponent(share);\\r\\n                    %>\\r\\n                    <a href=\\\'<%= fbLink %>\\\' target=\\\'_blank\\\'>\\r\\n                        <img src=\\\'//s3-us-west-2.amazonaws.com/static-misc-secondfunnel/images/gap/facebookicon.png\\\' />\\r\\n                    </a>\\r\\n                    <a href=\\\'<%= twtLink %>\\\' target=\\\'_blank\\\'>\\r\\n                        <img src=\\\'//s3-us-west-2.amazonaws.com/static-misc-secondfunnel/images/gap/twittericon.png\\\' />\\r\\n                    </a>\\r\\n                    <a href=\\\'<%= mailLink %>\\\' target=\\\'_blank\\\'>\\r\\n                        <img src=\\\'//s3-us-west-2.amazonaws.com/static-misc-secondfunnel/images/gap/emailicon.png\\\' />\\r\\n                    </a>\\r\\n                </div>\\r\\n                <span class=\\\'find\\\'>\\r\\n                    <% if (!App.support.mobile()) { %>\\r\\n                        <a href=\\\'http://www.gap.com/customerService/storeLocator.do\\\' target=\\\'_blank\\\'>Find a store</a>\\r\\n                    <% } else { %>\\r\\n                        <a href=\\\'http://m.gap.com/storelocator.html\\\' target=\\\'_blank\\\'>Find a store</a>\\r\\n                    <% } %>\\r\\n                </span>\\r\\n            </div>\\r\\n        </script>\\r\\n    </div>\\r\\n\\r\\n    {{ body_content }}\\r\\n\\r\\n    <!-- GAP Google Analytics -->\\r\\n    <script type="text/javascript">\\r\\n      // Shorthand for pushing data to Google Analytics\\r\\n      var productName = null,\\r\\n          recordEvent = function (event, eventCategory, eventAction, eventLabel) {\\r\\n              dataLayer.push({\\r\\n                  \\\'event\\\': event,\\r\\n                  \\\'eventCategory\\\': eventCategory,\\r\\n                  \\\'eventAction\\\': eventAction,\\r\\n                  \\\'eventLabel\\\': eventLabel\\r\\n              });\\r\\n          };\\r\\n\\r\\n      // Tracking Code for GAP\\\'s Google Analytics\\r\\n      window.GAP_ANALYTICS = new App.tracker.EventManager({\\r\\n          // 1 - Top Nav\\r\\n          \\\'click a.navbar-brand, .other-brands.dropdown a:not(.dropdown-toggle)\\\': function () {\\r\\n              var brand;\\r\\n              if ($(this).text().length) {\\r\\n                  brand = $(this).text().toLowerCase();\\r\\n              } else {\\r\\n                  brand = /(?:(\\\\w+?).com)/.exec($(this).attr(\\\'href\\\'))[1];\\r\\n              }\\r\\n              recordEvent(\\\'gap_nav\\\', \\\'nav\\\', \\\'exit\\\', \\\'nav - \\\' + brand);\\r\\n          },\\r\\n          // 2 - Header Logo\\r\\n          \\\'click header > a\\\': function () {\\r\\n              recordEvent(\\\'header_logo\\\', \\\'header\\\', \\\'exit\\\', \\\'gap.com\\\');\\r\\n          },\\r\\n          // 3 - Social Subscribe Links\\r\\n          \\\'click .nav.navbar-nav.navbar-right a, .stay-connected .dropdown-menu a\\\': function () {\\r\\n              var social_network = /(?:(\\\\w+?).com)/.exec($(this).attr(\\\'href\\\'))[1];\\r\\n              recordEvent(\\\'social_follow\\\', \\\'follow\\\', social_network + \\\' follow\\\', \\\'follow\\\');\\r\\n          },\\r\\n          // 4 - Main Visual\\r\\n          \\\'click #hero-area .jumbotron\\\': function () {\\r\\n              recordEvent(\\\'main_visual\\\', \\\'main visual\\\', \\\'visual click\\\', \\\'visual click\\\');\\r\\n          },\\r\\n          // 5 - Feed Visuals\\r\\n          \\\'click .tile.product\\\': function () {\\r\\n              productName = App.discovery.collection.get($(this).attr(\\\'id\\\')).get(\\\'name\\\');\\r\\n              recordEvent(\\\'product_feed\\\', \\\'product_feed\\\', \\\'pop-up open\\\', productName);\\r\\n          },\\r\\n          // 6 - Product Social Links\\r\\n          \\\'click .content-wrapper .social-buttons .button\\\': function () {\\r\\n              var social_network = $(this).attr(\\\'class\\\').replace(/\\\\s*button\\\\s*/, \\\'\\\');\\r\\n              recordEvent(\\\'product_share\\\', \\\'product pop-up\\\', social_network + \\\' share\\\', productName);\\r\\n          },\\r\\n          // 7 - Find Product in Store\\r\\n          \\\'click .content-wrapper a.button.find-store\\\': function () {\\r\\n              recordEvent(\\\'product_find in store\\\', \\\'product pop-up\\\', \\\'find in store\\\', productName);\\r\\n          },\\r\\n          // 8 - Buy Product Online\\r\\n          \\\'click .content-wrapper a.button.in-store\\\': function () {\\r\\n              recordEvent(\\\'product_buy online\\\', \\\'product pop-up\\\', \\\'buy online\\\', productName);\\r\\n          },\\r\\n          // 10 - Share deal\\r\\n          \\\'click #hero-area .buttons a\\\': function () {\\r\\n              var social_network = /(?:(\\\\w+?).com)/.exec($(this).attr(\\\'href\\\'))[1];\\r\\n              recordEvent(\\\'deal_share\\\', \\\'header\\\', social_network + \\\' share\\\', \\\'share page\\\');\\r\\n          },\\r\\n          // 13 - Lifestyle Feed Visuals\\r\\n          \\\'click .tile.image\\\': function () {\\r\\n              var cid = $(this).attr(\\\'id\\\'),\\r\\n                  obj = App.discovery.collection.get(cid),\\r\\n                  products = obj.get(\\\'related-products\\\');\\r\\n              if (products && products.length > 0) {\\r\\n                  productName = products[0].name;\\r\\n                  recordEvent(\\\'lifestyle_feed\\\', \\\'lifestyle feed\\\', \\\'pop-up open\\\', productName);\\r\\n              } else {\\r\\n                  productName = null;\\r\\n              }\\r\\n          },\\r\\n          // 14 - Lifestyle Product Social Links\\r\\n          \\\'click .image-with-related-products .social-buttons .button, .image-without-related-products .social-buttons .button\\\': function () {\\r\\n              if (productName) {\\r\\n                  var social_network = $(this).attr(\\\'class\\\').replace(/\\\\s*button\\\\s*/, \\\'\\\');\\r\\n                  recordEvent(\\\'lifestyle_share\\\', \\\'lifestyle pop-up\\\', social_network + \\\' share\\\', productName);\\r\\n              }\\r\\n          },\\r\\n          // 15 - Find Lifestyle Product in Store\\r\\n          \\\'click .image-with-related-products a.button.find-store, .image-without-related-products a.button.find-store\\\': function () {\\r\\n              if (productName) {\\r\\n                  recordEvent(\\\'lifestyle_find in store\\\', \\\'lifestyle pop-up\\\', \\\'find in store\\\', productName);\\r\\n              }\\r\\n          },\\r\\n          // 16 - Buy Lifestyle Product Online\\r\\n          \\\'click .image-with-related-products a.button.in-store, .image-without-related-products a.button.in-store \\\\\\r\\n               .image-with-related-products a.buy, .image-without-related-products a.buy\\\': function () {\\r\\n              if (productName) {\\r\\n                  recordEvent(\\\'lifestyle_buy online\\\', \\\'lifestyle pop-up\\\', \\\'buy online\\\', productName);\\r\\n              }\\r\\n          },\\r\\n          // 17 - Lifestyle Feed Video\\r\\n          \\\'click .tile.youtube.wide\\\': function () {\\r\\n              var cid = $(this).attr(\\\'id\\\'),\\r\\n                  obj = App.discovery.collection.get(cid),\\r\\n                  products = obj.get(\\\'related-products\\\');\\r\\n              if (products && products.length > 0) {\\r\\n                  recordEvent(\\\'lifestyle_video\\\', \\\'lifestyle_feed\\\', \\\'video play\\\', products[0].name);\\r\\n              }\\r\\n          },\\r\\n\\r\\n          // 18 - Lifestyle Feed Video\\r\\n          \\\'click #hero-area .overlay .find a\\\': function() {\\r\\n              recordEvent(\\\'find_store\\\', \\\'main visual\\\', \\\'store locator\\\', \\\'find a store\\\');\\r\\n          }\\r\\n      });\\r\\n\\r\\n      // Scroll event has to be seperately tracked.\\r\\n      // 12 - Scroll for more\\r\\n      var pagesScrolled = 1;\\r\\n      App.vent.on(\\\'tracking:trackEvent\\\', function (o) {\\r\\n          if (o.action == \\\'scroll\\\') {\\r\\n              recordEvent(\\\'page_scroll\\\', \\\'scroll\\\', \\\'page_scroll\\\', \\\'scroll - \\\' + o.label);\\r\\n          }\\r\\n      });\\r\\n\\r\\n      // Subscribe to FB event for GAP Analytic tracking\\r\\n      App.vent.on(\\\'tracking:registerFacebookListeners\\\', function () {\\r\\n          FB.Event.subscribe(\\\'edge.create\\\', function(href, widget) {\\r\\n              var type = $(\\\'div.facebook\\\').eq(0).parents(\\\'.image-with-related-products, .image-without-related-products\\\');\\r\\n              if (productName && type && type.length > 0) {\\r\\n                  recordEvent(\\\'lifestyle_share\\\', \\\'lifestyle pop-up\\\', \\\'facebook share\\\', productName);\\r\\n              } else if (productName) {\\r\\n                  recordEvent(\\\'product_share\\\', \\\'product pop-up\\\', \\\'facebook share\\\', productName);\\r\\n              }\\r\\n          });\\r\\n      });\\r\\n\\r\\n      var urlParams = App.options.urlParams;\\r\\n      urlParams += urlParams.length ? "&" : "?";\\r\\n      switch({{ url|default:"\\\\"\\\\""}}) {\\r\\n          case "livedin":\\r\\n              App.options.urlParams = urlParams + "tid=gpme000028";\\r\\n              break;\\r\\n          case "paddingtonbear":\\r\\n              App.options.urlParams = urlParams + "tid=gpme000029";\\r\\n              break;\\r\\n          case "presidentsday":\\r\\n              App.options.urlParams = urlParams + "tid=gpme000030";\\r\\n              break;\\r\\n      }\\r\\n    </script>\\r\\n\\r\\n    <!-- Google Tag Manager -->\\r\\n    <noscript><iframe src="//www.googletagmanager.com/ns.html?id=GTM-NQTT"\\r\\n    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\\r\\n    <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({\\\'gtm.start\\\':\\r\\n    new Date().getTime(),event:\\\'gtm.js\\\'});var f=d.getElementsByTagName(s)[0],\\r\\n    j=d.createElement(s),dl=l!=\\\'dataLayer\\\'?\\\'&l=\\\'+l:\\\'\\\';j.async=true;j.src=\\r\\n    \\\'//www.googletagmanager.com/gtm.js?id=\\\'+i+dl;f.parentNode.insertBefore(j,f);\\r\\n    })(window,document,\\\'script\\\',\\\'dataLayer\\\',\\\'GTM-NQTT\\\');</script>\\r\\n    <!-- End Google Tag Manager -->\\r\\n</body>\\r\\n</html>\\r\\n\''}),
            'page_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'store_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        }
    }

    complete_apps = ['assets']