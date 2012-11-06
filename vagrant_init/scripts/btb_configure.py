#!/usr/bin/env python

import os
from common import *

btb_dir = "/var/btb"
venv_dir = "/var/btb/venv"
venv_python = "/var/btb/venv/bin/python"
venv_pip = "/var/btb/venv/bin/pip"
wkhtmltopdf_url = "https://wkhtmltopdf.googlecode.com/files/wkhtmltopdf-0.11.0_rc1-static-i386.tar.bz2"

# Install BtB
if not os.path.exists(btb_dir):
    sh("git clone https://github.com/yourcelf/btb.git {0}".format(btb_dir))
else:
    sh("git --git-dir={0}/.git pull origin master".format(btb_dir))
write_template("/var/btb/scanblog/settings.py")

if not os.path.exists(venv_dir):
    sh("virtualenv {0}".format(venv_dir))
sh("{0} install -q -r {1}/scanblog/requirements.txt".format(
    venv_pip, btb_dir))

# Get wkhtmltopdf
sh("curl -L {0} | tar xjf - -O > /usr/local/bin/wkhtmltopdf".format(wkhtmltopdf_url))

# Install pre-processors: compass, coffeescript
sh("gem install compass")
sh("npm install -g coffee-script")

#  install fonts as system fonts for wkhtmltopdf's sake
sh("cp {0}/scanblog/static/fonts/*.ttf /usr/local/share/fonts/".format(btb_dir))

# Run initial management commands
manage = "{0} {1}/scanblog/manage.py".format(venv_python, btb_dir)
sh("{0} syncdb --noinput".format(manage))
sh("{0} migrate".format(manage))
sh("{0} loaddata btb/fixtures/initial_data.json".format(manage))
