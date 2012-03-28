.. highlight:: bash

Installation
============

1. Install system components
----------------------------

BtB should work on unix systems; it has been tested on Linux and OS X.

System requirements:
 
 * Python 2.6 or 2.7 (Python 3 not supported), and development headers
 * `poppler-utils <http://poppler.freedesktop.org/>`_
 * `pdftk <http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/>`_
 * `imagemagick <http://www.imagemagick.org>`_
 * `wkhtmltopdf <https://code.google.com/p/wkhtmltopdf/>`_ >= 0.10
 * `rubber <https://launchpad.net/rubber/>`_
 * `rabbitmq-server <http://www.rabbitmq.com/>`_
 * `git <http://git-scm.com>`_ (for obtaining the codebase)
 * `mercurial <http://mercurial.selenic.com>`_ (for installing python dependencies)
 * `python-virtualenv <http://www.virtualenv.org/en/latest/>`_

System-specific instructions:
 
 * Ubuntu::

    sudo apt-get install poppler-utils pdftk imagemagick rubber rabbitmq-server python-dev postgresql-server-dev-all

    cd /tmp
    curl -O https://wkhtmltopdf.googlecode.com/files/wkhtmltopdf-0.11.0_rc1-i386.tar.bz2
    tar xjvf wkhtmltopdf-0.11.0_rc1-i386.tar.bz2
    sudo cp wkhtmltopdf /usr/local/bin
 
 * OS X (using `MacPorts <http://www.macports.org/>`_ -- install that first)::

    sudo port install \
        python26 \
        py26-virtualenv \
        git-core \
        mercurial \
        sqlite3 py26-sqlite \
        poppler \
        pdftk \
        rubber \
        imagemagick \
        rabbitmq-server

    # create symlinks to be compatible with other systems
    sudo ln -s virtualenv-2.6 /opt/local/bin/virtualenv
    sudo ln -sf easy_install-2.6 /opt/local/bin/easy_install

    cd /tmp
    curl -O https://wkhtmltopdf.googlecode.com/files/wkhtmltopdf-OSX-0.10.0_rc2-static.tar.bz2
    tar jxvf wkhtmltopdf-OSX-0.10.0_rc2-static.tar.bz2
    sudo cp wkhtmltopdf /usr/local/bin

2. Set up project directory
---------------------------

Set up a directory to put project files/etc in::

    BTB_DIR=~/work/btb # or whatever you like...
    mkdir -p $BTB_DIR

The rest of this documentation assumes there is a ``BTB_DIR`` environment variable.

3. Clone the repository
-----------------------
Download the code::

    cd $BTB_DIR
    git clone http://github.com/yourcelf/btb.git btb

4. Set up ``virtualenv`` and install python library dependencies
----------------------------------------------------------------

Set up a virtualenv into which to install python dependencies.  Python dependencies are listed in the file ``scanblog/requirements.txt``::

    VENV_DIR=~/work/btb/venv # or whatever you like
    virtualenv --no-site-packages $VENV_DIR
    source $VENV_DIR/bin/activate
    easy_install pip
    pip install -r $BTB_DIR/btb/scanblog/requirements.txt

5. Fonts
--------

To render postcards and letters, as well as to give it that stylish look, a couple of fonts need to be installed.

Gentium
+++++++

* Ubuntu::

    sudo apt-get install ttf-sil-gentium

* OS X::

    cd $BTB_DIR
    mkdir fonts
    cd fonts
    curl "http://scripts.sil.org/cms/scripts/render_download.php?&format=file&media_id=Gentium_102_W&filename=Gentium_102_W.zip" -o Gentium_102_W.zip
    unzip Gentium_102_W.zip

Web fonts
+++++++++

``wkhtmltopdf`` doesn't properly render non-local webfonts, so it is necessary to install the webfont used on BtB locally.

* Ubuntu::

    sudo cp $BTB_DIR/btb/scanblog/static/fonts/*.ttf /usr/local/share/fonts/

* OS X: TODO

Latex fonts
+++++++++++

In order to render pretty letters, LaTeX needs its fonts too.

    TODO -- one or more of ``texlive-fonts-extra``, ``texlive-fonts-recommended``, ``texlive-font-utils``, ``texlive-generic-recommended``, ``texlive-latex-extra``, ``texlive-latex-recommended``...

6. Configure BtB
----------------

Copy ``example.settings.py`` to ``settings.py``, then edit it to reflect your settings::

    cd $BTB_DIR/btb/scanblog
    cp example.settings.py settings.py

Be sure to change:

* ADMINS and SERVER_EMAIL to a suitable name/email
* TEXT_IMAGE_FONT to the Gentium font path, e.g., ``~/work/btb/fonts/Gentium102/GenR102.TTF``
* Set the path to external executables as appropriate: ``NICE_CMD``, ``PDFTK_CMD``, ``WKHTMLTOPDF_CMD``, ``RUBBER_PIPE_CMD``, ``PDFINFO_CMD``, ``PDFTOTEXT_CMD``, ``CONVERT_CMD``
* Change ``SECRET_KEY`` to something long and random (it's used for hashing authentication cookies).
* If it's a production site, you'll want to use a database other than sqlite,
  as it doesn't support concurrent writes.  Set this in the ``DATABASES``
  configuration. (sqlite works fine for development)

7. Set up database
------------------

Load the initial database, and run initial migrations::

    source $VENV_DIR/bin/activate
    cd $BTB_DIR/btb/scanblog

    python manage.py syncdb --noinput
    python manage.py migrate
    python manage.py loaddata btb/fixtures/initial_data.json

    # Create superuser
    python manage.py shell  <<-EOF
    from shell import *
    u = User.objects.create(username='admin', is_superuser=True, is_staff=True)
    u.set_password('admin')
    u.save()
    exit()
    EOF

After running that script, there will be a single admin user with username
"admin" and password "admin".  This can be changed in the Django admin site by
navigating to ``http://localhost:8000/admin/``.

8. Run the dev server!
----------------------

Django ships with a built-in devserver.  You can run this directly::

    cd $BTB_DIR/btb/scanblog
    source $VENV_DIR/bin/activate
    python manage.py runserver

To also auto-compile coffeescript and sass sources, and run the celery deamon, use the included ``fromage.py`` instead::

    ./fromage.py

