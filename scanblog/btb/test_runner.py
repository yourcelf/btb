from uuid import uuid4
from datetime import datetime
from djcelery.contrib.test_runner import CeleryTestSuiteRunner
from celery.task import Task
from djcelery.backends.database import DatabaseBackend
from djcelery.models import TaskState
from django.conf import settings

class BtbTestRunner(CeleryTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        """ Setting up test environment. """

        def add_task_meta(task_id, kwargs, state):
            # HACK: when running tests with CELERY_ALWAYS_EAGER, TaskMeta
            # doesn't get written. Add results here for the cases we can handle.
            # https://github.com/celery/django-celery/issues/191 
            if 'redirect' in kwargs:
                DatabaseBackend().store_result(task_id, kwargs['redirect'], state)

        # Monkey-patch Task.on_success() method
        def on_success_patched(self, retval, task_id, args, kwargs):
            TaskState.objects.create(task_id=task_id,
                                     state="SUCCESS",
                                     name=self.name,
                                     result=retval,
                                     args=args,
                                     kwargs=kwargs,
                                     tstamp=datetime.now())
            add_task_meta(task_id, kwargs, "SUCCESS")

        Task.on_success = classmethod(on_success_patched)

        # Monkey-patch Task.on_failure() method
        def on_failure_patched(self, exc, task_id, args, kwargs, einfo):
            TaskState.objects.create(task_id=task_id,
                                     state="FAILURE",
                                     name=self.name,
                                     result=einfo,
                                     args=args,
                                     kwargs=kwargs,
                                     tstamp=datetime.now())
            add_task_meta(task_id, kwargs, "FAILURE")

        Task.on_failure = classmethod(on_failure_patched)

        # Call parent's version
        super(BtbTestRunner, self).setup_test_environment(**kwargs)

        # Tell celery run tasks synchronously
        settings.CELERY_RESULT_BACKEND = 'database'
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75
