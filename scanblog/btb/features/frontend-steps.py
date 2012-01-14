import re
from lettuce import *
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from scanning.models import Document

@step(r'I see (a page of|some|\d+) post snippets?')
def see_x_post_snippets(step, amount):
    count = Document.objects.public().filter(type="post").count()
    number = min(count, 10)
    elements = world.browser.find_elements_by_xpath("//div[contains(@class, 'post-snippet')]")
    if amount == "a page of":
        assert len(elements) == number, \
               "Expected %s, got %s" % (number, len(elements))
    elif amount == "some":
        assert len(elements) > 0, \
               "Expected more than 0, got %s" % (len(elements))
    else:
        assert len(elements) == int(amount), \
               "Expected %s, got %s" % (count, len(elements))

@step(u'I see a full post')
def i_see_a_full_post(step):
    pagegroup = world.browser.find_element_by_class_name("scan-page-group")

@step(u'I see a reply form')
def i_see_a_reply_form(step):
    form = world.browser.find_elements_by_class_name("commentform")

@step(u'I see a list of people')
def i_see_a_list_of_people(step):
    assert len(world.browser.find_elements_by_css_selector("li.person")) > 1

@step(u'I follow a person link')
def i_follow_a_person_link(step):
    link = world.browser.find_element_by_class_name("bloglink")
    link.click()

@step(u'I see a header')
def i_see_a_header(step):
    world.browser.find_elements_by_tag_name("h1")

@step(u'I see the subnav links')
def i_see_the_subnav_links(step):
    for dct in step.hashes:
        world.browser.find_element_by_link_text(dct['link text'])

@step(u'the following links work')
def the_following_links_work(step):
    for dct in step.hashes:
        world.browser.get(django_url(dct['url'].strip()))
        try:
            title = world.browser.find_element_by_tag_name("title")
        except NoSuchElementException:
            assert 0, "URL '%s' is broken" % dct['url']
        assert not re.search("404", title.text), "%s: (%s)" % (dct['url'], title.text)
