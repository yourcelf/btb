import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.conf import settings

from btb.tests import BtbLoginTestCase
from scanning.models import Scan, Document
from profiles.models import Organization
from scanning.management.commands.publish_queued import publish_ready, \
        next_by_pressure, calculate_pressure, calculate_interval

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

    def test_scan_json_lists(self):
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

class TestPublishQueued(BtbLoginTestCase):
    def setUp(self):
        super(TestPublishQueued, self).setUp()
        # Add more test users to test ready-queue sorting with
        for name in ('A', 'B', 'C', 'D', 'E'):
            self.add_user({
                'username': name,
                'managed': True,
                'member': self.org,
                'groups': ['authors', 'readers'],
            })

    def test_doesnt_publish_outside_publishing_hours(self):
        for hour in range(0, 24):
            now = datetime(2014, 1, 1, hour, 0, 0)
            doc = Document.objects.create(
                author=User.objects.get(username='author'),
                editor=User.objects.get(username='moderator'),
                title="Expired 1",
                type="post",
                status="ready",
                created=now - timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS, seconds=1),
            )
            publish_ready(now)
            # Refresh doc from db.
            doc = Document.objects.get(pk=doc.pk)
            if (now.hour < settings.PUBLISHING_HOURS[0] or
                    now.hour > settings.PUBLISHING_HOURS[1]):
                self.assertEquals(doc.status, "ready")
                self.assertEquals(Document.objects.ready().count(), 1)
            else:
                self.assertEquals(doc.status, "published")
                self.assertEquals(Document.objects.ready().count(), 0)
            doc.delete()

    def test_publishes_past_deadline(self):
        # Choose a "now" within publishing hours
        now = datetime(2014, 1, 1, 12, 0, 0)
        assert now.hour > settings.PUBLISHING_HOURS[0]
        assert now.hour < settings.PUBLISHING_HOURS[1]

        doc1 = Document.objects.create(
            author=User.objects.get(username='author'),
            editor=User.objects.get(username='moderator'),
            title="Expired 1",
            type="post",
            status="ready",
            created = now - timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS, seconds=1),
        )
        doc2 = Document.objects.create(
            author=User.objects.get(username='author'),
            editor=User.objects.get(username='moderator'),
            title="Expired 2",
            type="post",
            status="ready",
            created = now - timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS),
        )

        self.assertEquals(set(Document.objects.ready()), set([doc1, doc2]))
        publish_ready(now)
        self.assertEquals(set(Document.objects.ready()), set([doc2]))
        publish_ready(now)
        self.assertEquals(Document.objects.ready().count(), 0)

    def _build_test_docs(self, now):
        def _build_doc(username, i, age):
            return Document.objects.create(
                    author=User.objects.get(username=username),
                    editor=User.objects.get(username='moderator'),
                    title="%s%s" % (username, i),
                    status="ready",
                    type="post",
                    created=now - timedelta(days=age))
        M = settings.MAX_READY_TO_PUBLISH_DAYS
        a0 = _build_doc("A", 0, M + 1) # Expired
        # The rest aren't expired yet -- listed here from oldest to most recent per author
        a1 = _build_doc("A", 1, M - 2.0)
        a2 = _build_doc("A", 2, M - 2.1)
        a3 = _build_doc("A", 3, M - 2.2)
        a4 = _build_doc("A", 4, M - 2.3)
        a5 = _build_doc("A", 5, M - 2.4)
        b1 = _build_doc("B", 1, M - 2.0)
        b2 = _build_doc("B", 2, M - 2.1)
        b3 = _build_doc("B", 3, M - 2.2)
        c1 = _build_doc("C", 1, M - 2.0)
        d1 = _build_doc("D", 1, M - 2.0)
        return [a0, a1, a2, a3, a4, a5, b1, b2, b3, c1, d1]

    def test_next_by_pressure(self):
        now = datetime(2014, 1, 1, 12, 0, 0)
        user_ids = [User.objects.get(username=username).id for username in 'ABCD']
        pressure_sequence = [
        #    A  B  C  D, => next
            [6, 3, 1, 1,    'A0'],
            [5, 6, 2, 2,    'B1'],
            [10, 2, 3, 3,   'A1'],
            [4, 4, 4, 4,    'B2'],
            [8, 1, 5, 5,    'A2'],
            [3, 2, 6, 6,    'C1'],
            [6, 3, 0, 7,    'D1'],
            [9, 4, 0, 0,    'A3'],
            [2, 5, 0, 0,    'B3'],
            [4, 0, 0, 0,    'A4'],
            [1, 0, 0, 0,    'A5'],
        ]
        ready = self._build_test_docs(now)
        recent = []
        for seq in pressure_sequence:
            self.assertEquals(
                    dict(zip(user_ids, seq[0:-1])),
                    calculate_pressure(ready, recent)
            )
            doc = next_by_pressure(ready, recent)
            self.assertEquals(doc.title, seq[-1])
            recent.append(doc)
            ready.remove(doc)
        self.assertEquals(len(recent), 11)

    def test_calculate_interval(self):
        with self.settings(PUBLISHING_HOURS=[10,14], MAX_READY_TO_PUBLISH_DAYS=7):
            now = datetime(2014, 1, 1, 12, 0, 0)
            ready = self._build_test_docs(now)
            # a0 is past-due, interval should be 0.
            self.assertEquals(calculate_interval(ready, now), timedelta(0))
            ready.pop(0)
            # There are 2 days left for the oldest test doc.
            self.assertEquals(calculate_interval(ready, now),
                    # 2 days left * 4 hours per day, 10 documents
                    timedelta(seconds=2. * 4 * 60* 60 / 10)
            )

    def test_publish_ready(self):
        with self.settings(MAX_READY_TO_PUBLISH_DAYS=7, PUBLISHING_HOURS=[10,14]):
            now = datetime(2014, 1, 1, 12, 0, 0)
            a0, a1, a2, a3, a4, a5, b1, b2, b3, c1, d1 = self._build_test_docs(now)
            def _refresh(doc):
                return Document.objects.get(pk=doc.pk)

            # Publish every 5 minutes for a week.
            total_seconds = 7 * 24 * 60 * 60 
            order = []
            times = []
            cur = datetime(now.year, now.month, now.day,
                now.hour, now.minute, now.second, now.microsecond, now.tzinfo)
            for t in range(0, total_seconds, 5*60):
                cur = cur + timedelta(seconds=t)
                result = publish_ready(cur)
                if result is not None:
                    order.append(result.title)
                    times.append(cur)
            self.assertEquals(order, 'A0 B1 A1 B2 A2 C1 D1 A3 B3 A4 A5'.split())
            # "just-so" results from a suspected good run.  Since the interval
            # is calculated based on the time from the oldest ready document,
            # the results are only as linear as the times on the starting docs.
            self.assertEquals(times, [
                datetime(2014, 1, 1, 12, 0),
                datetime(2014, 1, 1, 12, 50),
                datetime(2014, 1, 1, 13, 45),
                datetime(2014, 1, 2, 11, 0),
                datetime(2014, 1, 2, 13, 0),
                datetime(2014, 1, 3, 10, 45),
                datetime(2014, 1, 3, 13, 35),
                datetime(2014, 1, 4, 11, 45),
                datetime(2014, 1, 5, 10, 0),
                datetime(2014, 1, 5, 14, 0),
                datetime(2014, 1, 6, 11, 15),
            ])

            self.assertEquals(Document.objects.ready().count(), 0)
