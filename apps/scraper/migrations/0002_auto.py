# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'StoreScraper.id'
        db.delete_column('scraper_storescraper', 'id')


        # Changing field 'StoreScraper.store'
        db.alter_column('scraper_storescraper', 'store_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Store'], unique=True, primary_key=True))
        # Adding unique constraint on 'StoreScraper', fields ['store']
        db.create_unique('scraper_storescraper', ['store_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'StoreScraper', fields ['store']
        db.delete_unique('scraper_storescraper', ['store_id'])

        # Adding field 'StoreScraper.id'
        db.add_column('scraper_storescraper', 'id',
                      self.gf('django.db.models.fields.AutoField')(default=1, primary_key=True),
                      keep_default=False)


        # Changing field 'StoreScraper.store'
        db.alter_column('scraper_storescraper', 'store_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['assets.Store']))

    models = {
        'assets.store': {
            'Meta': {'object_name': 'Store'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
        'scraper.detailscraper': {
            'Meta': {'object_name': 'DetailScraper'},
            'classname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'scraper.listscraper': {
            'Meta': {'object_name': 'ListScraper'},
            'classname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'scraper.pythondetailscraper': {
            'Meta': {'object_name': 'PythonDetailScraper', '_ormbases': ['scraper.DetailScraper']},
            'detailscraper_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scraper.DetailScraper']", 'unique': 'True', 'primary_key': 'True'}),
            'script': ('django.db.models.fields.TextField', [], {})
        },
        'scraper.pythonlistscraper': {
            'Meta': {'object_name': 'PythonListScraper', '_ormbases': ['scraper.ListScraper']},
            'listscraper_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scraper.ListScraper']", 'unique': 'True', 'primary_key': 'True'}),
            'script': ('django.db.models.fields.TextField', [], {})
        },
        'scraper.sitemaplistscraper': {
            'Meta': {'object_name': 'SitemapListScraper', '_ormbases': ['scraper.ListScraper']},
            'listscraper_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scraper.ListScraper']", 'unique': 'True', 'primary_key': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'scraper.storescraper': {
            'Meta': {'object_name': 'StoreScraper'},
            'detail_scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.DetailScraper']"}),
            'list_scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.ListScraper']"}),
            'list_url': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'scrape_interval': ('django.db.models.fields.IntegerField', [], {}),
            'store': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['assets.Store']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['scraper']