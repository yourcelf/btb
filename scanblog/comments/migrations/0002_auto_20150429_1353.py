# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
        ('scanning', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='removalreason',
            name='organizations',
            field=models.ManyToManyField(help_text=b'To which organizations will this removal reason be visible?', to='profiles.Organization'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='favorite',
            name='comment',
            field=models.ForeignKey(blank=True, to='comments.Comment', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='favorite',
            name='document',
            field=models.ForeignKey(blank=True, to='scanning.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commentremovalnotificationlog',
            name='comment',
            field=models.OneToOneField(to='comments.Comment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commentremoval',
            name='comment',
            field=models.OneToOneField(to='comments.Comment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commentremoval',
            name='reason',
            field=models.ForeignKey(blank=True, to='comments.RemovalReason', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='comment_doc',
            field=models.OneToOneField(null=True, blank=True, to='scanning.Document'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='document',
            field=models.ForeignKey(related_name='comments', blank=True, to='scanning.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
