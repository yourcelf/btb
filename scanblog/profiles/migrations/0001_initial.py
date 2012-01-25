# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Profile'
        db.create_table('profiles_profile', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('show_adult_content', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('in_prison', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('blog_name', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('mailing_address', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('special_mail_handling', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('consent_form_received', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('profiles', ['Profile'])

        # Adding model 'Organization'
        db.create_table('profiles_organization', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('personal_contact', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mailing_address', self.gf('django.db.models.fields.TextField')()),
            ('outgoing_mail_handled_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['profiles.Organization'], null=True, blank=True)),
            ('about', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('footer', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('profiles', ['Organization'])

        # Adding M2M table for field members on 'Organization'
        db.create_table('profiles_organization_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['profiles.organization'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('profiles_organization_members', ['organization_id', 'user_id'])

        # Adding M2M table for field moderators on 'Organization'
        db.create_table('profiles_organization_moderators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['profiles.organization'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('profiles_organization_moderators', ['organization_id', 'user_id'])


    def backwards(self, orm):
        
        # Deleting model 'Profile'
        db.delete_table('profiles_profile')

        # Deleting model 'Organization'
        db.delete_table('profiles_organization')

        # Removing M2M table for field members on 'Organization'
        db.delete_table('profiles_organization_members')

        # Removing M2M table for field moderators on 'Organization'
        db.delete_table('profiles_organization_moderators')


    models = {
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
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations_moderated'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'outgoing_mail_handled_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['profiles.Organization']", 'null': 'True', 'blank': 'True'}),
            'personal_contact': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'profiles.profile': {
            'Meta': {'object_name': 'Profile'},
            'blog_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'consent_form_received': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'in_prison': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mailing_address': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'show_adult_content': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'special_mail_handling': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['profiles']
