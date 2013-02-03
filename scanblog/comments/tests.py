"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from btb.tests import BtbLoginTestCase
from scanning.models import Document
from comments.models import Comment, Favorite

class SimpleTest(BtbLoginTestCase):
    def test_login_redirect(self):
        self.assertRedirectsToLogin(reverse("comments.mark_favorite"))
        self.assertRedirectsToLogin(reverse("comments.unmark_favorite"))

    def test_deny_non_public_docs(self):
        doc = Document.objects.create(status="unpublishable",
                author=User.objects.get(username="author"),
                editor=User.objects.get(username="moderator"))

        self.loginAs("reader")
        res = self.client.post(reverse("comments.mark_favorite"),
                {'document_id': doc.pk})
        self.assertEquals(res.status_code, 404)

    def test_require_post(self):
        doc = Document.objects.create(status="published",
                author=User.objects.get(username="author"),
                editor=User.objects.get(username="moderator"))
        self.loginAs("reader")
        res = self.client.get(reverse("comments.mark_favorite"),
                {'document_id': doc.pk})
        self.assertEquals(res.status_code, 400)

    def test_mark_and_unmark_favorite(self):
        doc = Document.objects.create(status="published",
                author=User.objects.get(username="author"),
                editor=User.objects.get(username="moderator"))
        comment = Comment.objects.create(document=doc, 
                user=User.objects.get(username="admin"))
        self.loginAs("reader")
        reader = User.objects.get(username="reader")
        # Add a favorite.

        for pvar in ({'document_id': doc.pk}, {'comment_id': comment.pk}):
            for i in range(2):
                # First time to do it; second time to prove idempotency.
                res = self.client.post(
                        reverse("comments.mark_favorite"), pvar)
                self.assertEquals(res.status_code, 200)
                self.assertTrue("1 Favorite" in res.content)
                self.assertTrue(
                        reverse("comments.unmark_favorite") in res.content)
                self.assertTrue(
                        reverse("comments.mark_favorite") not in res.content)
                self.assertEquals(reader.favorite_set.count(), 1)
            # Remove the favorite.
            for i in range(2):
                # First time to do it; second time to prove idempotency.
                res = self.client.post(
                        reverse("comments.unmark_favorite"), pvar)
                self.assertEquals(res.status_code, 200)
                self.assertTrue(
                        reverse("comments.mark_favorite") in res.content)
                self.assertTrue(
                        reverse("comments.unmark_favorite") not in res.content)
                self.assertEquals(reader.favorite_set.count(), 0)

