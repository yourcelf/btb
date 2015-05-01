# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resolved', models.DateTimeField(null=True, blank=True)),
                ('important', models.BooleanField(default=False)),
                ('text', models.TextField()),
                ('modified', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['-important', '-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReplyCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=16, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=30, db_index=True)),
                ('post_count', models.IntegerField(default=0, help_text=b'Denormalized count of posts with this tag.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
