# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ListScraper'
        db.create_table('scraper_listscraper', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('classname', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('scraper', ['ListScraper'])

        # Adding model 'DetailScraper'
        db.create_table('scraper_detailscraper', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('classname', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('scraper', ['DetailScraper'])

        # Adding model 'StoreScraper'
        db.create_table('scraper_storescraper', (
            ('store', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['assets.Store'], unique=True, primary_key=True)),
            ('list_url', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('list_scraper', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scraper.ListScraper'])),
            ('detail_scraper', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scraper.DetailScraper'])),
            ('scrape_interval', self.gf('django.db.models.fields.IntegerField')()),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0, null=True, blank=True)),
        ))
        db.send_create_signal('scraper', ['StoreScraper'])

        # Adding model 'SitemapListScraper'
        db.create_table('scraper_sitemaplistscraper', (
            ('listscraper_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scraper.ListScraper'], unique=True, primary_key=True)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('scraper', ['SitemapListScraper'])

        # Adding model 'PythonListScraper'
        db.create_table('scraper_pythonlistscraper', (
            ('listscraper_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scraper.ListScraper'], unique=True, primary_key=True)),
            ('script', self.gf('django.db.models.fields.TextField')()),
            ('enable_javascript', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enable_css', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('scraper', ['PythonListScraper'])

        # Adding model 'PythonDetailScraper'
        db.create_table('scraper_pythondetailscraper', (
            ('detailscraper_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scraper.DetailScraper'], unique=True, primary_key=True)),
            ('script', self.gf('django.db.models.fields.TextField')()),
            ('enable_javascript', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('enable_css', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('scraper', ['PythonDetailScraper'])

        # Adding model 'ProductSuggestion'
        db.create_table('scraper_productsuggestion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='suggestions', to=orm['assets.Product'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=500)),
            ('suggested', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='suggested', null=True, to=orm['assets.Product'])),
        ))
        db.send_create_signal('scraper', ['ProductSuggestion'])


    def backwards(self, orm):
        # Deleting model 'ListScraper'
        db.delete_table('scraper_listscraper')

        # Deleting model 'DetailScraper'
        db.delete_table('scraper_detailscraper')

        # Deleting model 'StoreScraper'
        db.delete_table('scraper_storescraper')

        # Deleting model 'SitemapListScraper'
        db.delete_table('scraper_sitemaplistscraper')

        # Deleting model 'PythonListScraper'
        db.delete_table('scraper_pythonlistscraper')

        # Deleting model 'PythonDetailScraper'
        db.delete_table('scraper_pythondetailscraper')

        # Deleting model 'ProductSuggestion'
        db.delete_table('scraper_productsuggestion')


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
        'scraper.productsuggestion': {
            'Meta': {'object_name': 'ProductSuggestion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestions'", 'to': "orm['assets.Product']"}),
            'suggested': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'suggested'", 'null': 'True', 'to': "orm['assets.Product']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '500'})
        },
        'scraper.pythondetailscraper': {
            'Meta': {'object_name': 'PythonDetailScraper', '_ormbases': ['scraper.DetailScraper']},
            'detailscraper_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scraper.DetailScraper']", 'unique': 'True', 'primary_key': 'True'}),
            'enable_css': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_javascript': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'script': ('django.db.models.fields.TextField', [], {})
        },
        'scraper.pythonlistscraper': {
            'Meta': {'object_name': 'PythonListScraper', '_ormbases': ['scraper.ListScraper']},
            'enable_css': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_javascript': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['assets.Store']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['scraper']