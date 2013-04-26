# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'HelpTopic'
        db.create_table('help_helptopic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('contents', self.gf('django.db.models.fields.TextField')()),
            ('parent_topic', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='sub_topics', null=True, to=orm['help.HelpTopic'])),
        ))
        db.send_create_signal('help', ['HelpTopic'])


    def backwards(self, orm):
        
        # Deleting model 'HelpTopic'
        db.delete_table('help_helptopic')


    models = {
        'help.helptopic': {
            'Meta': {'object_name': 'HelpTopic'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'contents': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_topic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sub_topics'", 'null': 'True', 'to': "orm['help.HelpTopic']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['help']
