# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20150429_1353'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comments', '0001_initial'),
        ('campaigns', '0001_initial'),
        ('profiles', '0001_initial'),
        ('scanning', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentNotificationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.ForeignKey(to='comments.Comment')),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentNotificationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document', models.ForeignKey(to='scanning.Document')),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailingListInterest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('volunteering', models.BooleanField(default=False, help_text=b'Are you interested in volunteering?')),
                ('allies', models.BooleanField(default=False, help_text=b'Are you interested in joining with Between the Bars in campaigns?')),
                ('announcements', models.BooleanField(default=False, help_text=b'Are you interested in announcements about new projects and features?')),
                ('details', models.TextField(help_text=b'Tell us more about your interests, if you like.', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NotificationBlacklist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('affiliation', models.ForeignKey(related_name='affiliation_subscriptions', blank=True, to='profiles.Affiliation', null=True)),
                ('author', models.ForeignKey(related_name='author_subscriptions', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('campaign', models.ForeignKey(related_name='organization_subscriptions', blank=True, to='campaigns.Campaign', null=True)),
                ('document', models.ForeignKey(related_name='subscriptions', blank=True, to='scanning.Document', null=True)),
                ('organization', models.ForeignKey(related_name='organization_subscriptions', blank=True, to='profiles.Organization', null=True)),
                ('subscriber', models.ForeignKey(related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
                ('tag', models.ForeignKey(related_name='tag_subscriptions', blank=True, to='annotations.Tag', null=True)),
            ],
            options={
                'ordering': ['tag', 'author', 'document', 'campaign', 'affiliation'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserNotificationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
            },
            bases=(models.Model,),
        ),
    ]
