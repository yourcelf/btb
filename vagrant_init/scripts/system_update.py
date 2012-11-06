#!/usr/bin/env python

from common import *

sh("""

apt-get -y update
DEBIAN_FRONTEND='noninteractive' apt-get -y upgrade

""")
