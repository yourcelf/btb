# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255)),
                ('body', models.TextField()),
                ('public', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(blank=True)),
                ('ended', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
    ]
