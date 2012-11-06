#!/usr/bin/env python

from common import *

import subprocess
import urllib2

## Install node
if not os.path.exists("/usr/local/bin/node") or \
        subprocess.check_output(["/usr/local/bin/node", "--version"]) != "v0.8.9\n":
    sh("rm -rf /tmp/node*")
    url = urllib2.urlopen("http://nodejs.org/dist/v0.8.9/node-v0.8.9.tar.gz")
    with open("/tmp/node.tar.gz", 'wb') as fh:
        fh.write(url.read())
    sh("tar -C /tmp -xzvf /tmp/node.tar.gz")
    sh("cd /tmp/node*/ && ./configure && make && make install")

## Install node packages
sh("npm install -g coffee-script")
