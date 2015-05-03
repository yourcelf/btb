# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('correspondence', '0002_auto_20150429_1353'),
    ]

    operations = [
        migrations.AlterField(
            model_name='letter',
            name='comments',
            field=models.ManyToManyField(to='comments.Comment', blank=True),
        ),
        migrations.AlterField(
            model_name='mailing',
            name='letters',
            field=models.ManyToManyField(to='correspondence.Letter', blank=True),
        ),
    ]
