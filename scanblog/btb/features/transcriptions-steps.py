import re
from lettuce import *
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from comments.models import Comment

@step(u'I am not signed in')
def i_am_not_signed_in(step):
    world.browser.get(django_url("/accounts/logout/?next=/"))

@step(u'I click a transcription link')
def i_click_a_transcription_link(step):
    world.browser.get(django_url("/scanning/transcribe/5"))

@step(u'I put "([^"]*)" in the transcription form')
def i_put_text_in_the_transcription_form(step, value):
    textarea = world.browser.find_element_by_id("id_body")
    textarea.clear()
    textarea.send_keys(value)

@step(u'The transcription text reads "([^"]*)"')
def the_transcription_text_reads(step, value):
    tx = world.browser.find_element_by_class_name("transcription")
    assert tx.text.strip() == value

@step(u'I have previously left (no )?comments on that post')
def i_have_no_comments_on_that_post(step, no):
    url = world.browser.current_url
    pk = url.split("/")[-1]
    comments = Comment.objects.filter(document__pk=pk,
                                      user__username='testuser')
    if no:
        assert not comments.exists()
    else:
        assert comments.exists()

@step(u"I am redirected to the after transcribe comment page")
def redirect_to_after_transcribe_page(step):
    textarea = world.browser.find_element_by_id("id_comment")
    assert "Thanks for writing" in textarea.text

@step(u'I am redirected to the post page')
def redirected_to_post_page(step):
    pagegroup = world.browser.find_element_by_class_name("scan-page-group")

@step(u'the transcription button reads "([^"]*)"')
def the_transcription_button_reads(step, value):
    button = world.browser.find_element_by_class_name("transcribe-top-button")
    assert button.text == value, "Expected %s, got %s" % (value, button.text)

@step(u'I visit a post with unlocked transcription revisions')
def i_visit_a_post_with_unlocked_transcription_revisions(step):
    world.browser.get(django_url("/posts/5"))

@step(u'I see a revision table')
def i_see_a_revision_table(step):
    world.browser.find_element_by_id("diffs")
    try:
        world.browser.find_element_by_class_name("error")
        assert 0, "Server error encountered in diff page"
    except NoSuchElementException:
        pass
