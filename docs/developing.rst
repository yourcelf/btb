.. highlight:: bash

Developing
==========

Running the development server and autocompilation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BtB includes a wrapper for the Django development server that autocompiles coffeescript and SASS, and also runs celery for pdf processing::

    ./fromage.py

Installing test data
~~~~~~~~~~~~~~~~~~~~

BtB ships with a small bit of test data to make sure things are working properly.  Generate and load this data with the following management command::

    python manage.py import_test_data

The data is described in a YAML file located in ``scanblog/media/test/test_data.yaml``.

Running tests
~~~~~~~~~~~~~

Tests for Between the Bars are written in two places: as unittests included in the app directories in standard Django style, and as integration tests implemented with `lettuce <http://lettuce.it/>`_ and `selenium <http://seleniumhq.org/>`_.

To run just unittests::

    python manage.py test <appname1> <appname2> ...

To run integration tests (note that this modifies the current database; don't run it on production)::

    python manage.py harvest 

See the `lettuce documentation <http://lettuce.it/>`_ for more on harvest.

.. note::

    Between the Bars uses `celery <http://celeryproject.org/>`_ for asynchronous processing of PDFs.  In order
    to run tests, you need to have celery running.  You can do this by either
    running::

        ./fromage.py

    or by starting celery manually with::

        python manage.py celeryd

    In production, celery is usually managed by something like supervisord.

To run both types of test, for every app for which BtB has tests::

    ./fromage.py test

