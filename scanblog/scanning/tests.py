import json

from django.contrib.auth.models import User, Group

from btb.tests import BtbLoginTestCase
from scanning.models import Scan
from profiles.models import Organization

class TestScanJson(BtbLoginTestCase):
    def json_response_contains(self, url, list_of_scans):
        c = self.client
        self.assertTrue(c.login(username="moderator", password="moderator"))
        res = c.get(url)
        self.assertEquals(res.status_code, 200)
        struct = json.loads(res.content)
        return self.assertEquals(
                set(r['id'] for r in struct['results']),
                set([s.pk for s in list_of_scans])
        )

    def test_scan_json(self):
        org = Organization.objects.get(name='org')
        uploader = User.objects.get(username='moderator')
        kwargs = {
            'org': Organization.objects.get(name='org'),
            'uploader': User.objects.get(username='moderator'),
            'pdf': 'media/test/src/ex-prof-posts.pdf',
        }
        # No user
        not_finished_no_user = Scan.objects.create(pk=1, 
                **kwargs)
        finished_no_user = Scan.objects.create(pk=2,
                processing_complete=True, **kwargs)
        # Managed user
        not_finished_managed = Scan.objects.create(pk=3,
                author=User.objects.get(username='author'),
                **kwargs)
        finished_managed = Scan.objects.create(pk=4,
                author=User.objects.get(username='author'),
                processing_complete=True,
                **kwargs)
        # Unmanaged user
        not_finished_unmanaged = Scan.objects.create(pk=5,
                author=User.objects.get(username='reader'),
                **kwargs)
        finished_unmanaged = Scan.objects.create(pk=6,
                author=User.objects.get(username='reader'),
                processing_complete=True,
                **kwargs)

        self.json_response_contains("/scanning/scans.json",
                [finished_no_user, not_finished_no_user, 
                 not_finished_managed, finished_managed,
                 not_finished_unmanaged, finished_unmanaged])
        self.json_response_contains(
                "/scanning/scans.json?processing_complete=0",
                [not_finished_no_user, 
                 not_finished_unmanaged, 
                 not_finished_managed])
        self.json_response_contains(
                "/scanning/scans.json?processing_complete=1",
                [finished_no_user, 
                 finished_unmanaged, 
                 finished_managed])
        self.json_response_contains(
                "/scanning/scans.json?managed=0",
                [finished_unmanaged, not_finished_unmanaged])
        self.json_response_contains(
                "/scanning/scans.json?managed=1",
                [finished_no_user, not_finished_no_user,
                 finished_managed, not_finished_managed])
        self.json_response_contains(
                "/scanning/scans.json?managed=1&processing_complete=0",
                [not_finished_no_user, not_finished_managed])
