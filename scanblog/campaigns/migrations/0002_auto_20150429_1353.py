# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('annotations', '0003_auto_20150429_1353'),
        ('campaigns', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='organizations',
            field=models.ManyToManyField(help_text=b'Which organizations are allowed to mark posts as being part of this campaign?', to='profiles.Organization'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='reply_code',
            field=models.OneToOneField(to='annotations.ReplyCode'),
            preserve_default=True,
        ),
    ]
