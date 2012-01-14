import os
import time

from lettuce import *
from lettuce.django import django_url
from django.conf import settings
from selenium.common.exceptions import NoSuchElementException

from scanning.models import Scan
from btblettuce import *

@step(u'there are no scans in the dashboard')
def there_are_no_scans_in_the_dashboard(step):
    for s in Scan.objects.filter(processing_complete=False):
        s.delete()

@step(u'I see the upload form')
def i_see_the_upload_form(step):
    h1_text = world.browser.find_element_by_tag_name("h1").text
    assert  h1_text == "Upload Scans", \
            "Expected %s; got %s" % ("Upload Scans", h1_text)


@step(u'I can upload the following files successfully')
def i_can_upload_the_following_files_successfully(step):
    for hsh in step.hashes:
        name = hsh['filename']
        num = int(hsh['number of scans'])

        path = os.path.join(settings.SETTINGS_ROOT, "media", "test", "src", 
                name)
        assert os.path.exists(path), "Test file missing: %s" % path

        world.browser.get(django_url("/scanning/add"))
        el = world.browser.find_element_by_id("id_file")
        el.send_keys(path)
        css(".upload-submit").submit()

        # Processing interstitial
        h2_text = world.browser.find_element_by_tag_name("h2").text
        assert h2_text == "Processing", \
                "Expected %s; got %s. (%s)" % ("Processing", h2_text, name)

        # Wait for it...
        while "moderation/wait" in world.browser.current_url:
            try:
                el = css(".error")
                assert False, el.text
                break
            except NoSuchElementException:
                time.sleep(1)
        time.sleep(2) # Let lingering JS finish..

        # And it worked.
        if num == 1:
            assert world.browser.current_url.startswith(django_url("/moderation/#/process"))
            eq_(css("h1").text, "Split Scan")
        else:
            eq_(world.browser.current_url, django_url("/moderation/"))
            els = csss(".open-scans .scan")
            assert len(els) == num, "Expected %s files in %s, got %s" % (num, name, len(els))

        # Clean up.
        there_are_no_scans_in_the_dashboard(step)
