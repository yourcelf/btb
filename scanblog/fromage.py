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

    try:
        autocompile = subprocess.Popen(
                [MANAGE_PATH, "autocompile"],
                preexec_fn=os.setsid)
        djcelery    = subprocess.Popen(
                [MANAGE_PATH, "celeryd", "--verbosity=2"],
                preexec_fn=os.setsid)
        runserver   = subprocess.Popen(
                [MANAGE_PATH, "runserver"] + ports,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                preexec_fn=os.setsid)
                                   
        return_code = 0
        if runtests:
            try:
                collectstatic = subprocess.Popen(
                        [MANAGE_PATH, "collectstatic", "--noinput"])
                collectstatic.communicate()
                unittests = subprocess.Popen(
                        [MANAGE_PATH, "test", 
                            "btb", "about", "profiles", 
                            "annotations", "scanning", 
                            "subscriptions", "blogs"])
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
    finally:
        # Use os.killpg to ensure that shell-launched process groups are all
        # killed, not just the launching process.
        for proc in [runserver, autocompile, djcelery]:
            os.killpg(proc.pid, signal.SIGTERM)
        sys.exit(return_code)
