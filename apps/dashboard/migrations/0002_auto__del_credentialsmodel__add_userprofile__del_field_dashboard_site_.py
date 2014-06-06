# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'CredentialsModel'
        db.delete_table(u'dashboard_credentialsmodel')

        # Adding model 'UserProfile'
        db.create_table(u'dashboard_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal(u'dashboard', ['UserProfile'])

        # Adding M2M table for field dashboards on 'UserProfile'
        m2m_table_name = db.shorten_name(u'dashboard_userprofile_dashboards')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm[u'dashboard.userprofile'], null=False)),
            ('dashboard', models.ForeignKey(orm[u'dashboard.dashboard'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userprofile_id', 'dashboard_id'])

        # Deleting field 'DashBoard.site'
        db.delete_column(u'dashboard_dashboard', 'site')

        # Adding field 'DashBoard.site_name'
        db.add_column(u'dashboard_dashboard', 'site_name',
                      self.gf('django.db.models.fields.CharField')(default='site', max_length=128),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'CredentialsModel'
        db.create_table(u'dashboard_credentialsmodel', (
            ('credential', self.gf('oauth2client.django_orm.CredentialsField')(null=True)),
            ('id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], primary_key=True)),
        ))
        db.send_create_signal(u'dashboard', ['CredentialsModel'])

        # Deleting model 'UserProfile'
        db.delete_table(u'dashboard_userprofile')

        # Removing M2M table for field dashboards on 'UserProfile'
        db.delete_table(db.shorten_name(u'dashboard_userprofile_dashboards'))


        # User chose to not deal with backwards NULL issues for 'DashBoard.site'
        raise RuntimeError("Cannot reverse this migration. 'DashBoard.site' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'DashBoard.site'
        db.add_column(u'dashboard_dashboard', 'site',
                      self.gf('django.db.models.fields.CharField')(max_length=128),
                      keep_default=False)

        # Deleting field 'DashBoard.site_name'
        db.delete_column(u'dashboard_dashboard', 'site_name')


    models = {
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
        u'dashboard.dashboard': {
            'Meta': {'object_name': 'DashBoard'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quicklook_today': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'quicklook_total': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'site_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'table_id': ('django.db.models.fields.IntegerField', [], {}),
            'timeStamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dashboard.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'dashboards': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['dashboard.DashBoard']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['dashboard']