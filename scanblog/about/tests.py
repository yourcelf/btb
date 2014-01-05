import datetime
from django.test import TestCase
from django.core.urlresolvers import reverse

from about.models import SiteBanner

class TestAccess(TestCase):
    fixtures = ["initial_data.json"]
    def test_access(self):
        for page in ("about", "about.copyright", "about.faq",
                "about.resources", "about.community_guidelines", "about.terms",
                "about.privacy", "about.dmca"):
            try:
                r = self.client.get(reverse(page))
                self.assertEquals(r.status_code, 200)
            except Exception:
                print page
                raise

class TestSiteBanner(TestCase):
    def test_no_banner(self):
        r = self.client.get("/")
        self.assertEquals(SiteBanner.objects.current().count(), 0)
        self.assertEquals(r.status_code, 200)
        self.assertFalse("<div class='site-banner'>" in r.content)

    def test_banner(self):
        banner = SiteBanner.objects.create(html="<b>TEST</b> banner")
        self.assertTrue(banner.is_current())
        self.assertEquals(list(SiteBanner.objects.current()), [banner])

        r = self.client.get("/")
        self.assertEquals(r.status_code, 200)
        self.assertTrue("<div class='site-banner'" in r.content)
        self.assertTrue("<b>TEST</b> banner" in r.content)

    def test_banner_currency(self):
        current_no_end_date = SiteBanner.objects.create(html="current no end")
        current_future_end_date = SiteBanner.objects.create(html="current future end",
                end_date=datetime.datetime.now() + datetime.timedelta(seconds=10))
        not_started_yet_no_end = SiteBanner.objects.create(html="not started yet",
                start_date=datetime.datetime.now() + datetime.timedelta(seconds=10))
        not_started_yet_future_end = SiteBanner.objects.create(html="not started yet",
                start_date=datetime.datetime.now() + datetime.timedelta(seconds=10),
                end_date=datetime.datetime.now() + datetime.timedelta(seconds=20))
        expired = SiteBanner.objects.create(html="expired",
                start_date=datetime.datetime.now() - datetime.timedelta(seconds=20),
                end_date=datetime.datetime.now() - datetime.timedelta(seconds=10))

        # ordered by creation date.
        self.assertEquals(list(SiteBanner.objects.current()), [
            current_future_end_date, current_no_end_date, 
        ])
