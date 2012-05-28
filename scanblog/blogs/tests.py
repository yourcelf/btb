from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from btb.tests import BtbTestCase
from scanning.models import Document
from profiles.models import Organization

class TestPostFromWeb(BtbTestCase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        for name in ('unmanaged', 'unmanaged2', 'managed', 'not_author'):
            u = User.objects.create(username=name)
            u.set_password(name)
            u.save()
            u.profile.blogger = True
            u.profile.managed = True
            u.profile.consent_form_received = True
            u.profile.save()
            setattr(self, name, u)

        self.unmanaged.profile.managed = False
        self.unmanaged.profile.save()

        self.unmanaged2.profile.managed = False
        self.unmanaged2.profile.save()

        self.not_author.profile.blogger = False
        self.not_author.profile.not_author = False

        org = Organization.objects.create(name="fun")
        org.members = [self.unmanaged, self.managed, self.not_author]

        self.doc = Document.objects.create(
            title="My title",
            body="My body",
            status="published",
            type='post',
            author=self.unmanaged,
            editor=self.unmanaged
        )

        self.post_capability = {
            'unmanaged': True,
            'managed': False,
            'not_author': False,
        }

    def test_post_controls(self):
        c = self.client
        for name, visibility in self.post_capability.items():
            c.login(username=name, password=name)
            res = c.get("/blogs/")
            for text in ("My Blog Posts", "Compose"):
                if visibility:
                    self.assertTrue(text in res.content)
                else:
                    self.assertFalse(text in res.content)

    def test_compose_post(self):
        c = self.client
        for name, visibility in self.post_capability.items():
            u = getattr(self, name)
            c.login(username=name, password=name)
            res = c.get(reverse("blogs.edit_post"))
            if visibility:
                self.assertEquals(res.status_code, 200)
            else:
                self.assertEquals(res.status_code, 403)

            res = c.post(reverse("blogs.edit_post"), {
                'title': "Good times", 'body': "In peace", 
                'tags': ['this', 'that'],
                'status': 'unknown',
            }, follow=True)
            if not visibility:
                self.assertEquals(res.status_code, 403)
            else:
                self.assertEquals(res.status_code, 200)
                doc = Document.objects.get(title="Good times")
                self.assertEquals(doc.author, u)
                self.assertEquals(doc.editor, u)
                self.assertEquals(doc.status, "unknown")

                post_edit_url = reverse("blogs.edit_post", kwargs={'post_id': doc.pk})

                res = c.get(post_edit_url)
                self.assertEquals(res.status_code, 200)

                res = c.post(post_edit_url, {
                    'title': "Good times", 'body': "In peace",
                    "tags": ['this', 'that'],
                    'status': 'published',
                }, follow=True)
                self.assertEquals(res.status_code, 200)
                doc = Document.objects.public().get(title="Good times")

    def test_only_author_can_edit(self):

        # Posted as unmanaged. unmanaged2 should be unable to edit.
        self.assertTrue(
            self.client.login(username="unmanaged2", password="unmanaged2")
        )
        res = self.client.get(reverse("blogs.edit_post", 
            kwargs={'post_id': self.doc.pk}))
        self.assertEquals(res.status_code, 404)

    def test_delete_post(self):
        self.assertEquals(self.doc.author.username, "unmanaged")

        doc_pk = self.doc.pk

        for name, status in (("unmanaged2", 404), ("unmanaged", 200)):
            self.assertTrue(self.client.login(username=name, password=name))

            res = self.client.get(reverse("blogs.delete_post",
                kwargs={'post_id': self.doc.pk}
            ))
            self.assertEquals(res.status_code, status)

            res = self.client.post(reverse("blogs.delete_post",
                kwargs={'post_id': self.doc.pk}
            ), follow=True)
            self.assertEquals(res.status_code, status)

        self.assertFalse(Document.objects.filter(pk=doc_pk).exists())

    def test_manage_posts(self):
        url = reverse("blogs.manage_posts")

        self.assertTrue(Document.objects.filter(author=self.unmanaged).count() > 0)

        for name, status in (("unmanaged", 200), ("managed", 403), ("not_author", 403)):
            self.assertTrue(self.client.login(username=name, password=name))

            res = self.client.get(url)
            self.assertEquals(res.status_code, status)
            if status == 200:
                self.assertTrue("Compose new post" in res.content)
            if name == "unmanaged":
                self.assertTrue("My title" in res.content)
