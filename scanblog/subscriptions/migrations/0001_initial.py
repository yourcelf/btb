# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Subscription'
        db.create_table('subscriptions_subscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscriptions', to=orm['auth.User'])),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='subscriptions', null=True, to=orm['scanning.Document'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='author_subscriptions', null=True, to=orm['auth.User'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='tag_subscriptions', null=True, to=orm['annotations.Tag'])),
        ))
        db.send_create_signal('subscriptions', ['Subscription'])

        # Adding model 'DocumentNotificationLog'
        db.create_table('subscriptions_documentnotificationlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.Document'])),
        ))
        db.send_create_signal('subscriptions', ['DocumentNotificationLog'])

        # Adding model 'NotificationBlacklist'
        db.create_table('subscriptions_notificationblacklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal('subscriptions', ['NotificationBlacklist'])


    def backwards(self, orm):
        
        # Deleting model 'Subscription'
        db.delete_table('subscriptions_subscription')

        # Deleting model 'DocumentNotificationLog'
        db.delete_table('subscriptions_documentnotificationlog')

        # Deleting model 'NotificationBlacklist'
        db.delete_table('subscriptions_notificationblacklist')


    models = {
        'annotations.replycode': {
            'Meta': {'object_name': 'ReplyCode'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '16', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'annotations.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'})
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
        'profiles.organization': {
            'Meta': {'object_name': 'Organization'},
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'footer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_address': ('django.db.models.fields.TextField', [], {}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations_moderated'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'outgoing_mail_handled_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profiles.Organization']", 'null': 'True', 'blank': 'True'}),
            'personal_contact': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'scanning.document': {
            'Meta': {'ordering': "['-date_written']", 'object_name': 'Document'},
            'adult': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documents_authored'", 'to': "orm['auth.User']"}),
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_written': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documents_edited'", 'to': "orm['auth.User']"}),
            'highlight': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'highlight_transform': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'document_replies'", 'null': 'True', 'to': "orm['annotations.ReplyCode']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pdf': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'reply_code': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['annotations.ReplyCode']", 'unique': 'True'}),
            'scan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.Scan']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'unknown'", 'max_length': '20', 'db_index': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['annotations.Tag']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'under_construction': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'scanning.scan': {
            'Meta': {'ordering': "['created']", 'object_name': 'Scan'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scans_authored'", 'null': 'True', 'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profiles.Organization']", 'null': 'True'}),
            'pdf': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'processing_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'under_construction': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scans_uploaded'", 'to': "orm['auth.User']"})
        },
        'subscriptions.documentnotificationlog': {
            'Meta': {'object_name': 'DocumentNotificationLog'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'subscriptions.notificationblacklist': {
            'Meta': {'object_name': 'NotificationBlacklist'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'subscriptions.subscription': {
            'Meta': {'ordering': "['tag', 'author', 'document']", 'object_name': 'Subscription'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'author_subscriptions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subscriptions'", 'null': 'True', 'to': "orm['scanning.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscriptions'", 'to': "orm['auth.User']"}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tag_subscriptions'", 'null': 'True', 'to': "orm['annotations.Tag']"})
        }
    }

    complete_apps = ['subscriptions']
