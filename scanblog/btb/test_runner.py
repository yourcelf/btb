import os
# https://docs.djangoproject.com/en/dev/topics/testing/#django.test.LiveServerTestCase
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8082-8999'
from datetime import datetime
from djcelery.contrib.test_runner import CeleryTestSuiteRunner
from djcelery.backends.database import DatabaseBackend
from django.conf import settings

# Custom test runner that stores TaskMeta even with CELERY_ALWAYS_EAGER.
class BtbTestRunner(CeleryTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        # Monkey-patch Task.on_success() method
        def on_success_patched(self, retval, task_id, args, kwargs):
            DatabaseBackend().store_result(task_id, retval, "SUCCESS")
        Task.on_success = classmethod(on_success_patched)

        super(BtbTestRunner, self).setup_test_environment(**kwargs)

        # Tell celery run tasks synchronously
        settings.CELERY_RESULT_BACKEND = 'database'
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75
