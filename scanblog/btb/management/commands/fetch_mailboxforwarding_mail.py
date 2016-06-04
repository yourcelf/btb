import re
import os
import sys
import time
import json
import tempfile
import requests
from cStringIO import StringIO
from pyPdf import PdfFileWriter, PdfFileReader
from PIL import Image

# Work around InseurePlatformWarning:
# https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning
# Remove this when we upgrade to python3.
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from scanning.models import Scan
from scanning import tasks
from profiles.models import Organization

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        base_url = "https://www.mailboxforwarding.com/"
        
        if (not hasattr(settings, "MAILBOX_FORWARDING") or 
                not "username" in settings.MAILBOX_FORWARDING or
                not "password" in settings.MAILBOX_FORWARDING):
            print "Requires MAILBOX_FORWARDING settings, e.g.:"
            print 'MAILBOX_FORWARDING = {'
            print '  "username": "user@domain.com",'
            print '  "password": "secret",'
            print '}'
            print "exit 1"
            sys.exit(1)

        sess = requests.Session()
        res = sess.post(base_url + "manage/login.php", {
            "action": "login",
            "email": settings.MAILBOX_FORWARDING["username"],
            "password": settings.MAILBOX_FORWARDING["password"],
            "loginsubmit.x": "0",
            "loginsubmit.y": "0"
        })
        # This is a slightly dirty hack -- we're matching a javascript data
        # structure with a regex, converting the quotes to doubles so it resembles
        # JSON, and then loading it as JSON.  This may prove brittle.
        match = re.search(r"Ext\.grid\.dummyData = (\[.*\]\]);", res.text, re.DOTALL)
        if not match:
            raise Exception("Can't find data. Are login creds correct?")
        text = match.group(1)
        text = text.replace('"', '\\"')
        text = text.replace("'", '"')
        data = json.loads(text)

        scans = {}
        packages = {}
        for checkbox, date, envelope, type_status, dl in data:
            details = {}
            match = re.search("Type: <b>([^<]+)</b>.*Status: <b>([^<]+)</b>", type_status)
            if not match:
                raise Exception("Can't match type/status")
            details['kind'] = match.group(1)
            details['status'] = match.group(2)

            if details['kind'] == "Letter" and details['status'] != "Scanned":
                continue

            match = re.search("pdfview.php\?id=(\d+)", dl)
            if match:
                id_ = match.group(1)
            else:
                # TODO: Handle packages correctly
                continue
                #raise Exception("Can't find ID")

            match = re.search("src=\"([^\"]+)\"", envelope)
            if not match:
                raise Exception("Can't match envelope image")
            details['envelope'] = match.group(1)


            if details['status'] == "Scanned":
                scans[id_] = details
            elif details['kind'] != "Letter":
                packages[id_] = details

        uploader = User.objects.get(username="uploader")
        org = Organization.objects.get(pk=1) #TODO: generalize this? 

        new_count = 0
        for id_, details in scans.iteritems():
            source_id = "mailboxforwarding.com-{}".format(id_)
            if Scan.objects.filter(source_id=source_id).exists():
                continue
            new_count += 1

            print "Downloading pdf", source_id
            res = sess.get("{}manage/pdfview.php?id={}".format(base_url, id_))
            in_pdf_fh = StringIO()
            in_pdf_fh.write(res.content)
            in_pdf_fh.seek(0)
            reader = PdfFileReader(in_pdf_fh)

            print "Downloading envelope", details['envelope']
            res = sess.get(details['envelope'])
            in_envelope_fh = StringIO()
            in_envelope_fh.write(res.content)
            in_envelope_fh.seek(0)
            img = Image.open(in_envelope_fh)
            out_envelope_fh = StringIO()
            img.save(out_envelope_fh, "pdf")
            envelope_reader = PdfFileReader(out_envelope_fh)

            writer = PdfFileWriter()
            writer.addPage(envelope_reader.getPage(0))
            for page in range(reader.getNumPages()):
                writer.addPage(reader.getPage(page))

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
                writer.write(fh)
                dest_pdf_name = fh.name

            in_envelope_fh.close()
            out_envelope_fh.close()
            in_pdf_fh.close()

            path = tasks.move_scan_file(filename=dest_pdf_name)
            scan = Scan.objects.create(
                uploader=uploader,
                pdf=os.path.relpath(path, settings.MEDIA_ROOT),
                under_construction=True,
                org=org,
                source_id=source_id
            )
            tasks.split_scan(scan=scan)

        if packages:
            print "Manual action needed on the following at " \
                  "https://www.mailboxforwarding.com/:"
            for id_, details in packages.iteritems():
                new_count += 1
                print details
        print "Examined {} letters, {} new.".format(len(data), new_count)
