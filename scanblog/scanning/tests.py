import json

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse

from btb.tests import BtbLoginTestCase
from scanning.models import Scan, Document
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

class TestInReplyTo(BtbLoginTestCase):
    def setUp(self):
        super(TestInReplyTo, self).setUp()
        self.doc1 = Document.objects.create(
            author=User.objects.get(username='author'),
            editor=User.objects.get(username='moderator'),
            type="post",
            title="Post 1",
            status="published",
        )
        self.doc2 = Document.objects.create(
            author=User.objects.get(username='author'),
            editor=User.objects.get(username='moderator'),
            type="post",
            title="Post 2",
            status="published",
        )
        self.doc3 = Document.objects.create(
            author=User.objects.get(username='author'),
            editor=User.objects.get(username='moderator'),
            type="post",
            title="Post 3",
            status="published",
        )

    def test_in_reply_to_url(self):
        self.doc2.in_reply_to = self.doc1.reply_code
        self.doc2.save()
        self.assertEquals(
            self.doc2.get_absolute_url(),
            self.doc2.comment.get_absolute_url()
        )

    def test_change_in_reply_to(self):
        self.doc3.in_reply_to = self.doc1.reply_code
        self.doc3.save()
        self.assertEquals(self.doc3.comment.document, self.doc1)
        self.assertEquals(self.doc3.comment.comment_doc, self.doc3)
        self.assertEquals(self.doc3.comment.user, self.doc3.author)
        self.assertEquals(self.doc3.comment.removed, False)
        self.assertTrue(self.doc3.get_absolute_url().startswith(self.doc1.get_absolute_url()))

        self.doc3.in_reply_to = None
        self.doc3.save()
        self.assertEquals(self.doc3.comment.document, self.doc1)
        self.assertEquals(self.doc3.comment.comment_doc, self.doc3)
        self.assertEquals(self.doc3.comment.user, self.doc3.author)
        self.assertEquals(self.doc3.comment.removed, True)
        self.assertEquals(self.doc3.get_absolute_url(),
            reverse("blogs.post_show", args=[self.doc3.pk, self.doc3.get_slug()]))

        self.doc3.in_reply_to = self.doc2.reply_code
        self.doc3.save()
        self.assertEquals(self.doc3.comment.document, self.doc2)
        self.assertEquals(self.doc3.comment.comment_doc, self.doc3)
        self.assertEquals(self.doc3.comment.user, self.doc3.author)
        self.assertEquals(self.doc3.comment.removed, False)
        self.assertTrue(self.doc3.get_absolute_url().startswith(self.doc2.get_absolute_url()))

        self.doc3.in_reply_to = self.doc2.reply_code

    def test_recursive_in_reply_to(self):
        # Just in case this happens, we don't want to crash the site with
        # recursion. But this should be a validation error.
        self.doc1.in_reply_to = self.doc1.reply_code
        self.doc1.save()
        self.assertEquals(self.doc1.get_absolute_url(),
            reverse("blogs.post_show", args=[self.doc1.pk, self.doc1.get_slug()]))
