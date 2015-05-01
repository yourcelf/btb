# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Letter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(blank=True)),
                ('is_postcard', models.BooleanField(default=False)),
                ('send_anonymously', models.BooleanField(default=False)),
                ('type', models.CharField(max_length=255, choices=[(b'letter', b'letter'), (b'consent_form', b'consent_form'), (b'signup_complete', b'signup_complete'), (b'first_post', b'first_post'), (b'printout', b'printout'), (b'comments', b'comments'), (b'waitlist', b'waitlist'), (b'returned_original', b'returned_original'), (b'refused_original', b'refused_original')])),
                ('auto_generated', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('sent', models.DateTimeField(null=True)),
                ('file', models.FileField(upload_to=b'tmp', blank=True)),
                ('recipient_address', models.TextField(default=b'', help_text=b'Legacy for old content.  No longer used.', blank=True)),
                ('comments', models.ManyToManyField(to='comments.Comment', null=True, blank=True)),
            ],
            options={
                'ordering': ['recipient', 'created'],
                'permissions': (('manage_correspondence', 'Manage correspondence'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Mailing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_finished', models.DateTimeField(null=True, blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to=b'tmp', blank=True)),
                ('editor', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('letters', models.ManyToManyField(to='correspondence.Letter', null=True, blank=True)),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-modified'],
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
    ]
