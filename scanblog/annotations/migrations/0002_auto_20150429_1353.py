# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='comment',
            field=models.ForeignKey(related_name='notes', blank=True, to='comments.Comment', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='note',
            name='creator',
            field=models.ForeignKey(related_name='notes_authored', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
