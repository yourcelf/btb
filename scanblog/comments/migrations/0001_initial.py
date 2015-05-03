# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(default=datetime.datetime.now)),
                ('comment', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('removed', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommentRemoval',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('web_message', models.TextField(blank=True)),
                ('comment_author_message', models.TextField(blank=True)),
                ('post_author_message', models.TextField(blank=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommentRemovalNotificationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RemovalReason',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('default_web_message', models.TextField(help_text=b'Default message to display in place of the removed comment. If blank, no web message will be left.', blank=True)),
                ('default_comment_author_message', models.TextField(help_text=b"Default message to send to commenters, if any. If blank, commenters won't be notified.", blank=True)),
                ('default_post_author_message', models.TextField(help_text=b"Default message to send to post authors, if any. If blank, post authors won't be notified.", blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
