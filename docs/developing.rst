.. highlight:: bash

Developing
==========

Running the development server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the development server in the standard way::

    python manage.py runserver

To process scans, you'll need to also run the celery deamon::

    python manage.py celeryd

.. note::

    Previous versions of Between the Bars used a custom wrapper for `runserver`
    which performed compilation of assets.  This is now handled automatically
    by django_compressor.

Installing test data
~~~~~~~~~~~~~~~~~~~~

BtB ships with a small bit of test data to make sure things are working properly.  Generate and load this data with the following management command::

    python manage.py import_test_data

The data is described in a YAML file located in ``scanblog/media/test/test_data.yaml``.

Running tests
~~~~~~~~~~~~~

Between the Bars includes unit tests and integration tests.  Run unit tests with::

    python manage.py test

Integration tests run with ``selenium webdriver``, which runs a real, scripted
webbrowser to test the full stack of frontend and backend functionality.  Due
to the heavy weight of launching and testing with a full browser, these tests
are excluded from the default testrunner, and must be run explicitly::

    python manage.py test btb

.. note::

    Some combinations of different selenium webdriver and firefox versions have
    difficulty with native operations (such as mouse drags) or file uploads.
    We've found Selenium 2.20 and Firefox 10.0 to be a winning combination.
    Download an `old firefox binary here <https://ftp.mozilla.org/pub/mozilla.org/firefox/releases/>`_,
    and specify the path to this binary in ``settings.SELENIUM_FIREFOX_BIN``, e.g.::

        SELENIUM_FIREFOX_BIN = "/path/to/firefox_10/firefox

.. note::

    Previous versions of Between the Bars used `lettuce` for tests. This has
    been removed in favor of the standard Django test framework.
