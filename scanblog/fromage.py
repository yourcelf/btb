#!/usr/bin/env python
#
# Quickly autocompile sass and coffeescript and run the server
#

import os
import sys
import signal
import subprocess

BASE_PATH   = os.path.abspath(os.path.dirname(__file__))
MANAGE_PATH = os.path.join(BASE_PATH, "manage.py")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        ports = sys.argv[2:]
        runtests = True
    else:
        ports = sys.argv[1:]
        runtests = False

    autocompile = subprocess.Popen([MANAGE_PATH, "autocompile"])
    djcelery    = subprocess.Popen([MANAGE_PATH, "celeryd", "--verbosity=2"])
    runserver   = subprocess.Popen([MANAGE_PATH, "runserver"] + ports,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                               
    return_code = 0

    if runtests:
        try:
            collectstatic = subprocess.Popen([MANAGE_PATH, "collectstatic", "--noinput"])
            collectstatic.communicate()
            unittests = subprocess.Popen(
                    [MANAGE_PATH, "test", "btb", "about", "profiles", 
                        "annotations", "scanning", "subscriptions", "blogs"])
            unittests.communicate()
            assert unittests.returncode == 0
            integration = subprocess.Popen([MANAGE_PATH, "harvest"])
            integration.communicate()
            assert integration.returncode == 0
        except AssertionError:
            return_code = 1
            print "Tests failed!"
        else:
            return_code = 0
            print "Tests passed."
    try:
        runserver.communicate()
    except KeyboardInterrupt:
        pass
    runserver.kill()
    autocompile.kill()
    djcelery.kill()
    sys.exit(return_code)
