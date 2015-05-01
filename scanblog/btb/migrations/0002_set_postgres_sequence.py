# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations, connection
from django.conf import settings

def set_pg_sequence(apps, schema_editor):
    if connection.vendor == "postgresql":
        # Reset sequence of user so Postgres doesn't crash on an existing user
        # ID 100 for our uploader user.
        # http://stackoverflow.com/a/3698777/85461
        migrations.RunSQL(
            """
            SELECT pg_catalog.setval(
                pg_get_serial_sequence('auth_user', 'id'), MAX(id)
            ) FROM auth_user;
            """.format(table_name=settings.AUTH_USER_MODEL)
        )

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('btb', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_pg_sequence, backwards)
    ]
