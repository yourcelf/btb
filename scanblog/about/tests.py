"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse

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
