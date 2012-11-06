#!/usr/bin/env python

from common import *

write_template("/etc/ssh/sshd_config")
sh("service ssh restart")
