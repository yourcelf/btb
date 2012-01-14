import datetime

import pyPdf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from djcelery.models import TaskMeta

from scanning.models import Scan
from scanning import tasks

def new_scan(filename=None, uploaded_file=None, uploader_id=None, scan_id=None):
    """
    Given an absolute filename or a Django UploadedFile instance, write the
    file to MEDIA_ROOT, then hand off processing to the asynchronous task to
    create scans.
    """
    if scan_id:
        scan = Scan.objects.get(pk=scan_id)
        scan.full_delete(filesonly=True)
    if not (filename or uploaded_file):
        raise Exception("Requires one of filename or uploaded_file")
    try:
        uploader = User.objects.get(pk=uploader_id)
    except User.DoesNotExist:
        raise Exception("Requires valid uploader_id.")

    dest = tasks.move_scan_file(uploaded_file, filename)
    after_processing = reverse("moderation.home") + "#/process"
    if scan_id:
        after_processing += "/scan/%s" % scan_id

    task_kwargs = {'redirect': after_processing}
    if scan_id:
        scan.pdf = dest
        scan.uploader = uploader
        scan.save()
        task_kwargs['scan_id'] = scan.id
    else:
        task_kwargs['filename'] = dest
        task_kwargs['uploader_id'] = uploader_id

    task_id = tasks.process_scan.delay(**task_kwargs).task_id

    # Create a TaskMeta for us to look at while processing happens.
    TaskMeta.objects.create(task_id=task_id, status="PENDING", 
            result=str(task_kwargs),
            date_done=datetime.datetime.now())

    return task_id

def get_pdf_page_count(filepath):
    with open(filepath) as fh:
        reader = pyPdf.PdfFileReader(fh)
        return reader.getNumPages()
