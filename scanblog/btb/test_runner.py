import os
# https://docs.djangoproject.com/en/dev/topics/testing/#django.test.LiveServerTestCase
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8082-8999'
from datetime import datetime
from djcelery.contrib.test_runner import CeleryTestSuiteRunner
from celery.task import Task
from celery import current_app
from djcelery.backends.database import DatabaseBackend
from django.conf import settings

# Custom test runner that stores TaskMeta even with CELERY_ALWAYS_EAGER.
class BtbTestRunner(CeleryTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        # Monkey-patch Task.on_success() method
        def on_success_patched(self, retval, task_id, args, kwargs):
            app = current_app._get_current_object()
            DatabaseBackend(app=app).store_result(task_id, retval, "SUCCESS")
        Task.on_success = classmethod(on_success_patched)

        super(BtbTestRunner, self).setup_test_environment(**kwargs)

        # Tell celery run tasks synchronously
        settings.CELERY_RESULT_BACKEND = 'database'
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75

    def run_tests(self, test_labels, **kwargs):
        # NOTE: exclude 'btb' by default, as it does slow integration tests
        # with selenium.  Explicitly list it to run those tests, e.g.:
        #
        #   python manage.py test btb.tests
        #
        if not test_labels:
            test_labels = ("about", "accounts", "annotations", "blogs",
                           "campaigns", "comments", "correspondence",
                           "moderation", "profiles", "scanning",
                           "subscriptions")
        return super(BtbTestRunner, self).run_tests(test_labels, **kwargs)
