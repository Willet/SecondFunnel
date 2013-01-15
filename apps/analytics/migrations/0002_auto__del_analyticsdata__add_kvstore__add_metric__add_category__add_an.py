# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'AnalyticsData'
        db.delete_table('analytics_analyticsdata')

        # Adding model 'KVStore'
        db.create_table('analytics_kvstore', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('analytics', ['KVStore'])

        # Adding model 'Metric'
        db.create_table('analytics_metric', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('analytics', ['Metric'])

        # Adding M2M table for field data on 'Metric'
        db.create_table('analytics_metric_data', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metric', models.ForeignKey(orm['analytics.metric'], null=False)),
            ('kvstore', models.ForeignKey(orm['analytics.kvstore'], null=False))
        ))
        db.create_unique('analytics_metric_data', ['metric_id', 'kvstore_id'])

        # Adding model 'Category'
        db.create_table('analytics_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('analytics', ['Category'])

        # Adding M2M table for field metrics on 'Category'
        db.create_table('analytics_category_metrics', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('category', models.ForeignKey(orm['analytics.category'], null=False)),
            ('metric', models.ForeignKey(orm['analytics.metric'], null=False))
        ))
        db.create_unique('analytics_category_metrics', ['category_id', 'metric_id'])

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


    def backwards(self, orm):
        # Adding model 'AnalyticsData'
        db.create_table('analytics_analyticsdata', (
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('analytics', ['AnalyticsData'])

        # Deleting model 'KVStore'
        db.delete_table('analytics_kvstore')

        # Deleting model 'Metric'
        db.delete_table('analytics_metric')

        # Removing M2M table for field data on 'Metric'
        db.delete_table('analytics_metric_data')

        # Deleting model 'Category'
        db.delete_table('analytics_category')

        # Removing M2M table for field metrics on 'Category'
        db.delete_table('analytics_category_metrics')

        # Deleting model 'AnalyticsSection'
        db.delete_table('analytics_analyticssection')

        # Removing M2M table for field categories on 'AnalyticsSection'
        db.delete_table('analytics_analyticssection_categories')


    models = {
        'analytics.analyticsrecency': {
            'Meta': {'object_name': 'AnalyticsRecency'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'analytics.analyticssection': {
            'Meta': {'object_name': 'AnalyticsSection'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['analytics.Category']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'analytics.category': {
            'Meta': {'object_name': 'Category'},
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