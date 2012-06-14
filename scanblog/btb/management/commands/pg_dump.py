import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    args = '<output_file>'
    help = "Use pg_dump to export the default database to the given file.  Only works if the database is a postgres database."

    def handle(self, output_file, *args, **kwargs):
        proc = subprocess.Popen('PGPASSWORD="{password}" pg_dump -U {user} {db} > {output_file}'.format(
                password=settings.DATABASES['default']['PASSWORD'],
                user=settings.DATABASES['default']['USER'],
                db=settings.DATABASES['default']['NAME'],
                output_file=output_file,
            ), shell=True)
        proc.communicate()
