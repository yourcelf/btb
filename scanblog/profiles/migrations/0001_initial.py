# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Affiliation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(help_text=b'Use this to identify this affiliation when editing documents.', unique=True, max_length=255)),
                ('logo', models.ImageField(null=True, upload_to=b'public/uploads/affiliations/', blank=True)),
                ('list_body', models.TextField(help_text=b'HTML for the top of the group page.')),
                ('detail_body', models.TextField(help_text=b'HTML to append to individual posts for this group.')),
                ('public', models.BooleanField(default=False, help_text=b"If false, the affiliation won't be listed publicly.")),
                ('order', models.IntegerField(default=0, help_text=b'Use to set the order for the list of affiliations on the categories view. Lower numbers come first.')),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('modified', models.DateTimeField(blank=True)),
            ],
            options={
                'ordering': ['order', '-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('personal_contact', models.CharField(max_length=255, blank=True)),
                ('public', models.BooleanField(default=False, help_text=b"Check to make this organization appear in the 'Groups' tab")),
                ('custom_intro_packet', models.FileField(help_text=b'Leave blank to use the default packet, formatted with your address.', null=True, upload_to=b'uploads/org_intro_packets', blank=True)),
                ('mailing_address', models.TextField()),
                ('about', models.TextField(help_text=b'Main text that will appear on the groups page.', blank=True)),
                ('footer', models.TextField(help_text=b'Additional text that will appear at the bottom of each post by a member of this organization.', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('display_name', models.CharField(max_length=50)),
                ('show_adult_content', models.BooleanField(default=False, help_text='Show posts and comments that have been marked as adult?')),
                ('blogger', models.BooleanField(default=False)),
                ('managed', models.BooleanField(default=False)),
                ('lost_contact', models.BooleanField(default=False)),
                ('blog_name', models.CharField(default=b'', max_length=255, blank=True)),
                ('comments_disabled', models.BooleanField(default=False)),
                ('mailing_address', models.TextField(default=b'', blank=True)),
                ('special_mail_handling', models.TextField(default=b'', blank=True)),
                ('consent_form_received', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='organization',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='moderators',
            field=models.ManyToManyField(related_name='organizations_moderated', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='outgoing_mail_handled_by',
            field=models.ForeignKey(blank=True, to='profiles.Organization', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='affiliation',
            name='organizations',
            field=models.ManyToManyField(help_text=b'Which organizations are allowed to mark posts as belonging to this affiliation?', to='profiles.Organization'),
            preserve_default=True,
        ),
    ]
