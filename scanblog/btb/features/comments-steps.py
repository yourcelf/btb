import re
import time
from lettuce import *
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from scanning.models import Document

@step('Post (\d+) has no comments')
def post_has_no_comments(step, id_):
    doc = Document.objects.get(id=id_)
    doc.comments = []
    assert doc.comments.all().count() == 0

@step('I go to post (\d+)')
def i_go_to_post(step, id_):
    world.browser.get(django_url('/posts/%s' % id_))

@step('I put "([^"]*)" in the comment form')
def i_put_text_in_the_comment_form(step, text):
    el = world.browser.find_element_by_name('comment')
    el.send_keys(text)

@step('I (don\'t )?see the comment "([^"]*)"')
def i_see_the_comment(step, dont, value):
    els = world.browser.find_elements_by_class_name('commentbody')
    found = False
    for el in els:
        if el.text.strip() == value:
            found = True
            break
    if dont and found:
        assert 0, "Comment '%s' not expected, but found." % value
    if not dont and not found:
        assert 0, "Comment with value '%s' not found." % value
    if found:
        return el
    return None

@step('I edit the comment "([^"]*)"')
def i_edit_the_comment(step, value):
    comments = world.browser.find_elements_by_class_name('comment')
    for i,comment in enumerate(comments):
        body = comment.find_element_by_class_name('commentbody')
        if body.text.strip() == value:
            el = comment.find_element_by_class_name('comment-edit')
            # Argh... 'click' not working, so go manually.
            href = el.get_attribute("href")
            world.browser.get(href)
            return
    assert 0, "Comment '%s' not found." % value

@step('I delete the comment "([^"]*)"')
def i_delete_the_comment(step, value):
    comments = world.browser.find_elements_by_class_name('comment')
    for i,comment in enumerate(comments):
        body = comment.find_element_by_class_name('commentbody')
        if body.text.strip() == value:
            delete = comment.find_element_by_class_name('comment-delete')
            # Argh... 'click' not working, so go manually.
            href = delete.get_attribute("href")
            world.browser.get(href)
            return
    assert 0, "Comment '%s' not found." % value

@step('I see the delete confirmation')
def i_see_the_delete_confirmation(step):
    world.browser.find_element_by_class_name("delete-form")

@step('I see the edit form')
def i_see_the_edit_form(step):
    el = world.browser.find_element_by_id('id_comment')
    header = world.browser.find_element_by_tag_name('h2')
    assert header.text.strip() == "Edit comment"
    return el

@step('I put "([^"]*)" in the edit form')
def i_put_text_in_the_edit_form(step, text):
    el = i_see_the_edit_form(step)
    el.clear()
    el.send_keys(text)
