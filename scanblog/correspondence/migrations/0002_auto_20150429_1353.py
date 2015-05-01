# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
        ('correspondence', '0001_initial'),
        ('scanning', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='document',
            field=models.ForeignKey(blank=True, to='scanning.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='letter',
            name='org',
            field=models.ForeignKey(blank=True, to='profiles.Organization', help_text=b'Organization for the return address for this letter', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='letter',
            name='recipient',
            field=models.ForeignKey(related_name='received_letters', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='letter',
            name='sender',
            field=models.ForeignKey(related_name='authored_letters', blank=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
