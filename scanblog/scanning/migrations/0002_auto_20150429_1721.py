# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scanning', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='tags',
            field=models.ManyToManyField(to='annotations.Tag', blank=True),
        ),
    ]
