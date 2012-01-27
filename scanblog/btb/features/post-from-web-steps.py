import re
import time
from lettuce import step, world
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from btblettuce import css, csss

@step(u'I visit the post editor')
def and_i_visit_the_post_editor(step):
    world.browser.get(django_url("/posts/edit"))
    css(".edit-post")

@step(u'I create a post with status "([^"]*)"')
def given_i_create_a_post_with_status(step, status):
    css("#id_title").send_keys("My Title %s" % status)
    css("#id_body").send_keys("This is the body of my %s post" % status)
    css(".tagit-input").send_keys("tag1, tag2, tag3")
    css("#id_status").send_keys(status)
    css("input[type=submit]").click()

@step(u'the post appears on my blog')
def then_the_post_appears_on_my_blog(step):
    world.browser.get(django_url("/blogs/"))
    csss("a.read-more")[0].click()
    assert css("h2").text.strip() == "My Title Publish"

@step(u'the post does not appear on my blog')
def then_the_post_does_not_appear_on_my_blog(step):
    world.browser.get(django_url("/blogs/"))
    for el in csss("h2"):
        if el.text.strip() == "My Title Draft":
            assert False, 'Draft was published.'

@step(u'I see the post in the post manager')
def but_i_see_the_post_in_the_post_manager(step):
    world.browser.get(django_url("/posts/manage"))
    for el in csss("a"):
        if el.text.strip() == "My Title Draft":
            break
    else:
        assert False, "Draft not found in post manager"

@step(u'I visit the post manager')
def and_i_visit_the_post_manager(step):
    world.browser.get(django_url("/posts/manage"))
    assert world.browser.current_url.endswith("/posts/manage")

@step(u'I see a list of posts')
def then_i_see_a_list_of_posts(step):
    assert len(csss(".my-posts tr")) > 1

@step(u'I click on the first one')
def given_i_click_on_the_first_one(step):
    css("a.edit-post").click()

@step(u'I see the post in the editing form')
def then_i_see_the_post_in_the_editing_form(step):
    title = css("#id_title").get_attribute("value").strip()
    assert title == "My Title Draft", "wrong title: '%s'" % title
    body = css("#id_body").text.strip()
    assert body == "This is the body of my Draft post", "wrong body: '%s'" % body
