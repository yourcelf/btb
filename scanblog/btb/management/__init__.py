from django.core.management import call_command

def set_up_groups(apps=None, schema_editor=None, with_create_permissions=True):
    # Branch to work either in a migration, or in a test loader.
    if apps:
        ContentType = apps.get_model('contenttypes', 'ContentType')
    else:
        from django import apps
        from django.contrib.contenttypes.models import ContentType

    # Ensure ``makepermissions`` has run.  Ugly hack:
    # https://code.djangoproject.com/ticket/23422
    if ContentType.objects.count() == 0 and with_create_permissions:
        from django.contrib.auth.management import create_permissions
        assert not hasattr(apps, 'models_module')
        apps.models_module = True
        create_permissions(apps, verbosity=0)
        del apps.models_module
        return set_up_groups(apps, schema_editor, with_create_permissions=False)

    call_command("loaddata", "btb/fixtures/groups.json",
            interactive=False, verbosity=0)
