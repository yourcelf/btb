#!/usr/bin/env python

from common import *

write_template("/etc/hosts")
sh("echo $HOSTNAME > /etc/hostname")
sh("hostname $HOSTNAME")
