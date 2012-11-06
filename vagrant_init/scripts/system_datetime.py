#!/usr/bin/env python

from common import *

sh("""

echo "UTC" > /etc/timezone
dpkg-reconfigure -f noninteractive tzdata
apt-get install -y ntp

""")
