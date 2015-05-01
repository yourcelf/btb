# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20150429_1353'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scanning', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='document',
            field=models.ForeignKey(related_name='notes', blank=True, to='scanning.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='note',
            name='scan',
            field=models.ForeignKey(related_name='notes', blank=True, to='scanning.Scan', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='note',
            name='user',
            field=models.ForeignKey(related_name='notes', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
