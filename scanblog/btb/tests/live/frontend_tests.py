from .base import BtbLiveServerTestCase

class TestFrontend(BtbLiveServerTestCase):
    """
    Test that basic page access and navigation proceeds without errors.
    """
    def test_blogs(self):
        b = self.selenium
        b.get(self.url("/"))
        b.find_element_by_link_text("Blogs").click()
        self.assertTrue(
            "Recent posts by date" in self.css("h1").text
        )
        self.assertTrue(len(self.csss('.post-snippet')) > 0)

        b.find_element_by_link_text("Reply").click()
        self.css(".post-detail")
        self.css(".commentform")

    def test_people(self):
        b = self.selenium
        b.get(self.url("/"))
        b.find_element_by_link_text("People").click()
        self.assertTrue(len(self.csss("li.person")) > 0)
        self.assertTrue(len(self.csss("li.org")) > 0)

    def test_author_posts(self):
        b = self.selenium
        b.get(self.url("/people/"))
        self.css(".bloglink").click()
        self.css("h1")
        self.assertTrue(len(self.csss(".post-snippet")) > 0)

    def test_about_pages(self):
        b = self.selenium
        for link in ("Community Guidelines", "Frequently Asked Questions", "News", "Mailing list"):
            b.get(self.url("/"))
            b.find_element_by_link_text("About").click()
            b.find_element_by_link_text(link).click()

    def test_static_urls(self):
        for link in (
                "/",
                "/blogs/",
                "/people/",
                "/about/",
                "/about/guidelines/",
                "/about/faq/",
                "/people/join",
                "/accounts/login/",
                "/accounts/register/",
                ):
            self.selenium.get(self.url(link))
            # Selenium webdriver does not expose status codes; do this instead.
            self.assertFalse("404" in self.css("title").text)


