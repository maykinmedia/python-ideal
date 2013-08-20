# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Issuer'
        db.create_table(u'ideal_compat_issuer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=11)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=250, db_index=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'ideal_compat', ['Issuer'])


    def backwards(self, orm):
        # Deleting model 'Issuer'
        db.delete_table(u'ideal_compat_issuer')


    models = {
        u'ideal_compat.issuer': {
            'Meta': {'object_name': 'Issuer'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '11'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '250', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '35'})
        }
    }

    complete_apps = ['ideal_compat']