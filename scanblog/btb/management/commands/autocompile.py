from django.core.management.base import BaseCommand, CommandError

import os
import subprocess
import platform

BASE_PATH         = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
COFFEEWATCH_PATH  = os.path.join(BASE_PATH, "btb", "management", "coffeewatch.sh")
COFFEESCRIPT_PATH = os.path.join(BASE_PATH, "static", "js")
SASS_PATH         = os.path.join(BASE_PATH, "static", "css", "sass")

class Command(BaseCommand):
    args = ''
    help = 'Watch and automatically compile sass and coffeescript files.'

    def exec_coffee(self):
        # XXX HACK: compile coffeescript with inotify instead
        #if platform.uname()[0] == 'Linux':
        #    return subprocess.Popen([COFFEEWATCH_PATH], shell=True)
        #else:
        return subprocess.Popen(["coffee", "--watch", "--compile", COFFEESCRIPT_PATH])

    def exec_compass(self):
        return subprocess.Popen(["compass", "watch"], cwd=SASS_PATH)

    def autocompile(self):
        compass = self.exec_compass()
        coffee = self.exec_coffee()
        try:
            compass.communicate() # wait on compass
        except KeyboardInterrupt:
            pass
        finally:
            if compass: compass.kill()
            if coffee: coffee.kill()

    def handle(self, *args, **options):
        self.autocompile()
