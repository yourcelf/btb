# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PendingScan'
        db.create_table('scanning_pendingscan', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pending_scans_edited', to=orm['auth.User'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pending_scans_authored', to=orm['auth.User'])),
            ('scan', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scanning.Scan'], unique=True, null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('completed', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('scanning', ['PendingScan'])

        # Adding model 'Scan'
        db.create_table('scanning_scan', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pdf', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='scans_authored', null=True, to=orm['auth.User'])),
            ('uploader', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scans_uploaded', to=orm['auth.User'])),
            ('processing_complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('received', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('under_construction', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('scanning', ['Scan'])

        # Adding model 'ScanPage'
        db.create_table('scanning_scanpage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.Scan'])),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
        ))
        db.send_create_signal('scanning', ['ScanPage'])

        # Adding unique constraint on 'ScanPage', fields ['order', 'scan']
        db.create_unique('scanning_scanpage', ['order', 'scan_id'])

        # Adding model 'Document'
        db.create_table('scanning_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.Scan'], null=True, blank=True)),
            ('pdf', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('in_reply_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='document_replies', null=True, to=orm['annotations.ReplyCode'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documents_authored', to=orm['auth.User'])),
            ('date_written', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('highlight', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('highlight_transform', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('under_construction', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('status', self.gf('django.db.models.fields.CharField')(default='unknown', max_length=20, db_index=True)),
            ('adult', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('reply_code', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['annotations.ReplyCode'], unique=True)),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documents_edited', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('scanning', ['Document'])

        # Adding M2M table for field tags on 'Document'
        db.create_table('scanning_document_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('document', models.ForeignKey(orm['scanning.document'], null=False)),
            ('tag', models.ForeignKey(orm['annotations.tag'], null=False))
        ))
        db.create_unique('scanning_document_tags', ['document_id', 'tag_id'])

        # Adding model 'DocumentPage'
        db.create_table('scanning_documentpage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.Document'])),
            ('scan_page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.ScanPage'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=255, null=True, blank=True)),
            ('transformations', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('scanning', ['DocumentPage'])

        # Adding unique constraint on 'DocumentPage', fields ['order', 'document']
        db.create_unique('scanning_documentpage', ['order', 'document_id'])

        # Adding model 'Transcription'
        db.create_table('scanning_transcription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scanning.Document'], unique=True)),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('scanning', ['Transcription'])

        # Adding model 'TranscriptionRevision'
        db.create_table('scanning_transcriptionrevision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('transcription', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['scanning.Transcription'])),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('scanning', ['TranscriptionRevision'])

        # Adding unique constraint on 'TranscriptionRevision', fields ['transcription', 'revision']
        db.create_unique('scanning_transcriptionrevision', ['transcription_id', 'revision'])

        # Adding model 'EditLock'
        db.create_table('scanning_editlock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.Scan'], null=True, blank=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scanning.Document'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('scanning', ['EditLock'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TranscriptionRevision', fields ['transcription', 'revision']
        db.delete_unique('scanning_transcriptionrevision', ['transcription_id', 'revision'])

        # Removing unique constraint on 'DocumentPage', fields ['order', 'document']
        db.delete_unique('scanning_documentpage', ['order', 'document_id'])

        # Removing unique constraint on 'ScanPage', fields ['order', 'scan']
        db.delete_unique('scanning_scanpage', ['order', 'scan_id'])

        # Deleting model 'PendingScan'
        db.delete_table('scanning_pendingscan')

        # Deleting model 'Scan'
        db.delete_table('scanning_scan')

        # Deleting model 'ScanPage'
        db.delete_table('scanning_scanpage')

        # Deleting model 'Document'
        db.delete_table('scanning_document')

        # Removing M2M table for field tags on 'Document'
        db.delete_table('scanning_document_tags')

        # Deleting model 'DocumentPage'
        db.delete_table('scanning_documentpage')

        # Deleting model 'Transcription'
        db.delete_table('scanning_transcription')

        # Deleting model 'TranscriptionRevision'
        db.delete_table('scanning_transcriptionrevision')

        # Deleting model 'EditLock'
        db.delete_table('scanning_editlock')


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
        'scanning.documentpage': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('order', 'document'),)", 'object_name': 'DocumentPage'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'scan_page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.ScanPage']"}),
            'transformations': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'scanning.editlock': {
            'Meta': {'object_name': 'EditLock'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.Document']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.Scan']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'scanning.pendingscan': {
            'Meta': {'ordering': "['-created']", 'object_name': 'PendingScan'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pending_scans_authored'", 'to': "orm['auth.User']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pending_scans_edited'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'scan': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scanning.Scan']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'scanning.scan': {
            'Meta': {'ordering': "['created']", 'object_name': 'Scan'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scans_authored'", 'null': 'True', 'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pdf': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'processing_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'received': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'under_construction': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scans_uploaded'", 'to': "orm['auth.User']"})
        },
        'scanning.scanpage': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('order', 'scan'),)", 'object_name': 'ScanPage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'scan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scanning.Scan']"})
        },
        'scanning.transcription': {
            'Meta': {'object_name': 'Transcription'},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'document': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scanning.Document']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'scanning.transcriptionrevision': {
            'Meta': {'ordering': "['-revision']", 'unique_together': "[('transcription', 'revision')]", 'object_name': 'TranscriptionRevision'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'transcription': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['scanning.Transcription']"})
        }
    }

    complete_apps = ['scanning']
