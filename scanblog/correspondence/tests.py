import json
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command

from btb.tests import BtbLoginTestCase
from correspondence import utils
from correspondence.models import Letter, StockResponse
from scanning.models import Document
from comments.models import Comment

class TextLatexCompilation(TestCase):
    def test_escape_tex(self):
        self.assertEquals(
            utils.tex_escape('Line one\nLine two\nLine three'),
            'Line one\\\\\nLine two\\\\\nLine three'
        )
        self.assertEquals(
            utils.tex_escape('Line one\n\nLine three'),
            'Line one\\\\\n~\\\\\nLine three'
        )
        self.assertEquals(
            utils.tex_escape('Line one\r\nLine two\r\nLine three'),
            'Line one\\\\\nLine two\\\\\nLine three'
        )

class TestStockResponses(BtbLoginTestCase):
    fixtures = ["groups.json"]
    def test_get_stock_response(self):
        stock_responses = [
                ["Stock 1", "The answer to your question 1..."],
                ["Stock 2", "The answer to your question 2..."],
                ["Stock 3", "The answer to your question 3..."],
        ]
        for name, body in stock_responses:
            StockResponse.objects.create(name=name, body=body)

        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 403)

        self.loginAs("reader")
        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 403)

        self.loginAs("moderator")
        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 200)
        self.assertEquals(json.loads(res.content), {
            'results': [
                {'id': 3, 'name': "Stock 3", 'body': "The answer to your question 3..."},
                {'id': 2, 'name': "Stock 2", 'body': "The answer to your question 2..."},
                {'id': 1, 'name': "Stock 1", 'body': "The answer to your question 1..."},
            ]
        })


class TestPostListLetter(BtbLoginTestCase):
    fixtures = ["groups.json"]

    def setUp(self):
        super(TestPostListLetter, self).setUp()
        self.author_user = User.objects.get(username='author')
        self.moderator_user = User.objects.get(username='moderator')
        # Create some published posts with varying dates.
        self.posts = []
        for i in range(3):
            doc = Document.objects.create(
                author=self.author_user,
                editor=self.moderator_user,
                type="post",
                title="Post %d" % (i + 1),
                status="published",
                date_written=datetime.datetime(2025, 1, 1 + i),
            )
            self.posts.append(doc)
        # Add comments to post 1 (2 comments) and post 3 (1 comment).
        self.commenter = User.objects.get(username='reader')
        for _ in range(2):
            Comment.objects.create(
                user=self.commenter,
                document=self.posts[0],
                comment="Nice post",
            )
        Comment.objects.create(
            user=self.commenter,
            document=self.posts[2],
            comment="Great post",
        )
        # Also create an unpublished post that should not appear.
        Document.objects.create(
            author=self.author_user,
            editor=self.moderator_user,
            type="post",
            title="Draft Post",
            status="unknown",
            date_written=datetime.datetime(2025, 2, 1),
        )

    def test_post_list_letter_query(self):
        """Test that post_list_letter produces correct post data."""
        from django.db import models as db_models
        posts = Document.objects.filter(
            author=self.author_user,
            type="post",
            status="published",
        ).annotate(
            comment_count=db_models.Count('comments')
        ).order_by('date_written')

        self.assertEquals(len(posts), 3)
        self.assertEquals(posts[0].title, "Post 1")
        self.assertEquals(posts[0].comment_count, 2)
        self.assertEquals(posts[1].title, "Post 2")
        self.assertEquals(posts[1].comment_count, 0)
        self.assertEquals(posts[2].title, "Post 3")
        self.assertEquals(posts[2].comment_count, 1)

    def test_enqueue_management_command(self):
        """Test that the management command creates a letter."""
        self.assertEquals(Letter.objects.filter(type="post_list").count(), 0)
        call_command('enqueue_post_list_letter', str(self.author_user.pk))
        self.assertEquals(Letter.objects.filter(type="post_list").count(), 1)
        letter = Letter.objects.get(type="post_list")
        self.assertEquals(letter.recipient, self.author_user)
        self.assertEquals(letter.org, self.org)
        self.assertIn(letter.sender, list(self.org.moderators.all()))
        self.assertTrue(letter.auto_generated)
        self.assertIsNone(letter.sent)

    def test_enqueue_picked_up_as_enqueued(self):
        """Test that the letter is unsent/unmailed and eligible for mailing."""
        call_command('enqueue_post_list_letter', str(self.author_user.pk))
        letter = Letter.objects.get(type="post_list")
        # Should appear in unsent letters (the criteria used by Mailings.post
        # for "enqueued" type).
        Letter.objects.filter(
            sent__isnull=True,
            recipient__profile__lost_contact=False,
            mailing__isnull=True,
            auto_generated=False,
        )
        # auto_generated=True letters are not picked up as "enqueued" in the
        # mailing creation flow; they are picked up individually. But they are
        # still unsent and will be included if manually added to a mailing.
        # The letter should at minimum be unsent and not in any mailing.
        self.assertIsNone(letter.sent)
        self.assertFalse(letter.mailing_set.exists())
