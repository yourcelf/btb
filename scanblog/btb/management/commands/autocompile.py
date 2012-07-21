from django.core.management.base import BaseCommand, CommandError

import os
import subprocess
import platform

BASE_PATH         = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SASS_PATH         = os.path.join(BASE_PATH, "static", "css", "sass")

class Command(BaseCommand):
    args = ''
    help = 'Watch and automatically compile sass and coffeescript files.'

    def exec_compass(self):
        return subprocess.Popen(["compass", "watch"], cwd=SASS_PATH)

    def autocompile(self):
        compass = self.exec_compass()
        try:
            compass.communicate() # wait on compass
        except KeyboardInterrupt:
            pass
        finally:
            if compass: compass.kill()

    def handle(self, *args, **options):
        self.autocompile()
