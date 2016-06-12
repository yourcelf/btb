# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_auto_20150902_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationprofile',
            name='activated',
            field=models.BooleanField(default=False),
        ),
    ]
