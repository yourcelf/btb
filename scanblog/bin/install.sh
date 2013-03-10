#!/bin/bash

# This script installs all the system components and the python debendencies
# necessary to test Between the Bars. The script is intended for use with 
# the travis-ci setup, but you could use it too.
#
# If you run this, YOU SHOULD install and activate a virtualenv for pip to use
# first, e.g.:
#
#     virtualenv venv
#     source venv/bin/activate
#

set -x
set -e

# Path to the currently executing script.
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install packages..
sudo apt-get -y -qq install git mercurial poppler-utils pdftk imagemagick rubber rabbitmq-server python-dev python-virtualenv postgresql-server-dev-all rubygems nodejs npm texlive-fonts-extra texlive-fonts-recommended texlive-font-utils texlive-generic-recommended texlive-latex-extra texlive-latex-recommended ttf-sil-gentium libjpeg-dev libpng-dev

pip install -r "$BIN_DIR/../requirements.txt"

sudo gem install --no-ri --no-rdoc compass
sudo npm install -g coffee-script

# Download latest webkithtmltopdf
curl -L https://wkhtmltopdf.googlecode.com/files/wkhtmltopdf-0.11.0_rc1-static-i386.tar.bz2 | tar -xjv -C $BIN_DIR 

# Current firefox works for the moment...
#curl -L https://ftp.mozilla.org/pub/mozilla.org/firefox/releases/10.0/linux-i686/en-US/firefox-10.0.tar.bz2 | tar xjv -C $BIN_DIR 

# Copy settings.
cp $BIN_DIR/../example.settings.py $BIN_DIR/../settings.py
