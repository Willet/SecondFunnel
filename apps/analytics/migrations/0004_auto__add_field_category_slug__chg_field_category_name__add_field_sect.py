# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Category.slug'
        db.add_column('analytics_category', 'slug',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)


        # Changing field 'Category.name'
        db.alter_column('analytics_category', 'name', self.gf('django.db.models.fields.CharField')(max_length=255))
        # Adding field 'Section.slug'
        db.add_column('analytics_section', 'slug',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)


        # Changing field 'Section.name'
        db.alter_column('analytics_section', 'name', self.gf('django.db.models.fields.CharField')(max_length=255))

    def backwards(self, orm):
        # Deleting field 'Category.slug'
        db.delete_column('analytics_category', 'slug')


        # Changing field 'Category.name'
        db.alter_column('analytics_category', 'name', self.gf('django.db.models.fields.CharField')(max_length=100))
        # Deleting field 'Section.slug'
        db.delete_column('analytics_section', 'slug')


        # Changing field 'Section.name'
        db.alter_column('analytics_section', 'name', self.gf('django.db.models.fields.CharField')(max_length=100))

    models = {
        'analytics.analyticsrecency': {
            'Meta': {'object_name': 'AnalyticsRecency'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'analytics.category': {
            'Meta': {'object_name': 'Category'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metrics': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['analytics.Metric']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'analytics.kvstore': {
            'Meta': {'object_name': 'KVStore'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'analytics.metric': {
            'Meta': {'object_name': 'Metric'},
            'data': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'data'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['analytics.KVStore']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'analytics.section': {
            'Meta': {'object_name': 'Section'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['analytics.Category']", 'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['analytics']