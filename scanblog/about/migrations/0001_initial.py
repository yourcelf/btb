# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SiteBanner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('html', models.TextField(verbose_name=b'HTML')),
                ('start_date', models.DateTimeField(default=datetime.datetime.now)),
                ('end_date', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'ordering': ['-start_date'],
            },
            bases=(models.Model,),
        ),
    ]
