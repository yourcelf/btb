# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanning', '0002_auto_20150429_1721'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='comments_disabled',
            field=models.BooleanField(default=False),
        ),
    ]
