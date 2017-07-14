# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from btb.management import set_up_groups


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0006_require_contenttypes_0002"),

        ("annotations", "0003_auto_20150429_1353"),
        ("comments", "0002_auto_20150429_1353"),
        ("correspondence", "0003_auto_20150429_1721"),
        ("profiles", "0001_initial"),
        ("scanning", "0003_document_comments_disabled")
    ]

    operations = [
        migrations.RunPython(set_up_groups)
    ]
