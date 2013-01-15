# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'AnalyticsSection'
        db.delete_table('analytics_analyticssection')

        # Removing M2M table for field categories on 'AnalyticsSection'
        db.delete_table('analytics_analyticssection_categories')

        # Adding model 'Section'
        db.create_table('analytics_section', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('analytics', ['Section'])

        # Adding M2M table for field categories on 'Section'
        db.create_table('analytics_section_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('section', models.ForeignKey(orm['analytics.section'], null=False)),
            ('category', models.ForeignKey(orm['analytics.category'], null=False))
        ))
        db.create_unique('analytics_section_categories', ['section_id', 'category_id'])

        # Adding field 'Metric.enabled'
        db.add_column('analytics_metric', 'enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Category.enabled'
        db.add_column('analytics_category', 'enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'AnalyticsSection'
        db.create_table('analytics_analyticssection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('analytics', ['AnalyticsSection'])

        # Adding M2M table for field categories on 'AnalyticsSection'
        db.create_table('analytics_analyticssection_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('analyticssection', models.ForeignKey(orm['analytics.analyticssection'], null=False)),
            ('category', models.ForeignKey(orm['analytics.category'], null=False))
        ))
        db.create_unique('analytics_analyticssection_categories', ['analyticssection_id', 'category_id'])

        # Deleting model 'Section'
        db.delete_table('analytics_section')

        # Removing M2M table for field categories on 'Section'
        db.delete_table('analytics_section_categories')

        # Deleting field 'Metric.enabled'
        db.delete_column('analytics_metric', 'enabled')

        # Deleting field 'Category.enabled'
        db.delete_column('analytics_category', 'enabled')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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