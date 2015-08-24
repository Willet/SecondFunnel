# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Tile.reviewed'
        db.add_column(u'assets_tile', 'reviewed',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=True)

        # Adding field 'Tile.in_stock'
        db.add_column(u'assets_tile', 'in_stock',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=True)


    def backwards(self, orm):
        # Deleting field 'Tile.reviewed'
        db.delete_column(u'assets_tile', 'reviewed')

        # Deleting field 'Tile.in_stock'
        db.delete_column(u'assets_tile', 'in_stock')


    models = {
        u'assets.category': {
            'Meta': {'object_name': 'Category'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categories'", 'to': u"orm['assets.Store']"}),
            'tiles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categories'", 'symmetrical': 'False', 'to': u"orm['assets.Tile']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'assets.content': {
            'Meta': {'object_name': 'Content'},
            'attributes': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'source_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'needs-review'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content'", 'to': u"orm['assets.Store']"}),
            'tagged_products': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'content'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['assets.Product']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'assets.feed': {
            'Meta': {'object_name': 'Feed'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed_algorithm': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'feed_ratio': ('django.db.models.fields.DecimalField', [], {'default': '0.2', 'max_digits': '2', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_finite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_urls': ('apps.utils.fields.ListField', [], {'blank': 'True'}),
            'spider_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'feeds'", 'to': u"orm['assets.Store']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'assets.gif': {
            'Meta': {'object_name': 'Gif', '_ormbases': [u'assets.Image']},
            'gif_url': ('django.db.models.fields.TextField', [], {}),
            u'image_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['assets.Image']", 'unique': 'True', 'primary_key': 'True'})
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
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dashboard.Campaign']", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'dashboard_settings': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'page'", 'null': 'True', 'to': u"orm['assets.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'last_published_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'legal_copy': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['assets.Store']"}),
            'theme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pages'", 'null': 'True', 'to': u"orm['assets.Theme']"}),
            'theme_settings': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'assets.product': {
            'Meta': {'object_name': 'Product'},
            'attributes': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'$'", 'max_length': '5'}),
            'default_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'default_image'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['assets.ProductImage']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_stock': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'last_scraped_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'sale_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'similar_products': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'reverse_similar_products'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['assets.Product']"}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['assets.Store']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        u'assets.productimage': {
            'Meta': {'ordering': "('id',)", 'object_name': 'ProductImage'},
            'attributes': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'dominant_color': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'file_checksum': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'original_url': ('django.db.models.fields.TextField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'product_images'", 'null': 'True', 'blank': 'True', 'to': u"orm['assets.Product']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
            'default_page': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'default_store'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['assets.Page']"}),
            'default_theme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'store'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['assets.Theme']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'public_base_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'staff': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'stores'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'assets.tag': {
            'Meta': {'object_name': 'Tag'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'tags'", 'symmetrical': 'False', 'to': u"orm['assets.Product']"}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['assets.Store']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'assets.theme': {
            'Meta': {'object_name': 'Theme'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'default': "'apps/pinpoint/templates/pinpoint/campaign_base.html'", 'max_length': '1024'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'assets.tile': {
            'Meta': {'object_name': 'Tile'},
            'attributes': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'clicks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tiles'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['assets.Content']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tiles'", 'to': u"orm['assets.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_stock': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'ir_cache': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'tiles'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['assets.Product']"}),
            'reviewed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'views': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
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
        },
        u'dashboard.campaign': {
            'Meta': {'object_name': 'Campaign'},
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['assets']