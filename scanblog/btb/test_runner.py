import os, sys
# https://docs.djangoproject.com/en/dev/topics/testing/#django.test.LiveServerTestCase
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8082-8999'
from datetime import datetime
from djcelery.contrib.test_runner import CeleryTestSuiteRunner
from celery.app.task import Task
from celery import current_app
from djcelery.backends.database import DatabaseBackend
from django.conf import settings


if "test" in sys.argv:
    # Connect a signal which will update task state, even if
    # CELERY_ALWAYS_EAGER is True.
    from celery.signals import task_postrun, task_failure

    @task_postrun.connect
    def postrun(sender, task_id, task, args, kwargs, retval, *margs, **mkwargs):
        app = current_app._get_current_object()
        DatabaseBackend(app=app).mark_as_done(task_id, retval)

    @task_failure.connect
    def failure(task_id, exception, args, kwargs, traceback, einfo, *margs, **mkwargs):
        app = current_app._get_current_object()
        DatabaseBackend(app=app).mark_as_failure(task_id, exception, traceback)

class BtbTestRunner(CeleryTestSuiteRunner):
    def run_tests(self, test_labels, **kwargs):
        if not test_labels:
            test_labels = ("about", "accounts", "annotations", "blogs",
                           "campaigns", "comments", "correspondence",
                           "moderation", "profiles", "scanning",
                           "subscriptions", "btb.tests")
        return super(BtbTestRunner, self).run_tests(test_labels, **kwargs)
