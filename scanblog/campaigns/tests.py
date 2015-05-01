import json

from django.contrib.auth.models import User

from btb.tests import BtbLoginTestCase
from btb.utils import dthandler

from annotations.models import ReplyCode
from campaigns.models import Campaign
from profiles.models import Organization
from scanning.models import Document

class TestCampaignsJSON(BtbLoginTestCase):
    url = "/campaigns/campaigns.json"
    required_keys = ["title", "slug", "body", "organizations",
                     "reply_code", "public", "ended"]

    def setUp(self):
        super(TestCampaignsJSON, self).setUp()
        self.camp = Campaign.objects.create(
                title="My campaign",
                slug="my-campaign",
                body="Campaign HTML",
                public=True,
                reply_code=ReplyCode.objects.create(code="mycampaign"),
        )
        self.camp.organizations = [Organization.objects.get()]

    def _denied(self):
        for method in ("get", "put", "post", "delete"):
            res = getattr(self.client, method)(self.url)
            self.assertEquals(res.status_code, 403)

    def test_perms(self):
        self._denied()
        self.loginAs("reader")
        self._denied()
        # Must be logged in with "profiles.<x>_affiliation" perms, which
        # regular moderators don't have.
        self.loginAs("moderator")
        self._denied()

    def _query(self, method, data=None, success=None, error=None, status_code=None, url=None):
        if data:
            res = getattr(self.client, method)(url or self.url,
                    json.dumps(data, default=dthandler),
                    content_type='application/json')
        else:
            res = getattr(self.client, method)(url or self.url)
        if error:
            self.assertEquals(res.status_code, status_code or 400)
            self.assertEquals(json.loads(res.content), {"error": error})
        if success:
            self.assertEquals(res.status_code, 200)
            self.assertEquals(json.loads(res.content), success)
        return res

    def test_get(self):
        self.loginAs("admin")
        dct = self.camp.to_dict()
        dct['created'] = dct['created'].isoformat()
        self._query("get", success={
            'results': [dct],
            'pagination': {'count': 1, 'per_page': 12, 'page': 1, 'pages': 1},
        })
        self._query("get", url="{0}?id={1}".format(self.url, self.camp.id),
            success=dct)

    def test_put(self):
        self.loginAs("admin")
        dct = self.camp.to_dict()
        dct['created'] = dct['created'].isoformat()
        for key in self.required_keys:
            val = dct.pop(key)
            self._query("put", data=dct, error="Missing parameters: {0}".format(key))
            dct[key] = val

        reply_code = ReplyCode.objects.create(code="taken")

        # Can't use already used reply code.
        dct['reply_code'] = 'taken'
        self._query("put", data=dct, error="Reply code not available.")
        dct['reply_code'] = 'not taken'

        # Can't use empty organizations.
        orig = dct['organizations']
        dct['organizations'] = []
        self._query("put", data=dct, error="No organization specified.")
        dct['organizations'] = orig

        orig_reply_code_id = self.camp.reply_code.id

        # Success -- change title and reply code.
        dct['title'] = "New title"
        self._query("put", data=dct, success=dct)

        camp = Campaign.objects.get()
        self.assertEquals(camp.reply_code.id, orig_reply_code_id)
        self.assertEquals(camp.reply_code.code, "not taken")
        self.assertEquals(camp.title, "New title")


    def test_post(self):
        self.loginAs("admin")
        dct = {
                'title': "Second Campaign",
                'slug': "second-campaign",
                'body': "nice body",
                'reply_code': '2nd-reply-code',
                'public': True,
                'ended': None,
                'organizations': [self.org.light_dict()],
        }
        for key in self.required_keys:
            val = dct.pop(key)
            self._query("post", data=dct, error="Missing parameters: {0}".format(key))
            dct[key] = val

        # Can't use duplicate slug
        orig = dct['slug']
        dct['slug'] = self.camp.slug
        self._query("post", data=dct, error="Slug not unique.")
        dct['slug'] = orig

        # Can't use empty organizations
        orig = dct['organizations']
        dct['organizations'] = []
        self._query("post", data=dct, error="No organization specified.")
        dct['organizations'] = orig

        reply_code = ReplyCode.objects.create(code="taken")
        # Can't use already used reply code.
        orig = dct['reply_code']
        dct['reply_code'] = 'taken'
        self._query("post", data=dct, error="Reply code not available.")
        dct['reply_code'] = orig

        res = self._query("post", data=dct)
        self.assertEquals(res.status_code, 200)
        json_res = json.loads(res.content)
        for key in dct:
            self.assertEquals(dct[key], json_res[key])

    def test_delete(self):
        self.loginAs("admin")
        assert Campaign.objects.count() == 1

        doc = Document.objects.create(
                author=User.objects.get(username='author'),
                editor=User.objects.get(username='moderator'),
                in_reply_to=self.camp.reply_code)

        dct = {"id": self.camp.pk}
        self._query("delete", data=dct, error="The following documents are replies to this campaign. Their in-reply-to field must be cleared or changed before this campaign can be deleted:\n{0}".format(doc.get_edit_url()))

        self.assertEquals(Campaign.objects.count(), 1)

        doc.in_reply_to = None
        doc.save()

        self._query("delete", data=dct, success={"status": "success"})

