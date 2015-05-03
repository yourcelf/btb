# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20150429_1353'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pdf', models.FileField(upload_to=b'uploads/tmp', blank=True)),
                ('body', models.TextField(blank=True)),
                ('type', models.CharField(max_length=25, choices=[(b'license', b'license'), (b'photo', b'photo'), (b'post', b'post'), (b'profile', b'profile'), (b'request', b'request')])),
                ('title', models.CharField(max_length=255, blank=True)),
                ('date_written', models.DateTimeField(null=True)),
                ('highlight', models.ImageField(upload_to=b'uploads/tmp', blank=True)),
                ('highlight_transform', models.TextField(blank=True)),
                ('under_construction', models.BooleanField(default=False, help_text=b"Deprecated, don't use.  Use status instead.")),
                ('status', models.CharField(default=b'unknown', max_length=20, db_index=True, choices=[(b'unknown', b'Needs attention'), (b'ready', b'Ready to publish'), (b'published', b'Published'), (b'unpublishable', b"Can't be published")])),
                ('adult', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(default=datetime.datetime.now)),
                ('affiliation', models.ForeignKey(blank=True, to='profiles.Affiliation', null=True)),
                ('author', models.ForeignKey(related_name='documents_authored', to=settings.AUTH_USER_MODEL)),
                ('editor', models.ForeignKey(related_name='documents_edited', to=settings.AUTH_USER_MODEL, help_text=b'The last person to edit this document.')),
                ('in_reply_to', models.ForeignKey(related_name='document_replies', blank=True, to='annotations.ReplyCode', null=True)),
                ('reply_code', models.OneToOneField(to='annotations.ReplyCode')),
            ],
            options={
                'ordering': ['-date_written'],
                'permissions': (('tag_post', 'Tag posts'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('image', models.ImageField(max_length=255, null=True, upload_to=b'uploads/tmp', blank=True)),
                ('transformations', models.TextField(help_text=b'Serialized description of transformations that change the original scan_page image to the image for this document.', blank=True)),
                ('document', models.ForeignKey(to='scanning.Document')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EditLock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('document', models.ForeignKey(blank=True, to='scanning.Document', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PendingScan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=12)),
                ('completed', models.DateTimeField(null=True, blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(related_name='pending_scans_authored', to=settings.AUTH_USER_MODEL)),
                ('editor', models.ForeignKey(related_name='pending_scans_edited', to=settings.AUTH_USER_MODEL)),
                ('org', models.ForeignKey(to='profiles.Organization', null=True)),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pdf', models.FileField(upload_to=b'uploads/tmp', blank=True)),
                ('processing_complete', models.BooleanField(default=False)),
                ('under_construction', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(default=datetime.datetime.now)),
                ('source_id', models.CharField(max_length=100, blank=True)),
                ('author', models.ForeignKey(related_name='scans_authored', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('org', models.ForeignKey(to='profiles.Organization', null=True)),
                ('uploader', models.ForeignKey(related_name='scans_uploaded', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created'],
                'permissions': (('view_raw_scans', 'View raw scans'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ScanPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('image', models.ImageField(upload_to=b'uploads/tmp')),
                ('scan', models.ForeignKey(to='scanning.Scan')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transcription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('complete', models.BooleanField(default=False, help_text='Check if transcription is complete')),
                ('locked', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('document', models.OneToOneField(to='scanning.Document')),
            ],
            options={
                'permissions': (('lock_transcription', 'Lock transcription'), ('change_locked_transcription', 'Change locked transcriptions')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TranscriptionRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('revision', models.IntegerField(default=0)),
                ('body', models.TextField()),
                ('modified', models.DateTimeField(default=datetime.datetime.now)),
                ('editor', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('transcription', models.ForeignKey(related_name='revisions', to='scanning.Transcription')),
            ],
            options={
                'ordering': ['-revision'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='transcriptionrevision',
            unique_together=set([('transcription', 'revision')]),
        ),
        migrations.AlterUniqueTogether(
            name='scanpage',
            unique_together=set([('order', 'scan')]),
        ),
        migrations.AddField(
            model_name='pendingscan',
            name='scan',
            field=models.OneToOneField(null=True, blank=True, to='scanning.Scan'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='editlock',
            name='scan',
            field=models.ForeignKey(blank=True, to='scanning.Scan', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='editlock',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='documentpage',
            name='scan_page',
            field=models.ForeignKey(to='scanning.ScanPage'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='documentpage',
            unique_together=set([('order', 'document')]),
        ),
        migrations.AddField(
            model_name='document',
            name='scan',
            field=models.ForeignKey(blank=True, to='scanning.Scan', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='tags',
            field=models.ManyToManyField(to='annotations.Tag', null=True, blank=True),
            preserve_default=True,
        ),
    ]
